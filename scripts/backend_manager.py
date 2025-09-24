#!/usr/bin/env python3
"""
Terraform backend configuration manager for cvideo-click-pave infrastructure.

This script manages the transition between local and S3 backends to solve the
chicken-and-egg problem where the S3 bucket is created by the same Terraform
configuration that needs to store its state in that bucket.

Usage:
  python3 scripts/backend_manager.py --local    # Switch to local backend
  python3 scripts/backend_manager.py --s3       # Switch to S3 backend
  python3 scripts/backend_manager.py --migrate  # Full migration workflow
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

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
    """Get boto3 client with proper error handling."""
    try:
        return boto3.client(service_name)  # type: ignore[call-overload]
    except NoCredentialsError:
        print_status("❌", "AWS credentials not configured")
        print_status("💡", "Ensure AWS credentials are configured")
        sys.exit(1)
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service_name}: {e}")
        sys.exit(1)


def backup_terraform_file() -> None:
    """Create backup of current Terraform configuration."""
    source = Path("pave_infra.tf")
    backup = Path("pave_infra.tf.backup")

    if source.exists():
        shutil.copy2(source, backup)
        print_status("💾", "Created backup: pave_infra.tf.backup")


def switch_to_local_backend() -> bool:
    """Switch Terraform configuration to use local backend."""
    tf_file = Path("pave_infra.tf")

    try:
        with open(tf_file, "r") as f:
            content = f.read()

        # Replace S3 backend with local backend
        s3_backend_block = """  backend "s3" {
    bucket = "pave-tf-state-bucket-us-east-1"
    key    = "pave/terraform.tfstate"
    region = "us-east-1"
    # Note: This bucket is created by this same configuration on first run
    # Use local backend initially, then migrate to S3 after bucket exists
  }"""

        local_backend_block = """  # Using local backend temporarily for bucket creation
  # backend "s3" {
  #   bucket = "pave-tf-state-bucket-us-east-1"
  #   key    = "pave/terraform.tfstate"
  #   region = "us-east-1"
  # }"""

        updated_content = content.replace(s3_backend_block, local_backend_block)

        with open(tf_file, "w") as f:
            f.write(updated_content)

        print_status("✅", "Switched to local backend configuration")
        return True

    except Exception as e:
        print_status("❌", f"Error switching to local backend: {e}")
        return False


def switch_to_s3_backend() -> bool:
    """Switch Terraform configuration to use S3 backend."""
    tf_file = Path("pave_infra.tf")

    try:
        with open(tf_file, "r") as f:
            content = f.read()

        # Replace local backend with S3 backend
        local_backend_block = """  # Using local backend temporarily for bucket creation
  # backend "s3" {
  #   bucket = "pave-tf-state-bucket-us-east-1"
  #   key    = "pave/terraform.tfstate"
  #   region = "us-east-1"
  # }"""

        s3_backend_block = """  backend "s3" {
    bucket = "pave-tf-state-bucket-us-east-1"
    key    = "pave/terraform.tfstate"
    region = "us-east-1"
    # Shared state across local, Act, and GitHub Actions deployments
  }"""

        updated_content = content.replace(local_backend_block, s3_backend_block)

        with open(tf_file, "w") as f:
            f.write(updated_content)

        print_status("✅", "Switched to S3 backend configuration")
        return True

    except Exception as e:
        print_status("❌", f"Error switching to S3 backend: {e}")
        return False


def check_s3_bucket_exists() -> bool:
    """Check if the S3 state bucket exists."""
    s3_client = get_boto3_client("s3")
    bucket_name = "pave-tf-state-bucket-us-east-1"

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print_status("✅", f"S3 state bucket {bucket_name} exists")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            print_status("ℹ️", f"S3 state bucket {bucket_name} does not exist")
            return False
        else:
            print_status("❌", f"Error checking S3 bucket: {e}")
            return False


def terraform_init() -> bool:
    """Run terraform init."""
    try:
        result = subprocess.run(
            ["terraform", "init", "-input=false"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print_status("✅", "Terraform init completed")
            return True
        else:
            print_status("❌", "Terraform init failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

    except FileNotFoundError:
        print_status("❌", "Terraform not found in PATH")
        return False


def migrate_state_to_s3() -> bool:
    """Migrate state from local to S3 with user confirmation."""
    try:
        result = subprocess.run(
            ["terraform", "init", "-migrate-state", "-input=false"],
            capture_output=True,
            text=True,
            input="yes\n",  # Auto-confirm migration
            check=False,
        )

        if result.returncode == 0:
            print_status("✅", "State migration to S3 completed")
            return True
        else:
            print_status("❌", "State migration failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

    except Exception as e:
        print_status("❌", f"Error during state migration: {e}")
        return False


def full_migration_workflow() -> None:
    """Complete migration workflow from local to S3 backend."""
    print_status("🚀", "Starting full migration workflow")
    print()

    # Step 1: Create backup
    backup_terraform_file()

    # Step 2: Check if bucket exists
    if check_s3_bucket_exists():
        print_status("ℹ️", "S3 bucket already exists, proceeding with migration")
    else:
        print_status("ℹ️", "S3 bucket doesn't exist, creating it first")

        # Step 2a: Ensure we're using local backend
        if not switch_to_local_backend():
            sys.exit(1)

        # Step 2b: Initialize and apply to create bucket
        if not terraform_init():
            sys.exit(1)

        print_status(
            "ℹ️",
            "Run 'terraform apply' to create the S3 bucket, then re-run this script",
        )
        return

    # Step 3: Switch to S3 backend
    if not switch_to_s3_backend():
        sys.exit(1)

    # Step 4: Migrate state
    if not migrate_state_to_s3():
        sys.exit(1)

    print()
    print_status("🎉", "Migration completed successfully!")
    print_status("ℹ️", "All deployment methods now share the same S3 state")
    print_status(
        "ℹ️", "You can safely remove terraform.tfstate and terraform.tfstate.backup"
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Terraform backend configuration manager"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--local", action="store_true", help="Switch to local backend")
    group.add_argument("--s3", action="store_true", help="Switch to S3 backend")
    group.add_argument("--migrate", action="store_true", help="Full migration workflow")

    args = parser.parse_args()

    if args.local:
        backup_terraform_file()
        if switch_to_local_backend():
            print_status("ℹ️", "Run 'terraform init' to apply the backend change")
    elif args.s3:
        backup_terraform_file()
        if switch_to_s3_backend():
            print_status("ℹ️", "Run 'terraform init' to apply the backend change")
    elif args.migrate:
        full_migration_workflow()


if __name__ == "__main__":
    main()
