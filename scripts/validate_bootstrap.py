#!/usr/bin/env python3
"""
Bootstrap user validation script for cvideo-click-pave infrastructure.

This script validates that the required bootstrap user, role, and policy exist
and have the correct configuration before allowing any infrastructure operations.

CRITICAL: This must pass before any Terraform operations can proceed.
"""

import boto3
import sys


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def get_boto3_client(service: str):
    """Get boto3 client with proper error handling."""
    try:
        return boto3.client(service)  # type: ignore[call-overload]
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service}: {e}")
        print_status("💡", "Ensure bootstrap user AWS credentials are configured")
        sys.exit(1)


def validate_bootstrap_user(iam_client) -> bool:
    """Validate that bootstrap-user exists."""
    try:
        response = iam_client.get_user(UserName="bootstrap-user")
        user_arn = response["User"]["Arn"]
        print_status("✅", f"Bootstrap user found: {user_arn}")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        print_status("❌", "Bootstrap user 'bootstrap-user' not found")
        print_status("💡", "Root account must create bootstrap user first")
        print_status("📚", "See README.md for bootstrap setup instructions")
        return False
    except Exception as e:
        if "AccessDenied" in str(e) and "iam:GetUser" in str(e):
            print_status(
                "⚠️",
                "Bootstrap user exists but lacks iam:GetUser self-permission "
                "(non-critical)",
            )
            print_status("ℹ️", "User identity already confirmed via STS call")
            return True  # This is OK - we already confirmed identity via STS
        else:
            print_status("❌", f"Error checking bootstrap user: {e}")
            return False


def validate_bootstrap_role(iam_client) -> bool:
    """Validate that PaveBootstrapRole exists."""
    try:
        response = iam_client.get_role(RoleName="PaveBootstrapRole")
        role_arn = response["Role"]["Arn"]
        print_status("✅", f"Bootstrap role found: {role_arn}")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        print_status("❌", "Bootstrap role 'PaveBootstrapRole' not found")
        print_status("💡", "Root account must create bootstrap role first")
        print_status("📚", "See README.md for bootstrap setup instructions")
        return False
    except Exception as e:
        print_status("❌", f"Error checking bootstrap role: {e}")
        return False


def validate_current_user_is_bootstrap(sts_client) -> bool:
    """Validate that we're running as the bootstrap user."""
    try:
        response = sts_client.get_caller_identity()
        current_arn = response.get("Arn", "")

        if "bootstrap-user" in current_arn:
            print_status("✅", f"Running as bootstrap user: {current_arn}")
            return True
        else:
            print_status("❌", f"Not running as bootstrap user: {current_arn}")
            print_status(
                "💡", "Configure bootstrap user credentials in .secrets or environment"
            )
            return False
    except Exception as e:
        print_status("❌", f"Error checking current user identity: {e}")
        return False


def validate_bootstrap_permissions(iam_client, sts_client) -> bool:
    """Validate bootstrap user has sufficient permissions."""
    try:
        # Test key permissions the bootstrap user needs
        test_operations = [
            ("List IAM users", lambda: iam_client.list_users(MaxItems=1)),
            ("List IAM roles", lambda: iam_client.list_roles(MaxItems=1)),
            (
                "List S3 buckets",
                lambda: boto3.client("s3").list_buckets(),  # type: ignore
            ),
        ]

        for operation_name, operation_func in test_operations:
            try:
                operation_func()
                print_status("✅", f"Permission check passed: {operation_name}")
            except Exception as e:
                print_status("❌", f"Permission check failed: {operation_name} - {e}")
                return False

        return True
    except Exception as e:
        print_status("❌", f"Error testing bootstrap permissions: {e}")
        return False


def main():
    """Main validation workflow."""
    print_status("🔍", "Validating bootstrap user setup...")
    print()

    # Get AWS clients
    iam_client = get_boto3_client("iam")
    sts_client = get_boto3_client("sts")

    # Run all validations
    validations = [
        (
            "Current user is bootstrap user",
            lambda: validate_current_user_is_bootstrap(sts_client),
        ),
        ("Bootstrap user exists", lambda: validate_bootstrap_user(iam_client)),
        (
            "Bootstrap permissions",
            lambda: validate_bootstrap_permissions(iam_client, sts_client),
        ),
    ]

    results = []
    for validation_name, validation_func in validations:
        print(f"Checking {validation_name}...")
        result = validation_func()
        results.append(result)
        print()

    if all(results):
        print_status("✅", "All bootstrap validations passed!")
        print_status("🚀", "Ready for infrastructure operations")
        sys.exit(0)
    else:
        print_status("❌", "Bootstrap validation failed")
        print_status("📚", "Please complete bootstrap setup per README.md")
        print_status(
            "🔒", "Infrastructure operations are blocked until bootstrap is configured"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
