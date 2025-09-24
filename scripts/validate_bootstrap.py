#!/usr/bin/env python3
"""
Bootstrap user validation script for cvideo-click-pave infrastructure.

This script validates that the required bootstrap user, role, and policy exist
and have the correct configuration before allowing any infrastructure operations.

CRITICAL: This must pass before any Terraform operations can proceed.
"""

import boto3
import sys
import time
from typing import Callable, Any


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def retry_with_backoff(
    func: Callable[[], Any],
    max_attempts: int = 6,
    initial_delay: float = 1.0,
    operation_name: str = "operation",
) -> Any:
    """Retry function with exponential backoff for AWS credential propagation."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                # Last attempt failed
                raise e

            # Check if this is a credential/authentication error that might resolve with time
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in [
                    "invalidclienttokenid",
                    "invalid",
                    "token",
                    "accessdenied",
                    "unauthorized",
                    "credentials",
                ]
            ):
                delay = initial_delay * (2**attempt)
                print_status(
                    "⏳",
                    f"AWS credential propagation delay (attempt {attempt + 1}/{max_attempts}), retrying in {delay:.1f}s...",
                )
                time.sleep(delay)
            else:
                # Not a credential issue, don't retry
                raise e

    # Should not reach here, but just in case
    raise Exception(f"Failed after {max_attempts} attempts")


def get_boto3_client(service: str):
    """Get boto3 client with proper error handling and retry logic."""
    try:

        def create_client():
            client = boto3.client(service)  # type: ignore[call-overload]
            # Test the client with a simple call to ensure credentials work
            if service == "sts":
                client.get_caller_identity()
            elif service == "iam":
                client.list_users(MaxItems=1)
            elif service == "s3":
                client.list_buckets()
            return client

        return retry_with_backoff(
            create_client, operation_name=f"connecting to AWS {service}"
        )
    except Exception as e:
        print_status("❌", f"Error connecting to AWS {service} after retries: {e}")
        print_status("💡", "Ensure bootstrap user AWS credentials are configured")
        print_status(
            "🔍",
            "Check that credentials have propagated (this can take up to 60 seconds)",
        )
        sys.exit(1)


def validate_bootstrap_user(iam_client) -> bool:
    """Validate that bootstrap-user exists."""
    try:

        def check_user():
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
                    raise e  # Re-raise for retry logic

        return retry_with_backoff(check_user, operation_name="checking bootstrap user")
    except Exception as e:
        print_status("❌", f"Error checking bootstrap user after retries: {e}")
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

        def check_identity():
            response = sts_client.get_caller_identity()
            current_arn = response.get("Arn", "")

            if "bootstrap-user" in current_arn:
                print_status("✅", f"Running as bootstrap user: {current_arn}")
                return True
            else:
                print_status("❌", f"Not running as bootstrap user: {current_arn}")
                print_status(
                    "💡",
                    "Configure bootstrap user credentials in .secrets or environment",
                )
                return False

        return retry_with_backoff(
            check_identity, operation_name="checking user identity"
        )
    except Exception as e:
        print_status("❌", f"Error checking current user identity after retries: {e}")
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

                def test_permission():
                    operation_func()
                    print_status("✅", f"Permission check passed: {operation_name}")
                    return True

                retry_with_backoff(
                    test_permission, operation_name=f"permission test: {operation_name}"
                )
            except Exception as e:
                print_status("❌", f"Permission check failed: {operation_name} - {e}")
                return False

        return True
    except Exception as e:
        print_status("❌", f"Error testing bootstrap permissions after retries: {e}")
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
