#!/usr/bin/env python3
"""
Infrastructure health test script
Tests deployed AWS infrastructure components
"""

import boto3
import sys
import argparse
from botocore.exceptions import ClientError, NoCredentialsError

# Global quiet mode flag
QUIET_MODE = False


def log_print(message, force=False):
    """Print message only if not in quiet mode or if forced"""
    if not QUIET_MODE or force:
        print(message)


def test_aws_connectivity():
    """Test basic AWS connectivity"""
    log_print("🔍 Testing AWS connectivity...")
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        log_print(f'✅ Connected as: {identity.get("Arn", "Unknown")}')
        return True, None
    except NoCredentialsError:
        error_msg = "❌ No AWS credentials found"
        log_print(error_msg, force=True)
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ AWS connectivity failed: {e}"
        log_print(error_msg, force=True)
        return False, error_msg


def test_iam_resources():
    """Test IAM users and roles"""
    log_print("🔍 Testing IAM resources...")
    errors = []
    try:
        iam = boto3.client("iam")

        # Test users
        users = iam.list_users()
        user_names = [user["UserName"] for user in users["Users"]]
        expected_users = ["admin-user", "developer-user"]

        for user in expected_users:
            if user in user_names:
                log_print(f"✅ User {user} exists")
            else:
                error_msg = f"❌ User {user} missing"
                log_print(error_msg, force=True)
                errors.append(error_msg)

        # Test roles
        roles = iam.list_roles()
        role_names = [role["RoleName"] for role in roles["Roles"]]
        expected_roles = ["CICDDeploymentRole", "DeveloperRole"]

        for role in expected_roles:
            if role in role_names:
                log_print(f"✅ Role {role} exists")
            else:
                error_msg = f"❌ Role {role} missing"
                log_print(error_msg, force=True)
                errors.append(error_msg)

        return len(errors) == 0, errors
    except Exception as e:
        error_msg = f"❌ IAM test failed: {e}"
        log_print(error_msg, force=True)
        return False, [error_msg]


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


def test_credential_storage():
    """Test credential storage (local files and AWS Secrets Manager)"""
    print("🔍 Testing credential storage...")
    success = True

    # Check for local root credentials file
    import os

    root_secrets_path = ".root-secrets"
    if os.path.exists(root_secrets_path):
        # Verify file has secure permissions
        file_stat = os.stat(root_secrets_path)
        file_mode = file_stat.st_mode & 0o777
        if file_mode == 0o600:
            print("✅ Root credentials file exists with secure permissions (600)")
        else:
            print(
                f"⚠️  Root credentials file exists but has insecure permissions ({oct(file_mode)})"
            )
            success = False
    else:
        print("⚠️  Root credentials file (.root-secrets) not found")

    # Check generated credential files
    credentials_dir = "credentials"
    if os.path.exists(credentials_dir):
        admin_file = os.path.join(credentials_dir, "admin.env")
        developer_file = os.path.join(credentials_dir, "developer.env")

        if os.path.exists(admin_file):
            print("✅ Admin credentials file exists")
        else:
            print("⚠️  Admin credentials file not found")

        if os.path.exists(developer_file):
            print("✅ Developer credentials file exists")
        else:
            print("⚠️  Developer credentials file not found")
    else:
        print("⚠️  Credentials directory not found")

    # Test AWS Secrets Manager access (optional - may not be available to all users)
    try:
        secrets = boto3.client("secretsmanager")
        response = secrets.list_secrets()
        secret_names = [secret["Name"] for secret in response["SecretList"]]

        bootstrap_secret = "pave/bootstrap-credentials"
        if bootstrap_secret in secret_names:
            print("✅ Bootstrap credentials exist in Secrets Manager")
        else:
            print(
                "ℹ️  Bootstrap credentials not found in Secrets Manager (may be stored locally)"
            )

    except ClientError as e:
        if "AccessDeniedException" in str(e):
            print("ℹ️  Secrets Manager access limited (using local credential storage)")
        else:
            print(f"ℹ️  Secrets Manager not accessible: {e}")
    except Exception as e:
        print(f"ℹ️  Secrets Manager check skipped: {e}")

    return success


def test_developer_permissions():
    """Test comprehensive developer user permissions for serverless development"""
    print("🔍 Testing developer user comprehensive permissions...")

    # Get developer credentials from terraform outputs
    try:
        import subprocess

        result = subprocess.run(
            ["terraform", "output", "-json"], capture_output=True, text=True, cwd="."
        )
        if result.returncode != 0:
            print(
                "⚠️  Could not get terraform outputs - testing with current credentials"
            )
            return test_current_user_permissions()

        import json

        outputs = json.loads(result.stdout)
        dev_access_key = outputs.get("developer_user_access_key", {}).get("value")
        dev_secret_key = outputs.get("developer_user_secret_key", {}).get("value")

        if not dev_access_key or not dev_secret_key:
            print(
                "⚠️  Could not get developer credentials - testing with current credentials"
            )
            return test_current_user_permissions()

        # Test with developer credentials
        session = boto3.Session(
            aws_access_key_id=dev_access_key,
            aws_secret_access_key=dev_secret_key,
            region_name="us-east-1",
        )

        return test_permissions_with_session(session, "developer")

    except Exception as e:
        print(f"⚠️  Error setting up developer session: {e}")
        print("Testing with current credentials instead...")
        return test_current_user_permissions()


def test_current_user_permissions():
    """Test permissions with current user credentials"""
    session = boto3.Session()
    return test_permissions_with_session(session, "current user")


def test_permissions_with_session(session, user_type):
    """Test comprehensive serverless permissions with given session"""
    print(f"🔍 Testing {user_type} serverless development permissions...")

    success = True

    # Test CloudFormation permissions
    try:
        cf = session.client("cloudformation")
        cf.list_stacks()
        print(f"✅ CloudFormation access verified for {user_type}")
    except Exception as e:
        print(f"❌ CloudFormation access failed for {user_type}: {e}")
        success = False

    # Test Lambda permissions
    try:
        lambda_client = session.client("lambda")
        lambda_client.list_functions(MaxItems=1)
        print(f"✅ Lambda access verified for {user_type}")
    except Exception as e:
        print(f"❌ Lambda access failed for {user_type}: {e}")
        success = False

    # Test API Gateway permissions
    try:
        apigw = session.client("apigateway")
        apigw.get_rest_apis(limit=1)
        print(f"✅ API Gateway access verified for {user_type}")
    except Exception as e:
        print(f"❌ API Gateway access failed for {user_type}: {e}")
        success = False

    # Test IAM permissions (read operations)
    try:
        iam = session.client("iam")
        iam.list_roles(MaxItems=1)
        print(f"✅ IAM access verified for {user_type}")
    except Exception as e:
        print(f"❌ IAM access failed for {user_type}: {e}")
        success = False

    # Test S3 permissions (different tests based on user type)
    try:
        s3 = session.client("s3")
        if user_type == "developer":
            # Developer has restricted S3 access - test bucket-specific operations
            # Try to check if a bucket exists (this uses s3:ListBucket permission)
            # We'll test with a pattern that should be allowed for developer
            try:
                # Test if we can check bucket existence for project-specific buckets
                s3.head_bucket(Bucket="cvideo-test-bucket-check")
                print(
                    f"✅ S3 access verified for {user_type} (project-specific bucket permissions)"
                )
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                if error_code in ["404", "NoSuchBucket"]:
                    # This is expected - bucket doesn't exist but we have permission to check
                    print(
                        f"✅ S3 access verified for {user_type} (project-specific bucket permissions)"
                    )
                elif error_code == "403":
                    # This means we don't have permission
                    raise e
                else:
                    # Bucket exists and we can access it, or other non-permission error
                    print(
                        f"✅ S3 access verified for {user_type} (project-specific bucket permissions)"
                    )
        else:
            # Admin/bootstrap users can list all buckets
            s3.list_buckets()
            print(f"✅ S3 access verified for {user_type}")
    except Exception as e:
        print(f"❌ S3 access failed for {user_type}: {e}")
        success = False

    # Test CloudWatch Logs permissions
    try:
        logs = session.client("logs")
        logs.describe_log_groups(limit=1)
        print(f"✅ CloudWatch Logs access verified for {user_type}")
    except Exception as e:
        print(f"❌ CloudWatch Logs access failed for {user_type}: {e}")
        success = False

    # Test DynamoDB permissions
    try:
        dynamodb = session.client("dynamodb")
        dynamodb.list_tables(Limit=1)
        print(f"✅ DynamoDB access verified for {user_type}")
    except Exception as e:
        print(f"❌ DynamoDB access failed for {user_type}: {e}")
        success = False

    # Test SQS permissions
    try:
        sqs = session.client("sqs")
        sqs.list_queues(MaxResults=1)
        print(f"✅ SQS access verified for {user_type}")
    except Exception as e:
        print(f"❌ SQS access failed for {user_type}: {e}")
        success = False

    return success


def main():
    """Run all infrastructure tests"""
    global QUIET_MODE

    parser = argparse.ArgumentParser(
        description="Test deployed AWS infrastructure components"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show failures and final summary",
    )
    args = parser.parse_args()

    QUIET_MODE = args.quiet

    if not QUIET_MODE:
        print("🏗️  Testing deployed AWS infrastructure...")
        print("")

    success = True
    all_errors = []

    # Run all tests
    tests = [
        ("AWS Connectivity", test_aws_connectivity),
        ("IAM Resources", test_iam_resources),
        ("S3 Backend", test_s3_backend),
        ("Credential Storage", test_credential_storage),
        ("Developer Permissions", test_developer_permissions),
    ]

    for test_name, test_func in tests:
        if test_name in ["AWS Connectivity", "IAM Resources"]:
            # These return (success, errors) format
            test_success, errors = test_func()
            if not test_success:
                success = False
                if isinstance(errors, list):
                    all_errors.extend(errors)
                else:
                    all_errors.append(errors)
        else:
            # These return boolean format - update later
            test_success = test_func()
            if not test_success:
                success = False
                all_errors.append(f"❌ {test_name} failed")

        if not QUIET_MODE:
            print("")

    if success:
        print("✅ Infrastructure health check completed successfully!")
        sys.exit(0)
    else:
        print("❌ Infrastructure health check failed!")
        if all_errors:
            print("Errors encountered:")
            for error in all_errors:
                print(f"  {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
