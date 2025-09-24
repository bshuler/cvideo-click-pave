# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Terraform infrastructure project that provisions AWS IAM resources for a development environment. The infrastructure is designed to support a development workflow with proper role-based access control, including:

- Admin IAM user with full AWS access
- Developer role with limited permissions (S3, Lambda, EC2)
- CI/CD role for GitHub Actions with OIDC authentication
- S3 backend for Terraform state management

## Common Development Commands

### Primary Workflow (via Makefile)

```bash
# Get help and see all available commands
make help

# One-time bootstrap setup (requires root credentials)
make bootstrap-create

# Initialize environment
make init

# Plan changes (dry run)
make plan

# Deploy infrastructure
make apply

# Generate credentials
make credentials

# Run validation and tests
make validate
make test

# Clean up everything (destructive!)
make clean
```

### Direct Terraform Commands (if needed)

```bash
# Initialize Terraform (first time setup)
terraform init

# Validate configuration
terraform validate

# Plan changes (dry run)
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show
```

### State Management

```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_iam_user.admin_user

# Pull remote state
terraform state pull
```

### Output Values

```bash
# Show all outputs
terraform output

# Show specific sensitive output
terraform output admin_user_access_key
terraform output admin_user_secret_key
terraform output cicd_role_arn
```

## Architecture Overview

### Infrastructure Components

**State Backend**: Uses S3 bucket `pave-tf-state-bucket` in `us-east-1` for storing Terraform state with versioning enabled.

**IAM Structure**:

- **Admin User** (`admin-user`): Full AWS administrative access with programmatic access keys
- **Developer Role** (`DeveloperRole`): Assumable by admin user with permissions for S3, Lambda, and EC2
- **CI/CD Role** (`CICDDeploymentRole`): For GitHub Actions using OIDC, with deployment permissions

**Security Features**:

- OIDC provider for GitHub Actions authentication
- Role-based access with least privilege principles
- Sensitive outputs for access keys
- Bucket-specific policies for CI/CD operations

### Configuration Details

- **AWS Region**: `us-east-1` (configurable in provider block)
- **GitHub OIDC**: Configured for repository `your-org/your-repo:ref:refs/heads/main` (needs customization)
- **S3 Bucket**: `your-app-bucket` referenced in CI/CD policies (needs customization)

## Key Customization Requirements

Before deploying, update these placeholders:

1. Line 115: Replace `your-org/your-repo` with actual GitHub organization/repository
2. Lines 148-149: Replace `your-app-bucket` with actual application S3 bucket name

## Security Considerations

- Admin user access keys are marked as sensitive outputs
- MFA should be manually enabled for admin user in AWS Console
- CI/CD role is restricted to specific GitHub repository and branch
- Developer role requires assumption by admin user for access

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (v1.0+)
- S3 bucket for state storage (created automatically by this configuration)
- GitHub repository for CI/CD integration
