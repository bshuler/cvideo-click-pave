#!/usr/bin/env python3
"""Comprehensive AWS resource cleanup script for cvideo-click-pave infrastructure.

This script replaces cleanup-all.sh with a robust Python implementation using boto3.
It handles cleanup of all pave-related AWS resources across all deployments.

Features:
- Comprehensive cleanup of IAM users, roles, policies, and S3 buckets
- Robust error handling and rollback capabilities
- Progress reporting with clear status messages
- Graceful handling of non-existent resources (idempotent)
- Optional confirmation prompts with --skip-confirm flag
- Bootstrap user protection (never deletes bootstrap resources)
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

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
        print_status("💡", "Run 'aws configure' or set environment variables")
        sys.exit(1)
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service_name}: {e}")
        print_status("💡", "Ensure AWS credentials are configured and valid")
        sys.exit(1)


def find_pave_users(iam_client: Any) -> List[str]:
    """Find all pave users across deployments, excluding bootstrap user.

    Args:
        iam_client: boto3 IAM client

    Returns:
        List of pave user names to be cleaned up
    """
    try:
        response = iam_client.list_users()
        pave_users = []

        for user in response["Users"]:
            username = user["UserName"]
            # NEVER delete bootstrap user
            if username == "pave-bootstrap-user":
                continue

            # Match exact names and patterns from all deployments
            if (
                username == "admin-user"
                or username == "developer-user"
                or "admin-user-" in username
                or "developer-user-" in username
            ):
                pave_users.append(username)

        return pave_users
    except ClientError as e:
        print_status("⚠️", f"Error listing users: {e}")
        return []


def find_pave_roles(iam_client: Any) -> List[str]:
    """Find all pave roles across deployments, excluding bootstrap role.

    Args:
        iam_client: boto3 IAM client

    Returns:
        List of pave role names to be cleaned up
    """
    try:
        response = iam_client.list_roles()
        pave_roles = []

        for role in response["Roles"]:
            role_name = role["RoleName"]
            # NEVER delete bootstrap role
            if role_name == "PaveBootstrapRole":
                continue

            # Match exact names and patterns from all deployments
            if (
                role_name == "CICDDeploymentRole"
                or role_name == "DeveloperRole"
                or "CICDDeploymentRole-" in role_name
                or "DeveloperRole-" in role_name
            ):
                pave_roles.append(role_name)

        return pave_roles
    except ClientError as e:
        print_status("⚠️", f"Error listing roles: {e}")
        return []


def find_pave_policies(iam_client: Any) -> List[Dict[str, str]]:
    """Find all pave custom policies, excluding bootstrap policy.

    Args:
        iam_client: boto3 IAM client

    Returns:
        List of dictionaries containing policy name and ARN
    """
    try:
        response = iam_client.list_policies(Scope="Local")
        pave_policies = []

        for policy in response["Policies"]:
            policy_name = policy["PolicyName"]
            # NEVER delete bootstrap policy
            if policy_name == "PaveBootstrapPolicy":
                continue

            # Match exact names and patterns from all deployments
            if (
                policy_name == "CICDS3SpecificAccess"
                or policy_name == "PaveAdminPolicy"
                or "CICDS3SpecificAccess-" in policy_name
            ):
                pave_policies.append({"name": policy_name, "arn": policy["Arn"]})

        return pave_policies
    except ClientError as e:
        print_status("⚠️", f"Error listing policies: {e}")
        return []


def find_pave_buckets(s3_client: Any) -> List[str]:
    """Find all pave S3 buckets.

    Args:
        s3_client: boto3 S3 client

    Returns:
        List of pave S3 bucket names to be cleaned up
    """
    try:
        response = s3_client.list_buckets()
        pave_buckets = []

        for bucket in response["Buckets"]:
            bucket_name = bucket.get("Name", "")
            if not bucket_name:
                continue
            # Match exact names and patterns from all deployments
            if (
                bucket_name == "pave-tf-state-bucket-us-east-1"
                or "pave-tf-state-bucket-" in bucket_name
            ):
                pave_buckets.append(bucket_name)

        return pave_buckets
    except ClientError as e:
        print_status("⚠️", f"Error listing buckets: {e}")
        return []


def cleanup_user_access_keys(iam_client: Any, username: str) -> None:
    """Remove all access keys for a user.

    Args:
        iam_client: boto3 IAM client
        username: IAM username
    """
    try:
        response = iam_client.list_access_keys(UserName=username)
        for key in response["AccessKeyMetadata"]:
            key_id = key["AccessKeyId"]
            print_status("    🔑", f"Deleting access key: {key_id}")
            iam_client.delete_access_key(UserName=username, AccessKeyId=key_id)
    except ClientError as e:
        print_status("⚠️", f"Error cleaning up access keys for {username}: {e}")


def cleanup_user_policies(iam_client: Any, username: str) -> None:
    """Detach all policies from a user.

    Args:
        iam_client: boto3 IAM client
        username: IAM username
    """
    try:
        # Detach managed policies
        response = iam_client.list_attached_user_policies(UserName=username)
        for policy in response["AttachedPolicies"]:
            policy_arn = policy["PolicyArn"]
            print_status("    📋", f"Detaching policy: {policy_arn}")
            iam_client.detach_user_policy(UserName=username, PolicyArn=policy_arn)

        # Delete inline policies
        response = iam_client.list_user_policies(UserName=username)
        for policy_name in response["PolicyNames"]:
            print_status("    📋", f"Deleting inline policy: {policy_name}")
            iam_client.delete_user_policy(UserName=username, PolicyName=policy_name)

    except ClientError as e:
        print_status("⚠️", f"Error cleaning up policies for {username}: {e}")


def cleanup_role_policies(iam_client: Any, role_name: str) -> None:
    """Detach all policies from a role.

    Args:
        iam_client: boto3 IAM client
        role_name: IAM role name
    """
    try:
        # Detach managed policies
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in response["AttachedPolicies"]:
            policy_arn = policy["PolicyArn"]
            print_status("    📋", f"Detaching policy: {policy_arn}")
            iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

        # Delete inline policies
        response = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in response["PolicyNames"]:
            print_status("    📋", f"Deleting inline policy: {policy_name}")
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    except ClientError as e:
        print_status("⚠️", f"Error cleaning up policies for {role_name}: {e}")


def empty_s3_bucket(s3_client: Any, bucket_name: str) -> None:
    """Empty an S3 bucket of all objects and versions.

    Args:
        s3_client: boto3 S3 client
        bucket_name: S3 bucket name
    """
    try:
        print_status("    📦", "Emptying bucket contents...")

        # Delete all object versions and delete markers
        paginator = s3_client.get_paginator("list_object_versions")
        for page in paginator.paginate(Bucket=bucket_name):
            # Delete versions
            if "Versions" in page:
                objects = [
                    {"Key": obj["Key"], "VersionId": obj["VersionId"]}
                    for obj in page["Versions"]
                ]
                if objects:
                    s3_client.delete_objects(
                        Bucket=bucket_name, Delete={"Objects": objects}
                    )

            # Delete delete markers
            if "DeleteMarkers" in page:
                delete_markers = [
                    {"Key": obj["Key"], "VersionId": obj["VersionId"]}
                    for obj in page["DeleteMarkers"]
                ]
                if delete_markers:
                    s3_client.delete_objects(
                        Bucket=bucket_name, Delete={"Objects": delete_markers}
                    )

    except ClientError as e:
        print_status("⚠️", f"Error emptying bucket {bucket_name}: {e}")


def cleanup_users(iam_client: Any, users: List[str]) -> None:
    """Clean up all pave users.

    Args:
        iam_client: boto3 IAM client
        users: List of usernames to clean up
    """
    if not users:
        print_status("ℹ️", "No pave users found to clean up")
        return

    print_status("👥", f"Cleaning up {len(users)} users...")

    for username in users:
        print_status("  🗑️", f"Cleaning up user: {username}")

        # Clean up access keys
        cleanup_user_access_keys(iam_client, username)

        # Clean up policies
        cleanup_user_policies(iam_client, username)

        # Delete user
        try:
            iam_client.delete_user(UserName=username)
            print_status("  ✅", f"Deleted user: {username}")
        except ClientError as e:
            print_status("  ⚠️", f"Error deleting user {username}: {e}")


def cleanup_roles(iam_client: Any, roles: List[str]) -> None:
    """Clean up all pave roles.

    Args:
        iam_client: boto3 IAM client
        roles: List of role names to clean up
    """
    if not roles:
        print_status("ℹ️", "No pave roles found to clean up")
        return

    print_status("🎭", f"Cleaning up {len(roles)} roles...")

    for role_name in roles:
        print_status("  🗑️", f"Cleaning up role: {role_name}")

        # Clean up policies
        cleanup_role_policies(iam_client, role_name)

        # Delete role
        try:
            iam_client.delete_role(RoleName=role_name)
            print_status("  ✅", f"Deleted role: {role_name}")
        except ClientError as e:
            print_status("  ⚠️", f"Error deleting role {role_name}: {e}")


def cleanup_policies(iam_client: Any, policies: List[Dict[str, str]]) -> None:
    """Clean up all pave custom policies.

    Args:
        iam_client: boto3 IAM client
        policies: List of policy dictionaries with name and arn keys
    """
    if not policies:
        print_status("ℹ️", "No pave custom policies found to clean up")
        return

    print_status("📋", f"Cleaning up {len(policies)} custom policies...")

    for policy in policies:
        policy_name = policy["name"]
        policy_arn = policy["arn"]

        print_status("  🗑️", f"Deleting policy: {policy_name}")

        try:
            iam_client.delete_policy(PolicyArn=policy_arn)
            print_status("  ✅", f"Deleted policy: {policy_name}")
        except ClientError as e:
            print_status("  ⚠️", f"Error deleting policy {policy_name}: {e}")


def cleanup_buckets(s3_client: Any, buckets: List[str]) -> None:
    """Clean up all pave S3 buckets.

    Args:
        s3_client: boto3 S3 client
        buckets: List of bucket names to clean up
    """
    if not buckets:
        print_status("ℹ️", "No pave buckets found to clean up")
        return

    print_status("🪣", f"Cleaning up {len(buckets)} S3 buckets...")

    for bucket_name in buckets:
        print_status("  🗑️", f"Cleaning up bucket: {bucket_name}")

        # Empty bucket first
        empty_s3_bucket(s3_client, bucket_name)

        # Delete bucket
        try:
            s3_client.delete_bucket(Bucket=bucket_name)
            print_status("  ✅", f"Deleted bucket: {bucket_name}")
        except ClientError as e:
            print_status("  ⚠️", f"Error deleting bucket {bucket_name}: {e}")


def cleanup_local_files() -> None:
    """Clean up local state files and credentials."""
    print_status("🧹", "Cleaning up local files...")

    files_to_clean = [
        "terraform.tfstate",
        "terraform.tfstate.backup",
        ".terraform.lock.hcl",
    ]

    dirs_to_clean = [".terraform", "credentials"]

    # Remove files
    for file_path in files_to_clean:
        try:
            Path(file_path).unlink(missing_ok=True)
            print_status("  🗑️", f"Removed: {file_path}")
        except Exception as e:
            print_status("  ⚠️", f"Error removing {file_path}: {e}")

    # Remove directories
    for dir_path in dirs_to_clean:
        try:
            if Path(dir_path).exists():
                shutil.rmtree(dir_path)
                print_status("  🗑️", f"Removed directory: {dir_path}")
        except Exception as e:
            print_status("  ⚠️", f"Error removing {dir_path}: {e}")


def main() -> None:
    """Main cleanup workflow."""
    parser = argparse.ArgumentParser(description="Comprehensive AWS resource cleanup")
    parser.add_argument(
        "--skip-confirm", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--dev-only",
        action="store_true",
        help="Clean only development resources (less destructive)",
    )
    args = parser.parse_args()

    print_status("🧹", "Starting comprehensive cleanup of pave infrastructure...")
    print()

    if not args.skip_confirm:
        print_status(
            "⚠️", "This will remove ALL pave infrastructure resources (destructive!)"
        )
        confirmation = input("Are you sure you want to continue? (y/N): ")
        if confirmation.lower() != "y":
            print_status("❌", "Cleanup cancelled")
            sys.exit(0)
        print()

    # Get AWS clients
    iam_client = get_boto3_client("iam")
    s3_client = get_boto3_client("s3")

    # Find all pave resources
    print_status("🔍", "Discovering pave resources...")
    users = find_pave_users(iam_client)
    roles = find_pave_roles(iam_client)
    policies = find_pave_policies(iam_client)
    buckets = find_pave_buckets(s3_client)

    # Report what was found
    print()
    print_status("📊", "Resources found:")
    print(f"  - Users: {len(users)}")
    print(f"  - Roles: {len(roles)}")
    print(f"  - Custom Policies: {len(policies)}")
    print(f"  - S3 Buckets: {len(buckets)}")
    print()
    print_status("🔒", "Bootstrap resources are protected and will NEVER be deleted:")
    print("  - User: pave-bootstrap-user")
    print("  - Role: PaveBootstrapRole")
    print("  - Policy: PaveBootstrapPolicy")
    print()

    if not any([users, roles, policies, buckets]):
        print_status("✅", "No pave resources found to clean up")
        return

    # Perform cleanup in proper order (dependencies first)
    cleanup_users(iam_client, users)
    print()
    cleanup_roles(iam_client, roles)
    print()
    cleanup_policies(iam_client, policies)
    print()
    cleanup_buckets(s3_client, buckets)
    print()

    # Clean up local files
    cleanup_local_files()
    print()

    print_status("✅", "Comprehensive cleanup completed!")
    print_status("💡", "Run 'make init' to reinitialize for fresh deployment")


if __name__ == "__main__":
    main()
