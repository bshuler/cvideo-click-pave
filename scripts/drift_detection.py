#!/usr/bin/env python3
"""
AWS-to-Terraform Drift Detection Script

This script compares the actual AWS IAM state with Terraform configuration
to detect any drift or inconsistencies that require attention.
"""

import boto3
import sys
import logging
from typing import Dict, List, Tuple, Any
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}📋 {title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * (len(title) + 4)}{Colors.END}")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.WHITE}ℹ️  {message}{Colors.END}")


class DriftDetector:
    """Main class for detecting drift between AWS and Terraform"""

    def __init__(self):
        try:
            self.iam = boto3.client("iam")
            self.sts = boto3.client("sts")
            # Test credentials
            identity = self.sts.get_caller_identity()
            print_info(f"Connected as: {identity['Arn']}")
        except NoCredentialsError:
            print_error("No AWS credentials found. Please configure credentials.")
            sys.exit(1)
        except ClientError as e:
            print_error(f"Failed to connect to AWS: {e}")
            sys.exit(1)

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get comprehensive information about a user"""
        try:
            user_info = {
                "exists": True,
                "attached_policies": [],
                "inline_policies": [],
                "groups": [],
            }

            # Get attached policies
            response = self.iam.list_attached_user_policies(UserName=username)
            user_info["attached_policies"] = [
                {"name": p["PolicyName"], "arn": p["PolicyArn"]}
                for p in response["AttachedPolicies"]
            ]

            # Get inline policies
            response = self.iam.list_user_policies(UserName=username)
            user_info["inline_policies"] = response["PolicyNames"]

            # Get groups
            response = self.iam.list_groups_for_user(UserName=username)
            user_info["groups"] = [g["GroupName"] for g in response["Groups"]]

            return user_info

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchEntity":
                return {"exists": False}
            else:
                print_error(f"Error getting user info for {username}: {e}")
                return {"exists": False}

    def get_role_info(self, rolename: str) -> Dict[str, Any]:
        """Get comprehensive information about a role"""
        try:
            role_info = {
                "exists": True,
                "attached_policies": [],
                "inline_policies": [],
                "assume_role_policy": None,
            }

            # Get role details
            response = self.iam.get_role(RoleName=rolename)
            role_info["assume_role_policy"] = response["Role"][
                "AssumeRolePolicyDocument"
            ]

            # Get attached policies
            response = self.iam.list_attached_role_policies(RoleName=rolename)
            role_info["attached_policies"] = [
                {"name": p["PolicyName"], "arn": p["PolicyArn"]}
                for p in response["AttachedPolicies"]
            ]

            # Get inline policies
            response = self.iam.list_role_policies(RoleName=rolename)
            role_info["inline_policies"] = response["PolicyNames"]

            return role_info

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchEntity":
                return {"exists": False}
            else:
                print_error(f"Error getting role info for {rolename}: {e}")
                return {"exists": False}

    def compare_policies(
        self,
        aws_policies: List[Dict[str, str]],
        expected_policies: List[str],
        resource_name: str,
    ) -> Tuple[bool, List[str]]:
        """Compare AWS policies with expected policies"""
        aws_policy_names = {p["name"] for p in aws_policies}
        expected_policy_set = set(expected_policies)

        missing = expected_policy_set - aws_policy_names
        extra = aws_policy_names - expected_policy_set

        issues = []
        if missing:
            issues.append(f"Missing policies in {resource_name}: {', '.join(missing)}")
        if extra:
            issues.append(f"Extra policies in {resource_name}: {', '.join(extra)}")

        return len(issues) == 0, issues

    def compare_inline_policies(
        self, aws_inline: List[str], expected_inline: List[str], resource_name: str
    ) -> Tuple[bool, List[str]]:
        """Compare inline policies"""
        aws_set = set(aws_inline)
        expected_set = set(expected_inline)

        missing = expected_set - aws_set
        extra = aws_set - expected_set

        issues = []
        if missing:
            issues.append(
                f"Missing inline policies in {resource_name}: {', '.join(missing)}"
            )
        if extra:
            issues.append(
                f"Extra inline policies in {resource_name}: {', '.join(extra)}"
            )

        return len(issues) == 0, issues

    def check_developer_user(self) -> Tuple[bool, List[str]]:
        """Check developer-user against expected Terraform configuration"""
        print_section("Checking developer-user")

        user_info = self.get_user_info("developer-user")
        if not user_info["exists"]:
            return False, ["developer-user does not exist in AWS"]

        # Expected configuration based on Terraform
        expected_attached = ["DeveloperExtendedPolicy", "AmazonEC2ReadOnlyAccess"]
        expected_inline: List[str] = ["DeveloperComprehensivePolicy"]

        issues = []

        # Check attached policies
        match, policy_issues = self.compare_policies(
            user_info["attached_policies"],
            expected_attached,
            "developer-user attached policies",
        )
        if not match:
            issues.extend(policy_issues)

        # Check inline policies
        match, inline_issues = self.compare_inline_policies(
            user_info["inline_policies"],
            expected_inline,
            "developer-user inline policies",
        )
        if not match:
            issues.extend(inline_issues)

        # Check groups (should be empty)
        if user_info["groups"]:
            issues.append(
                f"developer-user has unexpected groups: {', '.join(user_info['groups'])}"
            )

        if not issues:
            print_success("developer-user configuration matches Terraform")
        else:
            for issue in issues:
                print_warning(issue)

        return len(issues) == 0, issues

    def check_admin_user(self) -> Tuple[bool, List[str]]:
        """Check admin-user against expected Terraform configuration"""
        print_section("Checking admin-user")

        user_info = self.get_user_info("admin-user")
        if not user_info["exists"]:
            return False, ["admin-user does not exist in AWS"]

        # Expected configuration based on Terraform
        expected_attached = ["PaveAdminPolicy"]
        expected_inline: List[str] = []

        issues = []

        # Check attached policies
        match, policy_issues = self.compare_policies(
            user_info["attached_policies"],
            expected_attached,
            "admin-user attached policies",
        )
        if not match:
            issues.extend(policy_issues)

        # Check inline policies
        match, inline_issues = self.compare_inline_policies(
            user_info["inline_policies"], expected_inline, "admin-user inline policies"
        )
        if not match:
            issues.extend(inline_issues)

        # Check groups (should be empty)
        if user_info["groups"]:
            issues.append(
                f"admin-user has unexpected groups: {', '.join(user_info['groups'])}"
            )

        if not issues:
            print_success("admin-user configuration matches Terraform")
        else:
            for issue in issues:
                print_warning(issue)

        return len(issues) == 0, issues

    def check_developer_role(self) -> Tuple[bool, List[str]]:
        """Check DeveloperRole against expected Terraform configuration"""
        print_section("Checking DeveloperRole")

        role_info = self.get_role_info("DeveloperRole")
        if not role_info["exists"]:
            return False, ["DeveloperRole does not exist in AWS"]

        # Expected configuration based on Terraform
        expected_attached = [
            "AmazonAPIGatewayAdministrator",
            "AmazonEC2FullAccess",
            "CloudWatchLogsFullAccess",
            "AmazonSQSFullAccess",
            "AmazonDynamoDBFullAccess",
            "AmazonS3FullAccess",
            "AWSCloudFormationFullAccess",
            "AWSLambda_FullAccess",
        ]
        expected_inline: List[str] = []

        issues = []

        # Check attached policies
        match, policy_issues = self.compare_policies(
            role_info["attached_policies"],
            expected_attached,
            "DeveloperRole attached policies",
        )
        if not match:
            issues.extend(policy_issues)

        # Check inline policies
        match, inline_issues = self.compare_inline_policies(
            role_info["inline_policies"],
            expected_inline,
            "DeveloperRole inline policies",
        )
        if not match:
            issues.extend(inline_issues)

        # Check assume role policy (should allow admin-user)
        assume_policy = role_info["assume_role_policy"]
        admin_user_arn = "arn:aws:iam::256140316797:user/admin-user"

        can_assume = False
        for statement in assume_policy.get("Statement", []):
            principal = statement.get("Principal", {})
            if isinstance(principal, dict) and "AWS" in principal:
                aws_principals = principal["AWS"]
                if isinstance(aws_principals, str):
                    aws_principals = [aws_principals]
                if admin_user_arn in aws_principals:
                    can_assume = True
                    break

        if not can_assume:
            issues.append("DeveloperRole cannot be assumed by admin-user")

        if not issues:
            print_success("DeveloperRole configuration matches Terraform")
        else:
            for issue in issues:
                print_warning(issue)

        return len(issues) == 0, issues

    def check_cicd_role(self) -> Tuple[bool, List[str]]:
        """Check CICDDeploymentRole against expected Terraform configuration"""
        print_section("Checking CICDDeploymentRole")

        role_info = self.get_role_info("CICDDeploymentRole")
        if not role_info["exists"]:
            return False, ["CICDDeploymentRole does not exist in AWS"]

        # Expected configuration based on Terraform
        expected_attached = [
            "CICDS3SpecificAccess",
            "AmazonS3FullAccess",
            "AWSLambda_FullAccess",
        ]
        expected_inline: List[str] = []

        issues = []

        # Check attached policies
        match, policy_issues = self.compare_policies(
            role_info["attached_policies"],
            expected_attached,
            "CICDDeploymentRole attached policies",
        )
        if not match:
            issues.extend(policy_issues)

        # Check inline policies
        match, inline_issues = self.compare_inline_policies(
            role_info["inline_policies"],
            expected_inline,
            "CICDDeploymentRole inline policies",
        )
        if not match:
            issues.extend(inline_issues)

        # Check assume role policy (should allow GitHub OIDC)
        assume_policy = role_info["assume_role_policy"]
        expected_federated = "arn:aws:iam::256140316797:oidc-provider/token.actions.githubusercontent.com"

        can_assume = False
        for statement in assume_policy.get("Statement", []):
            principal = statement.get("Principal", {})
            if isinstance(principal, dict) and "Federated" in principal:
                if principal["Federated"] == expected_federated:
                    can_assume = True
                    break

        if not can_assume:
            issues.append("CICDDeploymentRole cannot be assumed by GitHub Actions OIDC")

        if not issues:
            print_success("CICDDeploymentRole configuration matches Terraform")
        else:
            for issue in issues:
                print_warning(issue)

        return len(issues) == 0, issues

    def run_full_drift_detection(self) -> bool:
        """Run complete drift detection"""
        print_header("AWS-to-Terraform Drift Detection")

        all_checks_passed = True
        all_issues = []

        # Check all resources
        checks = [
            ("developer-user", self.check_developer_user),
            ("admin-user", self.check_admin_user),
            ("DeveloperRole", self.check_developer_role),
            ("CICDDeploymentRole", self.check_cicd_role),
        ]

        for resource_name, check_func in checks:
            try:
                passed, issues = check_func()
                if not passed:
                    all_checks_passed = False
                    all_issues.extend(issues)
            except Exception as e:
                print_error(f"Error checking {resource_name}: {e}")
                all_checks_passed = False
                all_issues.append(f"Failed to check {resource_name}: {str(e)}")

        # Summary
        print_section("Drift Detection Summary")

        if all_checks_passed:
            print_success(
                "✅ NO DRIFT DETECTED - All AWS resources match Terraform configuration"
            )
            print_info("Your infrastructure is perfectly synchronized!")
        else:
            print_warning(f"⚠️  DRIFT DETECTED - {len(all_issues)} issue(s) found:")
            for i, issue in enumerate(all_issues, 1):
                print(f"   {i}. {issue}")
            print_info(
                "\nConsider running 'terraform plan' and 'terraform apply' to resolve drift."
            )

        return all_checks_passed


def main():
    """Main function"""
    detector = DriftDetector()
    success = detector.run_full_drift_detection()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
