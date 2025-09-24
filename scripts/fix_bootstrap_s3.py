#!/usr/bin/env python3
"""
Fix bootstrap user S3 permissions for cvideo-click-pave infrastructure.

This script fixes the current bootstrap user's policy to include the missing
S3 ListAllMyBuckets permission that's causing the validation to fail.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def fix_bootstrap_policy():
    """Fix the bootstrap user's S3 permissions."""
    print_status("🔧", "Fixing bootstrap user S3 permissions...")

    try:
        iam_client = boto3.client("iam")

        # Get current policy ARN
        current_policy_arn = "arn:aws:iam::256140316797:policy/BootstrapTerraformPolicy"

        # New policy document with proper S3 permissions
        new_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "IAMPermissions",
                    "Effect": "Allow",
                    "Action": [
                        "iam:CreateUser",
                        "iam:DeleteUser",
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:AttachUserPolicy",
                        "iam:DetachUserPolicy",
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:CreatePolicy",
                        "iam:DeletePolicy",
                        "iam:CreateAccessKey",
                        "iam:DeleteAccessKey",
                        "iam:UpdateUser",
                        "iam:UpdateRole",
                        "iam:Get*",
                        "iam:List*",
                        "iam:CreateOpenIDConnectProvider",
                        "iam:DeleteOpenIDConnectProvider",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "S3StatePermissions",
                    "Effect": "Allow",
                    "Action": [
                        "s3:CreateBucket",
                        "s3:DeleteBucket",
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:DeleteObject",
                        "s3:GetBucketVersioning",
                        "s3:PutBucketVersioning",
                    ],
                    "Resource": [
                        "arn:aws:s3:::pave-tf-state-bucket-us-east-1",
                        "arn:aws:s3:::pave-tf-state-bucket-us-east-1/*",
                    ],
                },
                {
                    "Sid": "S3GlobalPermissions",
                    "Effect": "Allow",
                    "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
                    "Resource": "*",
                },
                {
                    "Sid": "ComputePermissions",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:*",
                        "lambda:*",
                        "codebuild:*",
                        "codepipeline:*",
                        "codedeploy:*",
                    ],
                    "Resource": "*",
                },
            ],
        }

        # Create new policy version
        response = iam_client.create_policy_version(
            PolicyArn=current_policy_arn,
            PolicyDocument=json.dumps(new_policy_document),
            SetAsDefault=True,
        )

        print_status(
            "✅", f"Updated policy version: {response['PolicyVersion']['VersionId']}"
        )
        print_status("🔍", "Testing S3 permissions...")

        # Test the fix
        s3_client = boto3.client("s3")
        buckets = s3_client.list_buckets()
        bucket_count = len(buckets.get("Buckets", []))
        print_status("✅", f"S3 permission test passed! Found {bucket_count} buckets")

        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")  # type: ignore
        print_status("❌", f"Error fixing policy: {error_code} - {e}")
        return False
    except Exception as e:
        print_status("❌", f"Unexpected error: {e}")
        return False


def main():
    """Main fix workflow."""
    print_status("🚀", "Fixing Bootstrap User S3 Permissions")
    print()

    # Verify current user
    try:
        sts_client = boto3.client("sts")
        identity = sts_client.get_caller_identity()
        print_status("👤", f"Running as: {identity.get('Arn', 'Unknown')}")

        if "bootstrap-user" not in identity.get("Arn", ""):
            print_status("⚠️", "Not running as bootstrap-user, but continuing...")

    except Exception as e:
        print_status("❌", f"Cannot verify identity: {e}")
        sys.exit(1)

    print()

    if fix_bootstrap_policy():
        print()
        print_status("🎉", "Bootstrap user S3 permissions fixed successfully!")
        print_status("🔍", "Run 'make bootstrap-check' to verify the fix")
    else:
        print()
        print_status("❌", "Failed to fix bootstrap user permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
