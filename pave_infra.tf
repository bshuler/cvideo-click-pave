# Configure the AWS provider
provider "aws" {
  region = "us-east-1" # Adjust to your preferred region
  # AWS credentials will be read from environment variables:
  # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
}

# Use S3 remote backend for shared state across all deployment methods  
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    bucket = "pave-tf-state-bucket-us-east-1"
    key    = "pave/terraform.tfstate"
    region = "us-east-1"
    # Shared state across local terraform, Act, and GitHub Actions
  }
}

# Local variables for consistent naming
locals {
  project_name = "cvideo-click-pave"
  environment  = "main"
}

# Reference existing S3 bucket created by bootstrap process
data "aws_s3_bucket" "tf_state_bucket" {
  bucket = "pave-tf-state-bucket-us-east-1"
}

# Data source to verify bootstrap user exists (fails if not found)
data "aws_iam_user" "bootstrap_user" {
  user_name = "bootstrap-user"
}

# Custom policy for admin user - excludes bootstrap resource management
resource "aws_iam_policy" "admin_policy" {
  name        = "PaveAdminPolicy"
  description = "Administrative access for infrastructure management with least privilege principles"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # Infrastructure management
          "cloudformation:*",
          "lambda:*",
          "apigateway:*",
          "s3:*",
          "logs:*",
          "dynamodb:*",
          "ec2:*",

          # Monitoring and debugging
          "cloudwatch:*",
          "xray:*",

          # Security and compliance (read-only)
          "iam:Get*",
          "iam:List*",
          "sts:AssumeRole",
          "sts:GetCallerIdentity",

          # Cost management
          "ce:*",
          "budgets:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Deny"
        Action = [
          # Prevent bootstrap user modifications
          "iam:DeleteUser",
          "iam:DeleteRole",
          "iam:DeleteUserPolicy",
          "iam:DeleteRolePolicy",
          "iam:DetachUserPolicy",
          "iam:DetachRolePolicy",
          "iam:PutUserPolicy",
          "iam:PutRolePolicy",
          "iam:AttachUserPolicy",
          "iam:AttachRolePolicy"
        ]
        Resource = [
          "arn:aws:iam::*:user/bootstrap-user",
          "arn:aws:iam::*:role/bootstrap-*"
        ]
      }
    ]
  })
}

# 1. Create an admin IAM user (managed by bootstrap user)
resource "aws_iam_user" "admin_user" {
  name = "admin-user"
  path = "/"
}

resource "aws_iam_user_policy_attachment" "admin_user_policy" {
  user       = aws_iam_user.admin_user.name
  policy_arn = aws_iam_policy.admin_policy.arn
}

# Note: Enable MFA for admin-user manually in the AWS Console (IAM > Users > admin-user > Security credentials).

# Create an access key for the admin user (for CLI or programmatic access)
resource "aws_iam_access_key" "admin_user_key" {
  user = aws_iam_user.admin_user.name
}

# 2. Create a developer IAM user for application development
resource "aws_iam_user" "developer_user" {
  name = "developer-user"
  path = "/"
}

# Comprehensive developer policy for serverless application development with constrained permissions
resource "aws_iam_user_policy" "developer_comprehensive_policy" {
  name = "DeveloperComprehensivePolicy"
  user = aws_iam_user.developer_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudFormationPermissions"
        Effect = "Allow"
        Action = [
          "cloudformation:CreateStack",
          "cloudformation:UpdateStack",
          "cloudformation:DeleteStack",
          "cloudformation:DescribeStacks",
          "cloudformation:DescribeStackEvents",
          "cloudformation:DescribeStackResources",
          "cloudformation:GetTemplate",
          "cloudformation:ListStacks",
          "cloudformation:ListStackResources",
          "cloudformation:CreateChangeSet",
          "cloudformation:DeleteChangeSet",
          "cloudformation:DescribeChangeSet",
          "cloudformation:ExecuteChangeSet",
          "cloudformation:CancelUpdateStack",
          "cloudformation:ContinueUpdateRollback",
          "cloudformation:ValidateTemplate",
          "cloudformation:GetTemplateSummary"
        ]
        Resource = "*"
      },
      {
        Sid    = "LambdaPermissions"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:ListFunctions",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:InvokeFunction",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:GetPolicy",
          "lambda:PutFunctionConcurrency",
          "lambda:DeleteFunctionConcurrency",
          "lambda:TagResource",
          "lambda:UntagResource"
        ]
        Resource = "*"
      },
      {
        Sid    = "APIGatewayPermissions"
        Effect = "Allow"
        Action = [
          "apigateway:GET",
          "apigateway:POST",
          "apigateway:PUT",
          "apigateway:DELETE",
          "apigateway:PATCH"
        ]
        Resource = "*"
      }
    ]
  })
}

# Extended developer policy for additional permissions
resource "aws_iam_policy" "developer_extended_policy" {
  name        = "DeveloperExtendedPolicy"
  description = "Extended permissions for developer user - S3, IAM, logs, and state management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketPermissions"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:GetBucketAcl",
          "s3:PutBucketAcl",
          "s3:GetBucketCORS",
          "s3:PutBucketCORS",
          "s3:GetBucketWebsite",
          "s3:PutBucketWebsite",
          "s3:DeleteBucketWebsite",
          "s3:GetBucketNotification",
          "s3:PutBucketNotification",
          "s3:GetBucketTagging",
          "s3:PutBucketTagging",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectVersion",
          "s3:DeleteObjectVersion"
        ]
        Resource = [
          "arn:aws:s3:::aws-sam-cli-managed-*",
          "arn:aws:s3:::aws-sam-cli-managed-*/*",
          "arn:aws:s3:::cvideo-*",
          "arn:aws:s3:::cvideo-*/*",
          "arn:aws:s3:::${local.project_name}-*",
          "arn:aws:s3:::${local.project_name}-*/*"
        ]
      },
      {
        Sid    = "IAMRolePermissions"
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:PassRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:TagRole",
          "iam:UntagRole"
        ]
        Resource = [
          "arn:aws:iam::*:role/cvideo-click-api-*",
          "arn:aws:iam::*:role/aws-sam-cli-managed-*"
        ]
      },
      {
        Sid    = "CloudWatchLogsPermissions"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:DeleteLogGroup",
          "logs:DeleteLogStream",
          "logs:PutRetentionPolicy",
          "logs:TagLogGroup",
          "logs:UntagLogGroup"
        ]
        Resource = "*"
      },
      {
        Sid    = "TerraformStatePermissions"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::pave-tf-state-bucket-us-east-1",
          "arn:aws:s3:::pave-tf-state-bucket-us-east-1/*"
        ]
      },
      {
        Sid    = "TerraformLockPermissions"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:us-east-1:*:table/terraform-locks"
      },
      {
        Sid    = "DynamoDBPermissions"
        Effect = "Allow"
        Action = [
          "dynamodb:*"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMReadPermissions"
        Effect = "Allow"
        Action = [
          "iam:Get*",
          "iam:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMPolicyManagement"
        Effect = "Allow"
        Action = [
          "iam:CreatePolicy",
          "iam:GetPolicy",
          "iam:ListPolicies",
          "iam:GetPolicyVersion",
          "iam:ListPolicyVersions"
        ]
        Resource = "arn:aws:iam::*:policy/${local.project_name}-*"
      },
      {
        Sid    = "SQSPermissions"
        Effect = "Allow"
        Action = [
          "sqs:CreateQueue",
          "sqs:DeleteQueue",
          "sqs:GetQueueAttributes",
          "sqs:SetQueueAttributes"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the extended policy to the developer user
resource "aws_iam_user_policy_attachment" "developer_extended_policy" {
  user       = aws_iam_user.developer_user.name
  policy_arn = aws_iam_policy.developer_extended_policy.arn
}

# Keep EC2 read-only access for viewing instances
resource "aws_iam_user_policy_attachment" "developer_ec2_policy" {
  user       = aws_iam_user.developer_user.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

# Create access keys for the developer user
resource "aws_iam_access_key" "developer_user_key" {
  user = aws_iam_user.developer_user.name
}

# Output the admin user access key (sensitive, handle securely)
output "admin_user_access_key" {
  value     = aws_iam_access_key.admin_user_key.id
  sensitive = true
}

output "admin_user_secret_key" {
  value     = aws_iam_access_key.admin_user_key.secret
  sensitive = true
}

# Output the developer user credentials (for use in next code repo)
output "developer_user_access_key" {
  value       = aws_iam_access_key.developer_user_key.id
  sensitive   = true
  description = "Access key for developer user - use this in your application development"
}

output "developer_user_secret_key" {
  value       = aws_iam_access_key.developer_user_key.secret
  sensitive   = true
  description = "Secret key for developer user - use this in your application development"
}

# 2. Create a developer IAM role for app development
resource "aws_iam_role" "developer_role" {
  name = "DeveloperRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_user.admin_user.arn # Allow admin user to assume this role
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Attach policies for S3, Lambda, and EC2
resource "aws_iam_role_policy_attachment" "developer_s3_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "developer_lambda_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}

resource "aws_iam_role_policy_attachment" "developer_ec2_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

# 3. Use existing OIDC provider for GitHub Actions (commented out since it already exists)
# resource "aws_iam_openid_connect_provider" "github_oidc" {
#   url = "https://token.actions.githubusercontent.com"
#   client_id_list = [
#     "sts.amazonaws.com"
#   ]
#   thumbprint_list = [
#     "6938fd4d98bab03faadb97b34396831e3780aea1" # Verify from GitHub docs
#   ]
# }

# Reference existing OIDC provider
data "aws_iam_openid_connect_provider" "github_oidc" {
  url = "https://token.actions.githubusercontent.com"
}

# Create a CI/CD role for GitHub Actions
resource "aws_iam_role" "cicd_role" {
  name = "CICDDeploymentRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github_oidc.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:bshuler/cvideo-click-pave:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

# Attach policies for CI/CD (S3 and Lambda for deployment)
resource "aws_iam_role_policy_attachment" "cicd_s3_access" {
  role       = aws_iam_role.cicd_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cicd_lambda_access" {
  role       = aws_iam_role.cicd_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}

# Custom policy for specific S3 bucket access
resource "aws_iam_policy" "cicd_s3_specific" {
  name = "CICDS3SpecificAccess"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::cvideo-click-app-bucket/*", # Replace with your app bucket
          "arn:aws:s3:::cvideo-click-app-bucket"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cicd_s3_specific_access" {
  role       = aws_iam_role.cicd_role.name
  policy_arn = aws_iam_policy.cicd_s3_specific.arn
}

# Output the CI/CD role ARN for GitHub Actions
output "cicd_role_arn" {
  value = aws_iam_role.cicd_role.arn
}