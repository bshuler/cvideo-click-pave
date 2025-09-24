#!/usr/bin/env python3
"""
Infrastructure health test script
Tests deployed AWS infrastructure components
"""

import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError


def test_aws_connectivity():
    """Test basic AWS connectivity"""
    print("🔍 Testing AWS connectivity...")
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f'✅ Connected as: {identity.get("Arn", "Unknown")}')
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return False
    except Exception as e:
        print(f"❌ AWS connectivity failed: {e}")
        return False


def test_iam_resources():
    """Test IAM users and roles"""
    print("🔍 Testing IAM resources...")
    try:
        iam = boto3.client("iam")

        # Test users
        users = iam.list_users()
        user_names = [user["UserName"] for user in users["Users"]]
        expected_users = ["admin-user", "developer-user"]

        for user in expected_users:
            if user in user_names:
                print(f"✅ User {user} exists")
            else:
                print(f"❌ User {user} missing")
                return False

        # Test roles
        roles = iam.list_roles()
        role_names = [role["RoleName"] for role in roles["Roles"]]
        expected_roles = ["CICDDeploymentRole", "DeveloperRole"]

        for role in expected_roles:
            if role in role_names:
                print(f"✅ Role {role} exists")
            else:
                print(f"❌ Role {role} missing")
                return False

        return True
    except Exception as e:
        print(f"❌ IAM test failed: {e}")
        return False


def test_s3_backend():
    """Test S3 backend bucket"""
    print("🔍 Testing S3 backend...")
    try:
        s3 = boto3.client("s3")
        bucket_name = "pave-tf-state-bucket-us-east-1"

        # Test bucket exists and is accessible
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket {bucket_name} exists and accessible")

        # Test state file
        try:
            objects = s3.list_objects_v2(
                Bucket=bucket_name, Prefix="pave/terraform.tfstate"
            )
            if objects.get("Contents"):
                print("✅ Terraform state file exists in S3")
            else:
                print(
                    "⚠️  No Terraform state file found (this is OK for fresh deployments)"
                )
        except Exception as e:
            print(f"❌ Error checking state file: {e}")

        return True
    except Exception as e:
        print(f"❌ S3 bucket test failed: {e}")
        return False


def test_secrets_manager():
    """Test AWS Secrets Manager"""
    print("🔍 Testing AWS Secrets Manager...")
    try:
        secrets = boto3.client("secretsmanager")

        # List secrets to see if root credentials are stored
        response = secrets.list_secrets()
        secret_names = [secret["Name"] for secret in response["SecretList"]]

        if "pave/root-credentials" in secret_names:
            print("✅ Root credentials secret exists in Secrets Manager")
        else:
            print("⚠️  Root credentials secret not found (may have been cleaned up)")

        return True
    except ClientError as e:
        if "AccessDeniedException" in str(e):
            print(
                "⚠️  Secrets Manager access denied (bootstrap user has limited permissions)"
            )
            return True  # This is expected for bootstrap user
        else:
            print(f"❌ Secrets Manager test failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Secrets Manager test failed: {e}")
        return False


def main():
    """Run all infrastructure tests"""
    print("🏗️  Testing deployed AWS infrastructure...")
    print("")

    success = True

    # Run all tests
    tests = [
        test_aws_connectivity,
        test_iam_resources,
        test_s3_backend,
        test_secrets_manager,
    ]

    for test in tests:
        if not test():
            success = False
        print("")

    if success:
        print("✅ Infrastructure health check completed successfully!")
        sys.exit(0)
    else:
        print("❌ Infrastructure health check failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
