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

# Data sources for account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Extended bootstrap policy for Route 53 and KMS operations
resource "aws_iam_policy" "bootstrap_extended_policy" {
  name        = "BootstrapExtendedPolicy"
  description = "Extended policy for bootstrap user to deploy Route 53 and KMS infrastructure"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Route53Permissions"
        Effect = "Allow"
        Action = [
          "route53:CreateHostedZone",
          "route53:DeleteHostedZone",
          "route53:GetHostedZone",
          "route53:ListHostedZones",
          "route53:ChangeResourceRecordSets",
          "route53:GetChange",
          "route53:ListResourceRecordSets",
          "route53:CreateKeySigningKey",
          "route53:DeleteKeySigningKey",
          "route53:ActivateKeySigningKey",
          "route53:DeactivateKeySigningKey",
          "route53:EnableHostedZoneDNSSEC",
          "route53:DisableHostedZoneDNSSEC",
          "route53:GetDNSSEC",
          "route53:CreateQueryLoggingConfig",
          "route53:DeleteQueryLoggingConfig",
          "route53:GetQueryLoggingConfig",
          "route53:ChangeTagsForResource",
          "route53:ListTagsForResource"
        ]
        Resource = "*"
      },
      {
        Sid    = "KMSPermissions"
        Effect = "Allow"
        Action = [
          "kms:CreateKey",
          "kms:DeleteKey",
          "kms:DescribeKey",
          "kms:GetKeyPolicy",
          "kms:PutKeyPolicy",
          "kms:GetPublicKey",
          "kms:Sign",
          "kms:TagResource",
          "kms:UntagResource",
          "kms:CreateAlias",
          "kms:DeleteAlias",
          "kms:ListAliases",
          "kms:ListKeys",
          "kms:EnableKeyRotation",
          "kms:DisableKeyRotation",
          "kms:GetKeyRotationStatus",
          "kms:ListResourceTags",
          "kms:ScheduleKeyDeletion",
          "kms:CancelKeyDeletion"
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogsPermissions"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:PutRetentionPolicy",
          "logs:TagLogGroup",
          "logs:UntagLogGroup"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "bootstrap-extended-policy"
    Project     = local.project_name
    Environment = local.environment
    Purpose     = "Extended bootstrap permissions for infrastructure deployment"
  }
}

# Attach the extended policy to the bootstrap user
resource "aws_iam_user_policy_attachment" "bootstrap_extended_policy" {
  user       = data.aws_iam_user.bootstrap_user.user_name
  policy_arn = aws_iam_policy.bootstrap_extended_policy.arn
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

          # Route 53 DNS management
          "route53:*",
          "route53:GetDNSSEC",
          "route53:EnableHostedZoneDNSSEC",
          "route53:DisableHostedZoneDNSSEC",

          # KMS key management
          "kms:*",

          # Monitoring and debugging
          "cloudwatch:*",
          "xray:*",

          # Security and compliance
          "iam:Get*",
          "iam:List*",
          "iam:CreatePolicy",
          "iam:AttachUserPolicy",
          "iam:DetachUserPolicy",
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
        Sid    = "ACMCertificatePermissions"
        Effect = "Allow"
        Action = [
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "acm:RequestCertificate",
          "acm:DeleteCertificate",
          "acm:AddTagsToCertificate",
          "acm:RemoveTagsFromCertificate"
        ]
        Resource = "*"
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
          "sqs:SetQueueAttributes",
          "sqs:ListQueues",
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:PurgeQueue"
        ]
        Resource = "*"
      },
      {
        Sid    = "Route53DNSPermissions"
        Effect = "Allow"
        Action = [
          "route53:ListHostedZones",
          "route53:ListHostedZonesByName",
          "route53:GetHostedZone",
          "route53:ListResourceRecordSets",
          "route53:GetChange",
          "route53:ChangeResourceRecordSets"
        ]
        Resource = "*"
      },
      {
        Sid    = "Route53RecordManagement"
        Effect = "Allow"
        Action = [
          "route53:ChangeResourceRecordSets"
        ]
        Resource = "arn:aws:route53:::hostedzone/*"
        Condition = {
          "ForAllValues:StringLike" = {
            "route53:RRType" = [
              "A",
              "AAAA",
              "CNAME",
              "TXT",
              "MX",
              "SRV"
            ]
          }
          "ForAnyValue:StringLike" = {
            "route53:RRName" = [
              "*.apps.cvideo.click",
              "apps.cvideo.click"
            ]
          }
        }
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

# Attach comprehensive policies for serverless development
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

# Additional serverless development policies to match developer-user capabilities
resource "aws_iam_role_policy_attachment" "developer_role_dynamodb_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "developer_role_sqs_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

resource "aws_iam_role_policy_attachment" "developer_role_cloudwatch_logs_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role_policy_attachment" "developer_role_apigateway_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator"
}

resource "aws_iam_role_policy_attachment" "developer_role_cloudformation_access" {
  role       = aws_iam_role.developer_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess"
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

# Route 53 hosted zone for apps.cvideo.click subdomain
resource "aws_route53_zone" "apps_subdomain" {
  name    = "apps.cvideo.click"
  comment = "Hosted zone for applications under cvideo.click domain"

  tags = {
    Name        = "apps.cvideo.click"
    Project     = local.project_name
    Environment = local.environment
    Purpose     = "Application subdomain DNS management"
  }
}

# Enable DNSSEC signing for the hosted zone
resource "aws_route53_key_signing_key" "apps_subdomain_ksk" {
  hosted_zone_id             = aws_route53_zone.apps_subdomain.id
  key_management_service_arn = aws_kms_key.dnssec_key.arn
  name                       = "apps_subdomain_ksk"
}

resource "aws_route53_hosted_zone_dnssec" "apps_subdomain_dnssec" {
  depends_on     = [aws_route53_key_signing_key.apps_subdomain_ksk]
  hosted_zone_id = aws_route53_zone.apps_subdomain.id
}

# KMS key for DNSSEC signing
resource "aws_kms_key" "dnssec_key" {
  description              = "KMS key for Route 53 DNSSEC signing"
  customer_master_key_spec = "ECC_NIST_P256"
  key_usage                = "SIGN_VERIFY"
  deletion_window_in_days  = 7

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/bootstrap-user"
          ]
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Route53 DNSSEC Service"
        Effect = "Allow"
        Principal = {
          Service = "dnssec-route53.amazonaws.com"
        }
        Action = [
          "kms:DescribeKey",
          "kms:GetPublicKey",
          "kms:Sign"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = {
    Name        = "apps.cvideo.click-dnssec-key"
    Project     = local.project_name
    Environment = local.environment
    Purpose     = "Route 53 DNSSEC signing"
  }
}

resource "aws_kms_alias" "dnssec_key_alias" {
  name          = "alias/${local.project_name}-dnssec-key"
  target_key_id = aws_kms_key.dnssec_key.key_id
}

# KMS key for CloudWatch log encryption
resource "aws_kms_key" "cloudwatch_logs_key" {
  description             = "KMS key for CloudWatch log encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/route53/${aws_route53_zone.apps_subdomain.name}"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "apps.cvideo.click-logs-key"
    Project     = local.project_name
    Environment = local.environment
    Purpose     = "CloudWatch logs encryption"
  }
}

resource "aws_kms_alias" "cloudwatch_logs_key_alias" {
  name          = "alias/${local.project_name}-logs-key"
  target_key_id = aws_kms_key.cloudwatch_logs_key.key_id
}

# CloudWatch Log Group for DNS query logging
resource "aws_cloudwatch_log_group" "route53_query_logs" {
  name              = "/aws/route53/${aws_route53_zone.apps_subdomain.name}"
  retention_in_days = 365 # 1 year retention for security compliance
  kms_key_id        = aws_kms_key.cloudwatch_logs_key.arn

  tags = {
    Name        = "apps.cvideo.click-dns-logs"
    Project     = local.project_name
    Environment = local.environment
    Purpose     = "Route 53 DNS query logging"
  }
}

# CloudWatch log group resource policy for Route 53 query logging
resource "aws_cloudwatch_log_resource_policy" "route53_query_log_policy" {
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "route53.amazonaws.com"
        }
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.route53_query_logs.arn}:*"
        Condition = {
          ArnLike = {
            "aws:SourceArn" = "arn:aws:route53:::hostedzone/${aws_route53_zone.apps_subdomain.zone_id}"
          }
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
  policy_name = "route53-query-logging-policy"
}

# Route 53 query logging configuration
resource "aws_route53_query_log" "apps_subdomain_query_log" {
  depends_on               = [aws_cloudwatch_log_group.route53_query_logs, aws_cloudwatch_log_resource_policy.route53_query_log_policy]
  cloudwatch_log_group_arn = aws_cloudwatch_log_group.route53_query_logs.arn
  zone_id                  = aws_route53_zone.apps_subdomain.zone_id
}

# NOTE: Parent domain NS record delegation commented out - requires manual setup
# After deployment, add NS records to cvideo.click pointing to apps.cvideo.click nameservers

# Data source for the parent domain (cvideo.click)
# data "aws_route53_zone" "parent_domain" {
#   name         = "cvideo.click"
#   private_zone = false
# }

# Create NS record in parent domain for the subdomain delegation
# resource "aws_route53_record" "apps_subdomain_ns" {
#   zone_id = data.aws_route53_zone.parent_domain.zone_id
#   name    = "apps.cvideo.click"
#   type    = "NS"
#   ttl     = 300
#
#   records = aws_route53_zone.apps_subdomain.name_servers
#
#   depends_on = [aws_route53_zone.apps_subdomain]
# }

# Output the nameservers for the apps.cvideo.click hosted zone
output "apps_subdomain_nameservers" {
  value       = aws_route53_zone.apps_subdomain.name_servers
  description = "Nameservers for apps.cvideo.click - add these as NS records in your parent domain"
}

# Output the hosted zone ID for reference
output "apps_subdomain_zone_id" {
  value       = aws_route53_zone.apps_subdomain.zone_id
  description = "Route 53 hosted zone ID for apps.cvideo.click"
}

# Output DNSSEC status and key information
output "apps_subdomain_dnssec_status" {
  value       = aws_route53_hosted_zone_dnssec.apps_subdomain_dnssec.signing_status
  description = "DNSSEC signing status for apps.cvideo.click hosted zone"
}

output "apps_subdomain_kms_key_id" {
  value       = aws_kms_key.dnssec_key.key_id
  description = "KMS key ID used for DNSSEC signing"
}

# Output query logging configuration
output "apps_subdomain_query_log_group" {
  value       = aws_cloudwatch_log_group.route53_query_logs.name
  description = "CloudWatch log group for DNS query logging"
}