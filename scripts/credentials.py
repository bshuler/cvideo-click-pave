#!/usr/bin/env python3
"""Credential management script for cvideo-click-pave infrastructure.

This script replaces extract-credentials.sh and get-credentials.sh with
a unified Python approach using boto3 for AWS interactions.

Features:
- Extract credentials from Terraform outputs when available
- Fall back to AWS API discovery of users and keys
- Generate secure credential template files
- Provide AWS Console instructions for manual key retrieval
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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


def get_boto3_client(service_name: str):  # type: ignore[return]
    """Get boto3 client with proper error handling.

    Args:
        service_name: AWS service name (e.g., 'iam', 's3')

    Returns:
        boto3 client for the specified service

    Raises:
        SystemExit: If credentials are not configured or connection fails
    """
    try:
        return boto3.client(service_name)  # type: ignore[call-overload]
    except NoCredentialsError:
        print_status("❌", "AWS credentials not configured")
        print_status("💡", "Ensure AWS credentials are configured (make init)")
        sys.exit(1)
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service_name}: {e}")
        print_status("💡", "Ensure AWS credentials are configured (make init)")
        sys.exit(1)


def get_terraform_outputs() -> Dict[str, Optional[str]]:
    """Try to get credentials from Terraform outputs.

    Returns:
        Dictionary containing credential keys from terraform, or empty dict if
        unavailable
    """
    print_status("📋", "Checking for Terraform outputs...")

    try:
        # Check if terraform outputs are available
        result = subprocess.run(
            ["terraform", "output", "-json"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            outputs = json.loads(result.stdout)
            if outputs:
                print_status("✅", "Found Terraform outputs")
                return {
                    "admin_access_key": outputs.get("admin_user_access_key", {}).get(
                        "value"
                    ),
                    "admin_secret_key": outputs.get("admin_user_secret_key", {}).get(
                        "value"
                    ),
                    "developer_access_key": outputs.get(
                        "developer_user_access_key", {}
                    ).get("value"),
                    "developer_secret_key": outputs.get(
                        "developer_user_secret_key", {}
                    ).get("value"),
                }
    except (subprocess.SubprocessError, json.JSONDecodeError) as e:
        logger.debug(f"Failed to get terraform outputs: {e}")

    print_status("⚠️", "No Terraform outputs found, using AWS API discovery...")
    return {}


def find_pave_users(iam_client) -> Dict[str, str]:
    """Find pave users using boto3.

    Args:
        iam_client: boto3 IAM client

    Returns:
        Dictionary containing admin_user and developer_user names

    Raises:
        SystemExit: If users are not found
    """
    print_status("🔍", "Looking for deployed users...")

    try:
        response = iam_client.list_users()
        users = response["Users"]

        admin_user = None
        developer_user = None

        for user in users:
            username = user["UserName"]
            # Match exact names (no random suffixes) or legacy patterns
            if username == "admin-user" or "admin-user-" in username:
                admin_user = username
            elif username == "developer-user" or "developer-user-" in username:
                developer_user = username

        if not admin_user or not developer_user:
            print_status("❌", "Could not find admin or developer users")
            print_status("💡", "Make sure infrastructure has been deployed:")
            print_status("", "  make apply")
            print_status("", "  # OR #")
            print_status("", "  act -W .github/workflows/terraform.yaml")
            sys.exit(1)

        print_status("✅", "Found users:")
        print(f"  - Admin: {admin_user}")
        print(f"  - Developer: {developer_user}")

        return {"admin_user": admin_user, "developer_user": developer_user}

    except ClientError as e:
        print_status("❌", f"Error finding users: {e}")
        sys.exit(1)


def get_user_access_keys(iam_client, username: str) -> List[str]:
    """Get access keys for a user.

    Args:
        iam_client: boto3 IAM client
        username: IAM username

    Returns:
        List of access key IDs for the user
    """
    try:
        response = iam_client.list_access_keys(UserName=username)
        return [key["AccessKeyId"] for key in response["AccessKeyMetadata"]]
    except ClientError as e:
        logger.warning(f"Could not get access keys for {username}: {e}")
        return []


def create_credential_templates(
    users: Dict[str, str],
    terraform_creds: Dict[str, Optional[str]],
    access_keys: Dict[str, str],
) -> None:
    """Create credential template files.

    Args:
        users: Dictionary containing user names
        terraform_creds: Dictionary containing terraform credential outputs
        access_keys: Dictionary containing existing access key IDs
    """
    # Create credentials directory
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)

    print_status("📝", "Creating credential template files...")

    # Determine if we have actual credentials from terraform or need templates
    has_terraform_creds = bool(terraform_creds.get("admin_access_key"))

    if has_terraform_creds:
        create_actual_credential_files(terraform_creds, credentials_dir)
    else:
        create_template_credential_files(users, access_keys, credentials_dir)


def create_actual_credential_files(
    creds: Dict[str, Optional[str]], credentials_dir: Path
) -> None:
    """Create credential files with actual keys from Terraform.

    Args:
        creds: Dictionary containing actual credential values
        credentials_dir: Path to credentials directory
    """
    admin_file = credentials_dir / "admin.env"
    developer_file = credentials_dir / "developer.env"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Admin credentials
    admin_content = f"""# Admin user credentials - Full AWS access
# Created: {timestamp}
# Use these for administrative tasks only
AWS_ACCESS_KEY_ID={creds['admin_access_key']}
AWS_SECRET_ACCESS_KEY={creds['admin_secret_key']}
AWS_DEFAULT_REGION=us-east-1
"""

    # Developer credentials
    developer_content = f"""# Developer user credentials - Limited AWS access for
# application development
# Created: {timestamp}
# Use these in your next code repository for application development
AWS_ACCESS_KEY_ID={creds['developer_access_key']}
AWS_SECRET_ACCESS_KEY={creds['developer_secret_key']}
AWS_DEFAULT_REGION=us-east-1

# Permissions include:
# - Amazon S3 Full Access (for file storage, static websites)
# - AWS Lambda Full Access (for serverless functions)
# - Amazon EC2 Read Only Access (for viewing instances)
"""

    # Write files with secure permissions
    admin_file.write_text(admin_content, encoding="utf-8")
    developer_file.write_text(developer_content, encoding="utf-8")

    # Set secure permissions (600 - owner read/write only)
    admin_file.chmod(0o600)
    developer_file.chmod(0o600)

    print_status("✅", "Credentials extracted and saved with secure permissions (600)")
    print_status("📋", f"Admin Access Key: {creds['admin_access_key']}")
    print_status("📋", f"Developer Access Key: {creds['developer_access_key']}")


def create_template_credential_files(
    users: Dict[str, str], access_keys: Dict[str, str], credentials_dir: Path
) -> None:
    """Create template credential files with AWS Console instructions.

    Args:
        users: Dictionary containing user names
        access_keys: Dictionary containing existing access key IDs
        credentials_dir: Path to credentials directory
    """
    admin_file = credentials_dir / "admin.env"
    developer_file = credentials_dir / "developer.env"

    admin_user = users["admin_user"]
    developer_user = users["developer_user"]
    admin_key = access_keys.get("admin", "None")
    developer_key = access_keys.get("developer", "None")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print_status("🔑", "Existing Access Keys:")
    print(f"  - Admin: {admin_key}")
    print(f"  - Developer: {developer_key}")
    print()

    if admin_key != "None" and developer_key != "None":
        print_status(
            "⚠️",
            "Access keys exist but secret keys cannot be retrieved after creation.",
        )

    print_status(
        "📝", "Creating credential template files with AWS Console instructions..."
    )

    # Admin template
    admin_access_key_instruction = (
        f"Use existing access key: {admin_key}"
        if admin_key != "None"
        else "Create a new access key"
    )
    admin_access_key_value = (
        admin_key if admin_key != "None" else "REPLACE_WITH_ACTUAL_ACCESS_KEY"
    )

    admin_content = f"""# Admin user credentials - Full AWS access
# User: {admin_user}
# Created: {timestamp}
#
# ⚠️  MANUAL ENTRY REQUIRED:
# Go to AWS Console > IAM > Users > {admin_user} > Security credentials
# > Access keys
# {admin_access_key_instruction} and enter the values below:
#
AWS_ACCESS_KEY_ID={admin_access_key_value}
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_ACTUAL_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
"""

    # Developer template
    developer_access_key_instruction = (
        f"Use existing access key: {developer_key}"
        if developer_key != "None"
        else "Create a new access key"
    )
    developer_access_key_value = (
        developer_key if developer_key != "None" else "REPLACE_WITH_ACTUAL_ACCESS_KEY"
    )

    developer_content = f"""# Developer user credentials - Limited AWS access for
# application development
# User: {developer_user}
# Created: {timestamp}
#
# ⚠️  MANUAL ENTRY REQUIRED:
# Go to AWS Console > IAM > Users > {developer_user} > Security credentials
# > Access keys
# {developer_access_key_instruction} and enter the values below:
#
# Permissions include:
# - Amazon S3 Full Access (for file storage, static websites)
# - AWS Lambda Full Access (for serverless functions)
# - Amazon EC2 Read Only Access (for viewing instances)
#
AWS_ACCESS_KEY_ID={developer_access_key_value}
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_ACTUAL_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
"""

    # Write template files
    admin_file.write_text(admin_content, encoding="utf-8")
    developer_file.write_text(developer_content, encoding="utf-8")

    # Set secure permissions
    admin_file.chmod(0o600)
    developer_file.chmod(0o600)

    print_status("✅", "Template files created with secure permissions (600)")

    # Print manual instructions
    print()
    print_status("🚀", "Next Steps:")
    print("1. Go to AWS Console > IAM > Users")
    print("2. For each user, go to Security credentials > Access keys")
    print("3. Create new access key if none exists or get secret for existing key")
    print("4. Replace the placeholder values in the credential files")


def main() -> None:
    """Main credential extraction workflow."""
    print_status("🔐", "Setting up credential extraction...")

    # Get boto3 client
    iam_client = get_boto3_client("iam")

    # Try to get credentials from Terraform outputs first
    terraform_creds = get_terraform_outputs()

    # Find users via AWS API
    users = find_pave_users(iam_client)

    # Get existing access keys
    admin_keys = get_user_access_keys(iam_client, users["admin_user"])
    developer_keys = get_user_access_keys(iam_client, users["developer_user"])

    access_keys = {
        "admin": admin_keys[0] if admin_keys else "None",
        "developer": developer_keys[0] if developer_keys else "None",
    }

    # Create credential files
    create_credential_templates(users, terraform_creds, access_keys)

    print()
    print_status("📁", "Credentials saved to:")
    print("  - credentials/admin.env     (Administrator access)")
    print("  - credentials/developer.env (Development access)")
    print()
    print_status("🔒", "Security Notes:")
    print("  - These files are in .gitignore to prevent accidental commits")
    print("  - Use admin.env for full infrastructure management")
    print("  - Use developer.env for limited infrastructure access")
    print("  - Never commit these credentials to version control")
    print("  - Consider rotating keys periodically")

    if not terraform_creds.get("admin_access_key"):
        print()
        print_status("💡", "Manual Setup Required:")
        print("- Replace placeholder values in credential files")
        print("- Use AWS Console > IAM > Users > Security credentials")
        print("- Admin credentials: full infrastructure management access")
        print(
            "- Developer credentials: limited infrastructure access "
            "(S3, Lambda, EC2 read-only)"
        )


if __name__ == "__main__":
    main()
