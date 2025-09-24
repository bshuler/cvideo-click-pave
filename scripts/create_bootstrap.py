#!/usr/bin/env python3
"""
Bootstrap user creation script for cvideo-click-pave infrastructure.

This script creates the complete bootstrap setup including:
- bootstrap-user (IAM user)
- PaveBootstrapRole (IAM role)
- PaveBootstrapPolicy (IAM policy)

CRITICAL: This must be run with AWS root account or admin credentials.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def print_status(emoji: str, message: str):
    """Print formatted status message."""
    print(f"{emoji} {message}")


def create_bootstrap_policy(iam_client):
    """Create the PaveBootstrapPolicy with proper permissions."""
    policy_name = "PaveBootstrapPolicy"

    # Comprehensive bootstrap policy document
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "FullIAMAccess",
                "Effect": "Allow",
                "Action": ["iam:*"],
                "Resource": "*",
                "Condition": {
                    "StringNotEquals": {"iam:ResourceTag/ProtectedResource": "true"}
                },
            },
            {
                "Sid": "SelfAccess",
                "Effect": "Allow",
                "Action": [
                    "iam:GetUser",
                    "iam:ListAccessKeys",
                    "iam:GetUserPolicy",
                    "iam:ListUserPolicies",
                    "iam:ListAttachedUserPolicies",
                ],
                "Resource": "arn:aws:iam::*:user/bootstrap-user",
            },
            {
                "Sid": "ProtectBootstrapResources",
                "Effect": "Deny",
                "Action": [
                    "iam:DeleteUser",
                    "iam:DeleteRole",
                    "iam:DeletePolicy",
                    "iam:DetachUserPolicy",
                    "iam:DetachRolePolicy",
                ],
                "Resource": [
                    "arn:aws:iam::*:user/bootstrap-user",
                    "arn:aws:iam::*:role/PaveBootstrapRole",
                    "arn:aws:iam::*:policy/PaveBootstrapPolicy",
                ],
            },
            {
                "Sid": "FullS3Access",
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": "*",
            },
            {
                "Sid": "FullLambdaAccess",
                "Effect": "Allow",
                "Action": ["lambda:*"],
                "Resource": "*",
            },
            {
                "Sid": "FullEC2Access",
                "Effect": "Allow",
                "Action": ["ec2:*"],
                "Resource": "*",
            },
            {
                "Sid": "CodeServices",
                "Effect": "Allow",
                "Action": ["codebuild:*", "codepipeline:*", "codedeploy:*"],
                "Resource": "*",
            },
            {
                "Sid": "SupportingServices",
                "Effect": "Allow",
                "Action": ["sts:*", "logs:*", "cloudwatch:*", "apigateway:*"],
                "Resource": "*",
            },
        ],
    }

    try:
        # Try to create the policy
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description="Bootstrap policy for pave infrastructure management",
            Tags=[
                {"Key": "ProtectedResource", "Value": "true"},
                {"Key": "Purpose", "Value": "PaveBootstrap"},
            ],
        )
        policy_arn = response["Policy"]["Arn"]
        print_status("✅", f"Created policy: {policy_name}")
        return policy_arn

    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            # Policy exists, get its ARN
            account_id = boto3.client("sts").get_caller_identity()["Account"]
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            print_status("ℹ️", f"Policy already exists: {policy_name}")
            return policy_arn
        else:
            print_status("❌", f"Error creating policy: {e}")
            return None


def create_bootstrap_role(iam_client, bootstrap_user_arn: str):
    """Create the PaveBootstrapRole."""
    role_name = "PaveBootstrapRole"

    # Trust policy allowing bootstrap user to assume this role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": [bootstrap_user_arn]},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Bootstrap role for pave infrastructure operations",
            Tags=[
                {"Key": "ProtectedResource", "Value": "true"},
                {"Key": "Purpose", "Value": "PaveBootstrap"},
            ],
        )
        role_arn = response["Role"]["Arn"]
        print_status("✅", f"Created role: {role_name}")
        return role_arn

    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            # Role exists, get its ARN
            response = iam_client.get_role(RoleName=role_name)
            role_arn = response["Role"]["Arn"]
            print_status("ℹ️", f"Role already exists: {role_name}")
            return role_arn
        else:
            print_status("❌", f"Error creating role: {e}")
            return None


def cleanup_existing_access_keys(iam_client, user_name: str):
    """Clean up existing access keys for a user to prevent limit issues."""
    try:
        response = iam_client.list_access_keys(UserName=user_name)
        access_keys = response.get("AccessKeyMetadata", [])

        if access_keys:
            print_status(
                "🔍", f"Found {len(access_keys)} existing access key(s) for {user_name}"
            )
            for key in access_keys:
                key_id = key["AccessKeyId"]
                iam_client.delete_access_key(UserName=user_name, AccessKeyId=key_id)
                print_status("🗑️", f"Deleted existing access key: {key_id}")
        else:
            print_status("ℹ️", f"No existing access keys found for {user_name}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print_status("ℹ️", f"User {user_name} does not exist yet")
        else:
            print_status("❌", f"Error checking access keys: {e}")


def create_bootstrap_user(iam_client):
    """Create the bootstrap-user."""
    user_name = "bootstrap-user"

    try:
        response = iam_client.create_user(
            UserName=user_name,
            Tags=[
                {"Key": "ProtectedResource", "Value": "true"},
                {"Key": "Purpose", "Value": "PaveBootstrap"},
            ],
        )
        user_arn = response["User"]["Arn"]
        print_status("✅", f"Created user: {user_name}")
        return user_arn

    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            # User exists, get its ARN
            response = iam_client.get_user(UserName=user_name)
            user_arn = response["User"]["Arn"]
            print_status("ℹ️", f"User already exists: {user_name}")
            return user_arn
        else:
            print_status("❌", f"Error creating user: {e}")
            return None


def attach_policy_to_user(iam_client, user_name: str, policy_arn: str):
    """Attach policy to user."""
    try:
        iam_client.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        print_status("✅", f"Attached policy to {user_name}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print_status("ℹ️", "Policy already attached")
            return True
        else:
            print_status("❌", f"Error attaching policy: {e}")
            return False


def create_access_key(iam_client, user_name: str):
    """Create access key for bootstrap user."""
    try:
        response = iam_client.create_access_key(UserName=user_name)
        access_key = response["AccessKey"]

        print_status("✅", "Created access key for bootstrap user")
        print_status("🔑", f"Access Key ID: {access_key['AccessKeyId']}")
        print_status("🔒", f"Secret Access Key: {access_key['SecretAccessKey']}")
        print_status(
            "⚠️", "SAVE THESE CREDENTIALS SECURELY - They won't be shown again!"
        )

        return access_key
    except ClientError as e:
        print_status("❌", f"Error creating access key: {e}")
        return None


def create_s3_backend_bucket(region="us-east-1"):
    """Create S3 bucket for Terraform backend if it doesn't exist."""
    bucket_name = "pave-tf-state-bucket-us-east-1"

    try:
        s3_client = boto3.client("s3", region_name=region)

        # Check if bucket already exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print_status("ℹ️", f"S3 backend bucket already exists: {bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code != "404":  # Not a "bucket doesn't exist" error
                print_status("❌", f"Error checking bucket: {e}")
                return False

        # Create the bucket
        try:
            if region == "us-east-1":
                # For us-east-1, don't specify LocationConstraint
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                # For other regions, specify LocationConstraint
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        "LocationConstraint": region
                    },  # type: ignore
                )

            print_status("✅", f"Created S3 backend bucket: {bucket_name}")

            # Enable versioning for state file safety
            s3_client.put_bucket_versioning(
                Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"}
            )
            print_status("✅", "Enabled versioning on S3 backend bucket")

            # Enable server-side encryption
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    "Rules": [
                        {
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "AES256"
                            }
                        }
                    ]
                },
            )
            print_status("✅", "Enabled encryption on S3 backend bucket")

            # Block public access
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
            print_status("✅", "Configured public access block on S3 backend bucket")

            return True

        except ClientError as e:
            print_status("❌", f"Error creating S3 bucket: {e}")
            return False

    except Exception as e:
        print_status("❌", f"Error setting up S3 backend bucket: {e}")
        return False


def store_credentials_in_secrets_manager(access_key, region="us-east-1"):
    """Store bootstrap credentials in AWS Secrets Manager with root-only access."""
    secret_name = "pave/bootstrap-credentials"

    try:
        secrets_client = boto3.client("secretsmanager", region_name=region)
        sts_client = boto3.client("sts")

        # Get root account ID
        account_id = sts_client.get_caller_identity()["Account"]

        # Secret value with bootstrap credentials
        secret_value = {
            "AWS_ACCESS_KEY_ID": access_key["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": access_key["SecretAccessKey"],
            "AWS_DEFAULT_REGION": region,
            "AWS_REGION": region,
            "created_by": "pave-bootstrap-script",
            "description": "Bootstrap user credentials for pave infrastructure",
        }

        # Resource policy allowing only root user access
        resource_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                    "Action": "secretsmanager:*",
                    "Resource": "*",
                },
                {
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "secretsmanager:*",
                    "Resource": "*",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:PrincipalArn": (f"arn:aws:iam::{account_id}:root")
                        }
                    },
                },
            ],
        }

        try:
            # Try to update existing secret
            secrets_client.update_secret(
                SecretId=secret_name, SecretString=json.dumps(secret_value)
            )

            # Update resource policy
            secrets_client.put_resource_policy(
                SecretId=secret_name, ResourcePolicy=json.dumps(resource_policy)
            )

            print_status(
                "✅", f"Updated bootstrap credentials in Secrets Manager: {secret_name}"
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                # Create new secret
                secrets_client.create_secret(
                    Name=secret_name,
                    Description=(
                        "Bootstrap user credentials for pave infrastructure "
                        "(root access only)"
                    ),
                    SecretString=json.dumps(secret_value),
                    Tags=[
                        {"Key": "Project", "Value": "pave"},
                        {"Key": "Purpose", "Value": "Bootstrap"},
                        {"Key": "AccessLevel", "Value": "RootOnly"},
                    ],
                )

                # Apply resource policy for newly created secret
                secrets_client.put_resource_policy(
                    SecretId=secret_name, ResourcePolicy=json.dumps(resource_policy)
                )

                print_status(
                    "✅",
                    f"Created bootstrap credentials in Secrets Manager: {secret_name}",
                )
            elif error_code == "InvalidRequestException":
                # Secret is pending deletion, try to restore it first
                try:
                    print_status(
                        "🔄",
                        f"Secret pending deletion, attempting to restore: {secret_name}",
                    )
                    secrets_client.restore_secret(SecretId=secret_name)
                    print_status(
                        "✅", f"Restored secret from pending deletion: {secret_name}"
                    )

                    # Now update the restored secret
                    secrets_client.update_secret(
                        SecretId=secret_name, SecretString=json.dumps(secret_value)
                    )

                    # Update resource policy
                    secrets_client.put_resource_policy(
                        SecretId=secret_name, ResourcePolicy=json.dumps(resource_policy)
                    )

                    print_status(
                        "✅",
                        f"Updated restored bootstrap credentials in Secrets Manager: {secret_name}",
                    )
                except ClientError as restore_error:
                    print_status("❌", f"Failed to restore secret: {restore_error}")
                    return False
            else:
                raise

        return True

    except Exception as e:
        print_status("❌", f"Error storing credentials in Secrets Manager: {e}")
        return False


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


def update_secrets_file(access_key):
    """Update or create .secrets file with new bootstrap credentials."""
    import os
    import shutil

    secrets_path = ".secrets"
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secrets_path = os.path.join(project_root, secrets_path)

    try:
        # Create .secrets content
        secrets_content = f"""AWS_ACCESS_KEY_ID={access_key['AccessKeyId']}
AWS_SECRET_ACCESS_KEY={access_key['SecretAccessKey']}
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
"""

        # Create backup if .secrets exists
        if os.path.exists(secrets_path):
            backup_path = secrets_path + ".backup"
            print_status("💾", "Backed up existing .secrets to .secrets.backup")
            shutil.copy2(secrets_path, backup_path)

        # Write new .secrets file
        with open(secrets_path, "w") as f:
            f.write(secrets_content)

        # Set secure permissions (600)
        os.chmod(secrets_path, 0o600)

        print_status("✅", "Updated .secrets file with new bootstrap credentials")
        return True

    except Exception as e:
        print_status("❌", f"Error updating .secrets file: {e}")
        return False


def main():
    """Main bootstrap creation workflow."""
    print_status("🚀", "Creating Bootstrap User Setup for Pave Infrastructure")
    print_status("⚠️", "This must be run with AWS root account or admin credentials")
    print()

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

        # Step 0: Clean up any existing access keys to prevent limit issues
        print_status("0️⃣", "Checking for existing access keys...")
        cleanup_existing_access_keys(iam_client, "bootstrap-user")

        # Step 1: Create bootstrap user
        print_status("1️⃣", "Creating bootstrap user...")
        user_arn = create_bootstrap_user(iam_client)
        if not user_arn:
            sys.exit(1)

        # Step 2: Create bootstrap policy
        print_status("2️⃣", "Creating bootstrap policy...")
        policy_arn = create_bootstrap_policy(iam_client)
        if not policy_arn:
            sys.exit(1)

        # Step 3: Attach policy to user
        print_status("3️⃣", "Attaching policy to user...")
        if not attach_policy_to_user(iam_client, "bootstrap-user", policy_arn):
            sys.exit(1)

        # Step 4: Create access key
        print_status("4️⃣", "Creating access key...")
        access_key = create_access_key(iam_client, "bootstrap-user")
        if not access_key:
            sys.exit(1)

        # Step 5: Create S3 backend bucket
        print_status("5️⃣", "Creating S3 backend bucket...")
        if not create_s3_backend_bucket():
            sys.exit(1)

        # Step 6: Store credentials in Secrets Manager
        print_status("6️⃣", "Storing credentials in AWS Secrets Manager...")
        if not store_credentials_in_secrets_manager(access_key):
            sys.exit(1)

        # Step 7: Update .secrets file
        print_status("7️⃣", "Updating .secrets file...")
        if not update_secrets_file(access_key):
            sys.exit(1)

        print()
        print_status("🎉", "Bootstrap setup completed successfully!")
        print()
        print_status("📋", "Next Steps:")
        print_status(
            "🔧",
            "1. Clear root credentials: unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY",
        )
        print_status("🔧", "2. Run 'make bootstrap-check' to verify setup")
        print_status("🔧", "3. Run 'make init' to initialize the project")

    except Exception as e:
        print_status("❌", f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
