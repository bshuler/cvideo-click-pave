#!/usr/bin/env python3
"""
Credential management script for cvideo-click-pave infrastructure.

This script replaces extract-credentials.sh and get-credentials.sh with
a unified Python approach using boto3 for AWS interactions.

Features:
- Extract credentials from Terraform outputs when available
- Fall back to AWS API discovery of users and keys
- Generate secure credential template files
- Provide AWS Console instructions for manual key retrieval
"""

import boto3
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def get_boto3_client(service: str):
    """Get boto3 client with proper error handling."""
    try:
        return boto3.client(service)
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service}: {e}")
        print_status("💡", "Ensure AWS credentials are configured (make init)")
        sys.exit(1)


def get_terraform_outputs() -> dict:
    """Try to get credentials from Terraform outputs."""
    print_status("📋", "Checking for Terraform outputs...")
    
    try:
        # Check if terraform outputs are available
        result = subprocess.run(
            ["terraform", "output", "-json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            outputs = json.loads(result.stdout)
            if outputs:
                print_status("✅", "Found Terraform outputs")
                return {
                    'admin_access_key': outputs.get('admin_user_access_key', {}).get('value'),
                    'admin_secret_key': outputs.get('admin_user_secret_key', {}).get('value'),
                    'developer_access_key': outputs.get('developer_user_access_key', {}).get('value'),
                    'developer_secret_key': outputs.get('developer_user_secret_key', {}).get('value')
                }
    except (subprocess.SubprocessError, json.JSONDecodeError):
        pass
    
    print_status("⚠️", "No Terraform outputs found, using AWS API discovery...")
    return {}


def find_pave_users(iam_client) -> dict:
    """Find pave users using boto3."""
    print_status("🔍", "Looking for deployed users...")
    
    try:
        response = iam_client.list_users()
        users = response['Users']
        
        admin_user = None
        developer_user = None
        
        for user in users:
            username = user['UserName']
            # Match exact names (no random suffixes) or legacy patterns
            if username == 'admin-user' or 'admin-user-' in username:
                admin_user = username
            elif username == 'developer-user' or 'developer-user-' in username:
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
        
        return {
            'admin_user': admin_user,
            'developer_user': developer_user
        }
        
    except Exception as e:
        print_status("❌", f"Error finding users: {e}")
        sys.exit(1)


def get_user_access_keys(iam_client, username: str) -> list:
    """Get access keys for a user."""
    try:
        response = iam_client.list_access_keys(UserName=username)
        return [key['AccessKeyId'] for key in response['AccessKeyMetadata']]
    except Exception:
        return []


def create_credential_templates(users: dict, terraform_creds: dict, access_keys: dict):
    """Create credential template files."""
    # Create credentials directory
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)
    
    print_status("📝", "Creating credential template files...")
    
    # Determine if we have actual credentials from terraform or need templates
    has_terraform_creds = bool(terraform_creds.get('admin_access_key'))
    
    if has_terraform_creds:
        create_actual_credential_files(terraform_creds, credentials_dir)
    else:
        create_template_credential_files(users, access_keys, credentials_dir)


def create_actual_credential_files(creds: dict, credentials_dir: Path):
    """Create credential files with actual keys from Terraform."""
    admin_file = credentials_dir / "admin.env"
    developer_file = credentials_dir / "developer.env"
    
    # Admin credentials
    admin_content = f"""# Admin user credentials - Full AWS access
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Use these for administrative tasks only
AWS_ACCESS_KEY_ID={creds['admin_access_key']}
AWS_SECRET_ACCESS_KEY={creds['admin_secret_key']}
AWS_DEFAULT_REGION=us-east-1
"""
    
    # Developer credentials  
    developer_content = f"""# Developer user credentials - Limited AWS access for application development
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
    admin_file.write_text(admin_content)
    developer_file.write_text(developer_content)
    
    # Set secure permissions (600 - owner read/write only)
    admin_file.chmod(0o600)
    developer_file.chmod(0o600)
    
    print_status("✅", "Credentials extracted and saved with secure permissions (600)")
    print_status("📋", f"Admin Access Key: {creds['admin_access_key']}")
    print_status("📋", f"Developer Access Key: {creds['developer_access_key']}")


def create_template_credential_files(users: dict, access_keys: dict, credentials_dir: Path):
    """Create template credential files with AWS Console instructions."""
    admin_file = credentials_dir / "admin.env"
    developer_file = credentials_dir / "developer.env"
    
    admin_user = users['admin_user']
    developer_user = users['developer_user']
    admin_key = access_keys.get('admin', 'None')
    developer_key = access_keys.get('developer', 'None')
    
    print_status("🔑", "Existing Access Keys:")
    print(f"  - Admin: {admin_key}")
    print(f"  - Developer: {developer_key}")
    print()
    
    if admin_key != 'None' and developer_key != 'None':
        print_status("⚠️", "Access keys exist but secret keys cannot be retrieved after creation.")
    
    print_status("📝", "Creating credential template files with AWS Console instructions...")
    
    # Admin template
    admin_content = f"""# Admin user credentials - Full AWS access
# User: {admin_user}
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# ⚠️  MANUAL ENTRY REQUIRED:
# Go to AWS Console > IAM > Users > {admin_user} > Security credentials > Access keys
# {'Use existing access key: ' + admin_key if admin_key != 'None' else 'Create a new access key'} and enter the values below:
#
AWS_ACCESS_KEY_ID={'REPLACE_WITH_ACTUAL_ACCESS_KEY' if admin_key == 'None' else admin_key}
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_ACTUAL_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
"""

    # Developer template
    developer_content = f"""# Developer user credentials - Limited AWS access for application development
# User: {developer_user}
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# ⚠️  MANUAL ENTRY REQUIRED:
# Go to AWS Console > IAM > Users > {developer_user} > Security credentials > Access keys
# {'Use existing access key: ' + developer_key if developer_key != 'None' else 'Create a new access key'} and enter the values below:
#
# Permissions include:
# - Amazon S3 Full Access (for file storage, static websites)
# - AWS Lambda Full Access (for serverless functions)
# - Amazon EC2 Read Only Access (for viewing instances)
#
AWS_ACCESS_KEY_ID={'REPLACE_WITH_ACTUAL_ACCESS_KEY' if developer_key == 'None' else developer_key}
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_ACTUAL_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
"""
    
    # Write template files
    admin_file.write_text(admin_content)
    developer_file.write_text(developer_content)
    
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


def main():
    """Main credential extraction workflow."""
    print_status("🔐", "Setting up credential extraction...")
    
    # Get boto3 client
    iam_client = get_boto3_client('iam')
    
    # Try to get credentials from Terraform outputs first
    terraform_creds = get_terraform_outputs()
    
    # Find users via AWS API
    users = find_pave_users(iam_client)
    
    # Get existing access keys
    admin_keys = get_user_access_keys(iam_client, users['admin_user'])
    developer_keys = get_user_access_keys(iam_client, users['developer_user'])
    
    access_keys = {
        'admin': admin_keys[0] if admin_keys else 'None',
        'developer': developer_keys[0] if developer_keys else 'None'
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
    print("  - Copy credentials/developer.env to your next code repository")
    print("  - Never commit these credentials to version control")
    print("  - Consider rotating keys periodically")
    
    if not terraform_creds.get('admin_access_key'):
        print()
        print_status("🔒", "Security Reminders:")
        print("- These files are already in .gitignore")
        print("- Never commit credential files to version control")
        print("- Use admin credentials only for infrastructure management")
        print("- Use developer credentials for your application code")
        print("- Consider rotating keys periodically")


if __name__ == "__main__":
    main()