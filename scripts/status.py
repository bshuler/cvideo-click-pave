#!/usr/bin/env python3
"""
Status checker for cvideo-click-pave infrastructure.

Shows current status of AWS resources and local configuration.
"""

import boto3
import subprocess
from pathlib import Path


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def get_terraform_status():
    """Get Terraform initialization and state status."""
    terraform_dir = Path(".terraform")
    state_file = Path("terraform.tfstate")

    if not terraform_dir.exists():
        return "Not initialized", "Run 'make init'"

    if not state_file.exists():
        return "Initialized, no state", "Run 'make apply' to deploy"

    try:
        result = subprocess.run(
            ["terraform", "show", "-json"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip() == "{}":
            return "No resources deployed", "Run 'make apply' to deploy"
        else:
            return "Resources deployed", "Ready for operations"
    except Exception:
        return "State file exists", "Unknown status"


def get_aws_resources():
    """Get count of deployed AWS resources."""
    try:
        iam_client = boto3.client("iam")  # type: ignore[call-overload]
        s3_client = boto3.client("s3")  # type: ignore[call-overload]

        # Count users (exact names or legacy patterns)
        users_response = iam_client.list_users()
        pave_users = [
            u["UserName"]
            for u in users_response["Users"]
            if (
                u["UserName"] == "admin-user"
                or u["UserName"] == "developer-user"
                or "admin-user-" in u["UserName"]
                or "developer-user-" in u["UserName"]
            )
        ]

        # Count roles (exact names or legacy patterns)
        roles_response = iam_client.list_roles()
        pave_roles = [
            r["RoleName"]
            for r in roles_response["Roles"]
            if (
                r["RoleName"] == "CICDDeploymentRole"
                or r["RoleName"] == "DeveloperRole"
                or "CICDDeploymentRole-" in r["RoleName"]
                or "DeveloperRole-" in r["RoleName"]
            )
        ]  # Count buckets
        buckets_response = s3_client.list_buckets()
        pave_buckets = [
            b.get("Name", "")
            for b in buckets_response["Buckets"]
            if b.get("Name") and "pave-tf-state-bucket-" in b.get("Name", "")
        ]

        return {
            "users": len(pave_users),
            "roles": len(pave_roles),
            "buckets": len(pave_buckets),
            "user_names": pave_users[:3],  # Show first 3
            "role_names": pave_roles[:3],
            "bucket_names": pave_buckets[:3],
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main status check."""
    print_status("📊", "CVideo Click Pave - Infrastructure Status")
    print()

    # Local status
    print_status("🏠", "Local Environment:")
    terraform_status, terraform_advice = get_terraform_status()
    print(f"  Terraform: {terraform_status}")
    if terraform_advice:
        print(f"  💡 {terraform_advice}")

    credentials_dir = Path("credentials")
    if credentials_dir.exists():
        cred_files = list(credentials_dir.glob("*.env"))
        print(f"  Credentials: {len(cred_files)} files")
    else:
        print("  Credentials: None generated")
        print("  💡 Run 'make credentials' after deployment")

    print()

    # AWS resources status
    print_status("☁️", "AWS Resources:")
    try:
        resources = get_aws_resources()
        if "error" in resources:
            print(f"  ❌ Error: {resources['error']}")
            print("  💡 Check AWS credentials with 'make validate'")
        else:
            print(f"  Users: {resources['users']}")
            if resources["user_names"]:
                for user in resources["user_names"]:
                    print(f"    - {user}")

            print(f"  Roles: {resources['roles']}")
            if resources["role_names"]:
                for role in resources["role_names"]:
                    print(f"    - {role}")

            print(f"  S3 Buckets: {resources['buckets']}")
            if resources["bucket_names"]:
                for bucket in resources["bucket_names"]:
                    print(f"    - {bucket}")

            if (
                resources["users"] == 0
                and resources["roles"] == 0
                and resources["buckets"] == 0
            ):
                print("  💡 No resources found - run 'make apply' to deploy")

    except ImportError:
        print("  ❌ boto3 not available")
        print("  💡 Run 'make init' to install dependencies")

    print()
    print_status("🚀", "Quick Commands:")
    print("  make help        - Show all available commands")
    print("  make init        - Initialize environment")
    print("  make apply       - Deploy infrastructure")
    print("  make credentials - Generate credential files")
    print("  make clean       - Clean up all resources")


if __name__ == "__main__":
    main()
