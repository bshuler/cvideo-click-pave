#!/usr/bin/env python3
"""AWS Access Key Rotation Script for Security Incident Response

This script safely rotates compromised AWS access keys for the developer user
while maintaining infrastructure access and following AWS security best practices.

Features:
- Creates new access keys for the developer user
- Updates local credential files
- Deactivates (but doesn't delete) the compromised key initially for safety
- Provides instructions for final cleanup after validation
- Handles AWS quarantine policies during security incidents
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def print_status(emoji: str, message: str) -> None:
    """Print formatted status message with emoji and logging."""
    formatted_message = f"{emoji} {message}"
    print(formatted_message)
    logger.info(message)


def get_boto3_client(service_name: str) -> Any:
    """Get boto3 client with proper error handling."""
    try:
        return boto3.client(service_name)  # type: ignore[misc]
    except NoCredentialsError:
        print_status(
            "❌", "No AWS credentials found. Ensure bootstrap credentials are loaded."
        )
        sys.exit(1)
    except Exception as e:
        print_status("❌", f"Failed to create {service_name} client: {e}")
        sys.exit(1)


def get_current_user() -> str:
    """Get current AWS user identity."""
    try:
        sts_client = get_boto3_client("sts")
        identity = sts_client.get_caller_identity()
        arn = identity.get("Arn", "")
        if ":user/" in arn:
            return arn.split(":user/")[1]
        else:
            print_status("❌", f"Not running as IAM user. Current identity: {arn}")
            sys.exit(1)
    except ClientError as e:
        print_status("❌", f"Failed to get caller identity: {e}")
        sys.exit(1)


def create_new_access_key(username: str) -> Dict[str, str]:
    """Create new access key for the specified user."""
    try:
        iam_client = get_boto3_client("iam")
        print_status("🔑", f"Creating new access key for user: {username}")

        response = iam_client.create_access_key(UserName=username)
        access_key = response["AccessKey"]

        return {
            "access_key_id": access_key["AccessKeyId"],
            "secret_access_key": access_key["SecretAccessKey"],
            "created": access_key["CreateDate"].isoformat(),
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "LimitExceeded":
            print_status(
                "❌",
                f"User {username} already has the maximum number of access keys (2)",
            )
            print_status("💡", "You may need to delete an existing key first")
        else:
            print_status("❌", f"Failed to create access key: {e}")
        sys.exit(1)


def deactivate_access_key(username: str, access_key_id: str) -> None:
    """Deactivate (but don't delete) the compromised access key."""
    try:
        iam_client = get_boto3_client("iam")
        print_status("🔒", f"Deactivating compromised access key: {access_key_id}")

        iam_client.update_access_key(
            UserName=username, AccessKeyId=access_key_id, Status="Inactive"
        )
        print_status("✅", f"Access key {access_key_id} has been deactivated")
    except ClientError as e:
        print_status("❌", f"Failed to deactivate access key: {e}")
        sys.exit(1)


def list_access_keys(username: str) -> list:
    """List all access keys for the user."""
    try:
        iam_client = get_boto3_client("iam")
        response = iam_client.list_access_keys(UserName=username)
        return response["AccessKeyMetadata"]
    except ClientError as e:
        print_status("❌", f"Failed to list access keys: {e}")
        sys.exit(1)


def update_credential_file(file_path: Path, new_credentials: Dict[str, str]) -> None:
    """Update credential file with new access key."""
    try:
        if not file_path.exists():
            print_status("⚠️", f"Credential file not found: {file_path}")
            return

        # Read current file
        content = file_path.read_text()
        lines = content.split("\n")

        # Update the credentials
        updated_lines = []
        for line in lines:
            if line.startswith("AWS_ACCESS_KEY_ID="):
                updated_lines.append(
                    f'AWS_ACCESS_KEY_ID={new_credentials["access_key_id"]}'
                )
            elif line.startswith("AWS_SECRET_ACCESS_KEY="):
                updated_lines.append(
                    f'AWS_SECRET_ACCESS_KEY={new_credentials["secret_access_key"]}'
                )
            elif line.startswith("# Created:"):
                updated_lines.append(
                    f'# Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (ROTATED - Security Incident Response)'
                )
            else:
                updated_lines.append(line)

        # Write updated content
        file_path.write_text("\n".join(updated_lines))
        print_status("✅", f"Updated credential file: {file_path}")

    except Exception as e:
        print_status("❌", f"Failed to update credential file {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Rotate AWS access keys for security incident response"
    )
    parser.add_argument(
        "--user", default="developer-user", help="IAM username to rotate keys for"
    )
    parser.add_argument(
        "--compromised-key",
        required=True,
        help="The compromised access key ID to deactivate",
    )
    parser.add_argument(
        "--skip-confirm", action="store_true", help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    print_status("🚨", "AWS ACCESS KEY ROTATION - Security Incident Response")
    print_status("🔍", f"Target user: {args.user}")
    print_status("🚨", f"Compromised key: {args.compromised_key}")

    # Confirm we're using bootstrap credentials
    current_user = get_current_user()
    if "bootstrap" not in current_user.lower():
        print_status(
            "⚠️", f"Warning: Not running as bootstrap user. Current user: {current_user}"
        )
        if not args.skip_confirm:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != "y":
                sys.exit(1)

    if not args.skip_confirm:
        print_status(
            "⚠️",
            f"This will create a new access key for {args.user} and deactivate {args.compromised_key}",
        )
        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            sys.exit(1)

    # Check current access keys
    print_status("🔍", f"Checking current access keys for {args.user}...")
    current_keys = list_access_keys(args.user)

    print_status("📋", f"Current access keys for {args.user}:")
    for key in current_keys:
        status_emoji = "🟢" if key["Status"] == "Active" else "🔴"
        print_status(
            "",
            f"  {status_emoji} {key['AccessKeyId']} ({key['Status']}) - Created: {key['CreateDate']}",
        )

    # Create new access key
    try:
        new_credentials = create_new_access_key(args.user)
        print_status(
            "✅", f"New access key created: {new_credentials['access_key_id']}"
        )
    except Exception as e:
        print_status("❌", f"Failed to create new access key: {e}")
        sys.exit(1)

    # Update credential files
    credentials_dir = Path("credentials")
    if credentials_dir.exists():
        developer_env = credentials_dir / "developer.env"
        update_credential_file(developer_env, new_credentials)

    # Deactivate compromised key
    deactivate_access_key(args.user, args.compromised_key)

    print_status("🎉", "Key rotation completed successfully!")
    print_status("📋", "Next steps:")
    print_status("", "1. Test new credentials with: make validate")
    print_status("", "2. Verify infrastructure access works correctly")
    print_status("", "3. Check CloudTrail for unauthorized activity")
    print_status("", "4. Remove quarantine policy from developer user")
    print_status(
        "", f"5. After verification, delete the compromised key: {args.compromised_key}"
    )
    print_status("", "6. Create AWS support case to confirm security measures")


if __name__ == "__main__":
    main()
