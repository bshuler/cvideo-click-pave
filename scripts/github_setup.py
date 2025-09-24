#!/usr/bin/env python3
"""
GitHub repository secrets setup script.

Helps set up GitHub repository secrets for CI/CD pipeline.
"""

import subprocess
import sys
from typing import Dict, Optional

import boto3


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def get_admin_credentials() -> Optional[Dict[str, str]]:
    """Get admin user credentials from AWS."""
    try:
        iam_client = boto3.client("iam")  # type: ignore[call-overload]

        # Find admin user
        response = iam_client.list_users()
        admin_user = None

        for user in response["Users"]:
            if user["UserName"] == "admin-user":
                admin_user = user["UserName"]
                break

        if not admin_user:
            print_status("❌", "No admin user found")
            print_status("💡", "Deploy infrastructure first: make apply")
            return None

        # Get access keys
        keys_response = iam_client.list_access_keys(UserName=admin_user)
        if not keys_response["AccessKeyMetadata"]:
            print_status("❌", f"No access keys found for {admin_user}")
            print_status(
                "💡", "Create access key in AWS Console or use credentials script"
            )
            return None

        access_key = keys_response["AccessKeyMetadata"][0]["AccessKeyId"]

        return {"username": admin_user, "access_key": access_key}

    except Exception as e:
        print_status("❌", f"Error getting admin credentials: {e}")
        return None


def check_gh_cli():
    """Check if GitHub CLI is available."""
    try:
        subprocess.run(["gh", "--version"], capture_output=True, text=True, check=True)
        print_status("✅", "GitHub CLI available")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print_status("❌", "GitHub CLI not found")
        print_status("💡", "Install GitHub CLI: https://cli.github.com/")
        return False


def main():
    """Main GitHub setup workflow."""
    print_status("🔧", "Setting up GitHub repository secrets...")
    print()

    # Check prerequisites
    if not check_gh_cli():
        sys.exit(1)

    # Get admin credentials
    creds = get_admin_credentials()
    if not creds:
        sys.exit(1)

    print_status("✅", f"Found admin user: {creds['username']}")
    print_status("🔑", f"Access Key: {creds['access_key']}")
    print()

    print_status("⚠️", "Secret key cannot be retrieved programmatically.")
    print_status("📝", "You'll need to get the secret key manually:")
    print(f"1. Go to AWS Console > IAM > Users > {creds['username']}")
    print("2. Go to Security credentials > Access keys")
    print(f"3. Find access key {creds['access_key']}")
    print("4. If secret is not available, create a new access key")
    print()

    print_status("🚀", "GitHub CLI commands to run:")
    print()
    print("# Set the three required secrets:")
    print(f"gh secret set AWS_ACCESS_KEY_ID --body '{creds['access_key']}'")
    print("gh secret set AWS_SECRET_ACCESS_KEY --body 'YOUR_SECRET_KEY_HERE'")
    print("gh secret set AWS_REGION --body 'us-east-1'")
    print()
    print("# Verify secrets are set:")
    print("gh secret list")
    print()
    print("# Trigger workflow:")
    print("gh workflow run terraform.yaml")
    print()

    print_status(
        "💡",
        "After setting secrets, the GitHub Actions workflow will work automatically!",
    )


if __name__ == "__main__":
    main()
