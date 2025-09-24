#!/usr/bin/env python3
"""
Terraform state migration script for cvideo-click-pave infrastructure.

This script handles the migration from local Terraform state to S3 remote backend.
It solves the chicken-and-egg problem where the S3 bucket for state storage
is created by the same Terraform configuration.

Migration Process:
1. Verify current local state exists
2. Ensure S3 bucket exists (create if needed)
3. Migrate state to S3 backend
4. Verify migration succeeded
"""

import json
import logging
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


def check_local_state() -> bool:
    """Check if local Terraform state exists."""
    state_file = Path("terraform.tfstate")
    if not state_file.exists():
        print_status("ℹ️", "No local terraform.tfstate found")
        return False

    try:
        with open(state_file, "r") as f:
            state_data = json.load(f)

        resources = state_data.get("resources", [])
        print_status("✅", f"Local state found with {len(resources)} resources")
        return True
    except json.JSONDecodeError:
        print_status("❌", "Local state file is corrupted")
        return False


def ensure_s3_bucket_exists() -> bool:
    """Ensure the S3 state bucket exists, create if necessary."""
    s3_client = get_boto3_client("s3")
    bucket_name = "pave-tf-state-bucket-us-east-1"

    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print_status("✅", f"S3 state bucket {bucket_name} already exists")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            print_status("ℹ️", f"S3 state bucket {bucket_name} does not exist")
            # The bucket should be created by Terraform, not here
            return False
        else:
            print_status("❌", f"Error checking S3 bucket: {e}")
            return False


def migrate_state_to_s3() -> bool:
    """Migrate Terraform state from local to S3 backend."""
    print_status("🔄", "Migrating Terraform state to S3 backend...")

    try:
        # Run terraform init to migrate state
        result = subprocess.run(
            ["terraform", "init", "-migrate-state", "-input=false"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print_status("✅", "State migration completed successfully")
            return True
        else:
            print_status("❌", "State migration failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

    except FileNotFoundError:
        print_status("❌", "Terraform not found in PATH")
        return False
    except Exception as e:
        print_status("❌", f"Error during state migration: {e}")
        return False


def verify_remote_state() -> bool:
    """Verify that remote state is working correctly."""
    try:
        result = subprocess.run(
            ["terraform", "state", "list"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            resources = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            print_status("✅", f"Remote state verified with {len(resources)} resources")
            return True
        else:
            print_status("❌", "Failed to verify remote state")
            return False

    except Exception as e:
        print_status("❌", f"Error verifying remote state: {e}")
        return False


def main() -> None:
    """Main migration workflow."""
    print_status("🚀", "Starting Terraform state migration to S3 backend")
    print()

    # Step 1: Check current state
    if not check_local_state():
        print_status(
            "ℹ️", "No local state to migrate - you can proceed with normal deployment"
        )
        return

    # Step 2: Ensure S3 bucket exists
    if not ensure_s3_bucket_exists():
        print_status("💡", "S3 bucket doesn't exist yet")
        print_status("💡", "The bucket will be created during the first deployment")
        print_status(
            "💡", "After first deployment, run this script again to migrate state"
        )
        return

    # Step 3: Migrate state
    if not migrate_state_to_s3():
        print_status("❌", "State migration failed")
        sys.exit(1)

    # Step 4: Verify remote state
    if not verify_remote_state():
        print_status("❌", "Remote state verification failed")
        sys.exit(1)

    print()
    print_status("🎉", "State migration completed successfully!")
    print_status("ℹ️", "All deployment methods now share the same state")
    print_status("ℹ️", "Local terraform.tfstate file can be safely removed")


if __name__ == "__main__":
    main()
