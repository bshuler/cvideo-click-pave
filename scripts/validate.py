#!/usr/bin/env python3
"""
Validation script for cvideo-click-pave infrastructure.

Validates AWS credentials, required tools, and infrastructure status.
"""

import boto3
import subprocess
import sys


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def check_aws_credentials():
    """Check if AWS credentials are configured and working."""
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        user_arn = response.get('Arn', 'Unknown')
        print_status("✅", f"AWS credentials valid - Account: {account_id}")
        print(f"    Identity: {user_arn}")
        return True
    except Exception as e:
        print_status("❌", f"AWS credentials invalid: {e}")
        print_status("💡", "Configure AWS credentials:")
        print("    - Set environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("    - Or configure AWS CLI: aws configure")
        print("    - Or use .secrets file for local development")
        return False


def check_terraform():
    """Check if Terraform is installed and accessible."""
    try:
        result = subprocess.run(['terraform', 'version'], 
                              capture_output=True, text=True, check=True)
        version_line = result.stdout.split('\n')[0]
        print_status("✅", f"Terraform available: {version_line}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print_status("❌", "Terraform not found")
        print_status("💡", "Install Terraform: https://terraform.io/downloads")
        return False


def check_python_deps():
    """Check if required Python dependencies are available."""
    try:
        import boto3
        print_status("✅", f"boto3 available: {boto3.__version__}")
        return True
    except ImportError:
        print_status("❌", "boto3 not found")
        print_status("💡", "Install dependencies: make init")
        return False


def main():
    """Main validation workflow."""
    print_status("🔍", "Validating environment...")
    print()
    
    checks = [
        ("AWS Credentials", check_aws_credentials),
        ("Terraform", check_terraform),
        ("Python Dependencies", check_python_deps)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        print()
    
    if all(results):
        print_status("✅", "All validations passed!")
        sys.exit(0)
    else:
        print_status("❌", "Some validations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()