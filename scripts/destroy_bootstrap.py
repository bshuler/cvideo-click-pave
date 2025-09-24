#!/usr/bin/env python3
"""
Destroy bootstrap user setup for cvideo-click-pave infrastructure.

This script completely removes the bootstrap user, role, and policy
so you can start fresh with proper setup.

CRITICAL: This must be run with AWS root account or admin credentials.
"""

import argparse
import boto3
import sys
from botocore.exceptions import ClientError


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def delete_access_keys(iam_client, user_name: str):
    """Delete all access keys for a user."""
    try:
        response = iam_client.list_access_keys(UserName=user_name)
        access_keys = response.get("AccessKeyMetadata", [])

        for key in access_keys:
            key_id = key["AccessKeyId"]
            iam_client.delete_access_key(UserName=user_name, AccessKeyId=key_id)
            print_status("🗑️", f"Deleted access key: {key_id}")

        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")  # type: ignore
        if error_code == "NoSuchEntity":
            print_status("ℹ️", f"No access keys found for {user_name}")
            return True
        else:
            print_status("❌", f"Error deleting access keys: {e}")
            return False


def detach_user_policies(iam_client, user_name: str):
    """Detach all policies from a user."""
    try:
        # Detach managed policies
        response = iam_client.list_attached_user_policies(UserName=user_name)
        for policy in response.get("AttachedPolicies", []):
            iam_client.detach_user_policy(
                UserName=user_name, PolicyArn=policy["PolicyArn"]
            )
            print_status("🔗", f"Detached policy: {policy['PolicyName']}")

        # Delete inline policies
        response = iam_client.list_user_policies(UserName=user_name)
        for policy_name in response.get("PolicyNames", []):
            iam_client.delete_user_policy(UserName=user_name, PolicyName=policy_name)
            print_status("🗑️", f"Deleted inline policy: {policy_name}")

        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")  # type: ignore
        if error_code == "NoSuchEntity":
            print_status("ℹ️", f"User {user_name} not found")
            return True
        else:
            print_status("❌", f"Error detaching policies: {e}")
            return False


def delete_bootstrap_user(iam_client):
    """Delete the bootstrap user."""
    user_name = "bootstrap-user"

    try:
        # First detach policies and delete access keys
        print_status("🔗", f"Cleaning up {user_name}...")

        if not delete_access_keys(iam_client, user_name):
            return False

        if not detach_user_policies(iam_client, user_name):
            return False

        # Delete the user
        iam_client.delete_user(UserName=user_name)
        print_status("✅", f"Deleted user: {user_name}")
        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")  # type: ignore
        if error_code == "NoSuchEntity":
            print_status("ℹ️", f"User {user_name} does not exist")
            return True
        else:
            print_status("❌", f"Error deleting user: {e}")
            return False


def delete_bootstrap_role(iam_client):
    """Delete the bootstrap role."""
    role_name = "PaveBootstrapRole"

    try:
        # Detach policies from role
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in response.get("AttachedPolicies", []):
            iam_client.detach_role_policy(
                RoleName=role_name, PolicyArn=policy["PolicyArn"]
            )
            print_status("🔗", f"Detached policy from role: {policy['PolicyName']}")

        # Delete inline policies
        response = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in response.get("PolicyNames", []):
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
            print_status("🗑️", f"Deleted inline role policy: {policy_name}")

        # Delete the role
        iam_client.delete_role(RoleName=role_name)
        print_status("✅", f"Deleted role: {role_name}")
        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")  # type: ignore
        if error_code == "NoSuchEntity":
            print_status("ℹ️", f"Role {role_name} does not exist")
            return True
        else:
            print_status("❌", f"Error deleting role: {e}")
            return False


def delete_bootstrap_policies(iam_client):
    """Delete bootstrap policies."""
    policy_names = ["PaveBootstrapPolicy", "BootstrapTerraformPolicy"]

    for policy_name in policy_names:
        try:
            # Get account ID for policy ARN
            account_id = boto3.client("sts").get_caller_identity()["Account"]
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

            # First, detach policy from all entities
            print_status("🔗", f"Detaching policy {policy_name} from all entities...")

            # Detach from users
            try:
                response = iam_client.list_entities_for_policy(PolicyArn=policy_arn)

                # Detach from users
                for user in response.get("PolicyUsers", []):
                    iam_client.detach_user_policy(
                        UserName=user["UserName"], PolicyArn=policy_arn
                    )
                    print_status("🔗", f"Detached policy from user: {user['UserName']}")

                # Detach from roles
                for role in response.get("PolicyRoles", []):
                    iam_client.detach_role_policy(
                        RoleName=role["RoleName"], PolicyArn=policy_arn
                    )
                    print_status("🔗", f"Detached policy from role: {role['RoleName']}")

                # Detach from groups
                for group in response.get("PolicyGroups", []):
                    iam_client.detach_group_policy(
                        GroupName=group["GroupName"], PolicyArn=policy_arn
                    )
                    print_status(
                        "🔗", f"Detached policy from group: {group['GroupName']}"
                    )

            except ClientError as e:
                if e.response.get("Error", {}).get("Code") != "NoSuchEntity":
                    print_status("⚠️", f"Warning detaching policy {policy_name}: {e}")

            # List and delete all policy versions except default
            response = iam_client.list_policy_versions(PolicyArn=policy_arn)
            for version in response.get("Versions", []):
                if not version["IsDefaultVersion"]:
                    iam_client.delete_policy_version(
                        PolicyArn=policy_arn, VersionId=version["VersionId"]
                    )
                    print_status("🗑️", f"Deleted policy version: {version['VersionId']}")

            # Delete the policy
            iam_client.delete_policy(PolicyArn=policy_arn)
            print_status("✅", f"Deleted policy: {policy_name}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get(
                "Code", "Unknown"
            )  # type: ignore
            if error_code == "NoSuchEntity":
                print_status("ℹ️", f"Policy {policy_name} does not exist")
            else:
                print_status("❌", f"Error deleting policy {policy_name}: {e}")

    return True


def delete_credentials_from_secrets_manager(region="us-east-1"):
    """Delete bootstrap credentials from AWS Secrets Manager."""
    secret_name = "pave/bootstrap-credentials"

    try:
        secrets_client = boto3.client("secretsmanager", region_name=region)

        try:
            # Delete the secret immediately (no recovery period)
            secrets_client.delete_secret(
                SecretId=secret_name, ForceDeleteWithoutRecovery=True
            )
            print_status(
                "✅",
                f"Deleted bootstrap credentials from Secrets Manager: {secret_name}",
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                print_status(
                    "ℹ️",
                    f"No bootstrap credentials found in Secrets Manager: {secret_name}",
                )
                return True
            else:
                print_status("❌", f"Error deleting secret from Secrets Manager: {e}")
                return False

    except Exception as e:
        print_status("❌", f"Error connecting to Secrets Manager: {e}")
        return False


def main():
    """Main destruction workflow."""
    parser = argparse.ArgumentParser(description="Destroy bootstrap user setup")
    parser.add_argument(
        "--skip-confirm", action="store_true", help="Skip confirmation prompts"
    )
    args = parser.parse_args()

    print_status("💥", "DESTROYING Bootstrap User Setup")
    print_status("⚠️", "This will completely remove all bootstrap resources!")
    print_status("⚠️", "Make sure you're running with root/admin credentials")
    print()

    # Confirmation
    if not args.skip_confirm:
        confirm = input(
            "Are you sure you want to destroy the bootstrap setup? (type 'yes'): "
        )
        if confirm.lower() != "yes":
            print_status("❌", "Destruction cancelled")
            sys.exit(0)

    try:
        iam_client = boto3.client("iam")
        sts_client = boto3.client("sts")

        # Verify we have admin permissions
        try:
            caller_identity = sts_client.get_caller_identity()
            print_status("👤", f"Running as: {caller_identity.get('Arn', 'Unknown')}")
        except Exception as e:
            print_status("❌", f"Cannot verify identity: {e}")
            sys.exit(1)

        print()

        # Step 1: Delete credentials from Secrets Manager
        print_status("1️⃣", "Deleting credentials from AWS Secrets Manager...")
        delete_credentials_from_secrets_manager()

        # Step 2: Delete bootstrap user
        print_status("2️⃣", "Deleting bootstrap user...")
        delete_bootstrap_user(iam_client)

        # Step 3: Delete bootstrap role
        print_status("3️⃣", "Deleting bootstrap role...")
        delete_bootstrap_role(iam_client)

        # Step 4: Delete bootstrap policies
        print_status("4️⃣", "Deleting bootstrap policies...")
        delete_bootstrap_policies(iam_client)

        print()
        print_status("💥", "Bootstrap setup destroyed successfully!")
        print()
        print_status("📋", "Next Steps:")
        print_status(
            "🔧",
            "1. Run 'python3 scripts/create_bootstrap.py' to recreate "
            "with proper permissions",
        )
        print_status("🔧", "2. Update .secrets file with new credentials")
        print_status("🔧", "3. Run 'make bootstrap-check' to verify")

    except Exception as e:
        print_status("❌", f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
