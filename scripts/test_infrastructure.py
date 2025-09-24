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


def test_developer_permissions():
    """Test comprehensive developer user permissions for serverless development"""
    print("🔍 Testing developer user comprehensive permissions...")
    
    # Get developer credentials from terraform outputs
    try:
        import subprocess
        result = subprocess.run(
            ["terraform", "output", "-json"], 
            capture_output=True, 
            text=True, 
            cwd="."
        )
        if result.returncode != 0:
            print("⚠️  Could not get terraform outputs - testing with current credentials")
            return test_current_user_permissions()
        
        import json
        outputs = json.loads(result.stdout)
        dev_access_key = outputs.get("developer_user_access_key", {}).get("value")
        dev_secret_key = outputs.get("developer_user_secret_key", {}).get("value")
        
        if not dev_access_key or not dev_secret_key:
            print("⚠️  Could not get developer credentials - testing with current credentials")
            return test_current_user_permissions()
        
        # Test with developer credentials
        session = boto3.Session(
            aws_access_key_id=dev_access_key,
            aws_secret_access_key=dev_secret_key,
            region_name="us-east-1"
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
    
    # Test S3 permissions
    try:
        s3 = session.client("s3")
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
    
    return success


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
        test_developer_permissions,
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
