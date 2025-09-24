# CVideo Click Pave - AWS Infrastructure as Code

## Project Overview

This repository contains Terraform infrastructure as code for AWS resource provisioning, specifically designed for the cvideo-click project. It creates the necessary AWS infrastructure including S3 buckets, IAM roles, users, and policies required for both development and CI/CD operations.

## ⚠️ PREREQUISITE: Bootstrap User Setup

**This repository requires a bootstrap user to be created by the AWS root account before any operations can be performed.**

### Root Account Setup Steps

**These steps must be completed by someone with AWS root account access:**

1. **Login to AWS Console with Root Account**
   
2. **Create Bootstrap User** (in IAM Console > Users):

   ```text
   User Name: pave-bootstrap-user
   Access type: Programmatic access
   ```

3. **Create Bootstrap Role** (in IAM Console > Roles):

   ```text
   Role Name: PaveBootstrapRole
   Trust relationship: Allow the bootstrap user to assume this role
   Permissions: AdministratorAccess (or custom policy with required permissions)
   ```

4. **Create Bootstrap Policy** (in IAM Console > Policies):

   ```text
   Policy Name: PaveBootstrapPolicy
   Permissions:
   - Full IAM access EXCEPT cannot delete pave-bootstrap-user or PaveBootstrapRole
   - Full S3 access
   - Full Lambda access  
   - Full EC2 access
   ```

5. **Attach Policy to Bootstrap User**:
   - Attach `PaveBootstrapPolicy` to `pave-bootstrap-user`

6. **Generate Access Keys**:
   - Create access key for `pave-bootstrap-user`
   - Save the Access Key ID and Secret Access Key securely

7. **Configure Repository Secrets**:
   - Set `AWS_ACCESS_KEY_ID` to bootstrap user's access key
   - Set `AWS_SECRET_ACCESS_KEY` to bootstrap user's secret key
   - Set `AWS_REGION` to your preferred region (e.g., `us-east-1`)

### Security Model

- **Bootstrap User**: Has administrative privileges, manages all pave infrastructure
- **Admin Users**: Created by pave, cannot delete bootstrap resources  
- **Developer Users**: Limited privileges for application development
- **CI/CD Roles**: Specific permissions for deployment automation

**The bootstrap user and role are never managed by Terraform and will never be deleted by cleanup operations.**

### Key Features

- **Unified Workflow**: Single GitHub Actions workflow that intelligently adapts to local (Act) and production (GitHub Actions) environments
- **Smart Authentication**: Uses access key authentication for both local and GitHub Actions (simplified approach)
- **Unique Resource Naming**: Uses random suffixes to prevent naming conflicts across deployments
- **Clean State Management**: Local testing includes destroy step for clean slate deployments
- **Comprehensive IAM**: Separate users and roles for admin, developers, and CI/CD with appropriate permissions
- **Credential Management**: Smart scripts for extracting and setting up credentials securely

### What This Repository Provisions

- **S3 Bucket**: Terraform state storage with versioning enabled
- **IAM Roles**:
  - `CICDDeploymentRole-{suffix}`: For GitHub Actions with S3/Lambda access
  - `DeveloperRole-{suffix}`: For development with EC2/S3/Lambda access
- **IAM Users**:
  - `admin-user-{suffix}`: Full administrative access with access keys
  - `developer-user-{suffix}`: Limited development access (S3, Lambda, EC2 read-only) with access keys
- **IAM Policies**: Custom S3-specific policies for granular access control

## Project Structure

```text
├── .github/workflows/
│   └── terraform.yaml         # Unified intelligent workflow
├── pave_infra.tf              # Main Terraform configuration
├── cleanup-all.sh             # Comprehensive resource cleanup script
├── extract-credentials.sh     # Legacy credential extraction (see get-credentials.sh)
├── get-credentials.sh         # Smart credential template generator
├── .secrets                   # Local AWS credentials (gitignored)
├── .actrc                     # Act configuration (secrets file, container settings)
├── .gitignore                 # Git ignore rules (includes credentials/)
├── credentials/               # Generated credentials directory (gitignored)
│   ├── admin.env             # Admin user credentials template
│   └── developer.env         # Developer user credentials template
├── GITHUB_SETUP.md            # GitHub repository secrets setup guide
├── WARP.md                    # Project documentation
└── README.md                  # This file
```
## 🎯 Purpose

This project provisions AWS infrastructure for:

- **Application deployment** via S3 and Lambda
- **Developer access** with appropriate IAM users and roles
- **CI/CD pipeline** integration with GitHub Actions
- **Terraform state management** with S3 backend
- **Security best practices** with access key authentication

## 🏗️ Infrastructure Components

### Core Resources

- **S3 Bucket**: Terraform state storage with versioning (`pave-tf-state-bucket-{region}-{suffix}`)
- **Admin User**: Full AWS administrator access (`admin-user-{suffix}`)
- **Developer User**: Limited access for application development (`developer-user-{suffix}`)
- **CI/CD Role**: GitHub Actions role with deployment permissions (`CICDDeploymentRole-{suffix}`)
- **Developer Role**: Role for developers to assume (`DeveloperRole-{suffix}`)

### IAM Policies & Permissions

- **Administrator Access**: Full AWS permissions for admin user
- **Developer Permissions**: S3 Full Access + Lambda Full Access + EC2 Read Only
- **CI/CD Permissions**: S3 Full Access + Lambda Full Access + Custom S3 bucket policies

### Unique Resource Naming

All resources use random suffixes (e.g., `ef47b899`) to prevent conflicts:
- Multiple deployments can coexist
- Clean separation between environments
- No naming collision issues

## 🚀 Getting Started

### Prerequisites

1. **AWS Account** with appropriate permissions to create IAM users, roles, and S3 buckets
2. **AWS CLI** configured with admin credentials
3. **Terraform** 1.5.6+ installed locally
4. **Docker** (for local testing with Act)
5. **GitHub CLI** (for GitHub Actions management)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bshuler/cvideo-click-pave.git
   cd cvideo-click-pave
   ```

2. **Install Act** (for local testing):
   ```bash
   # macOS
   brew install act
   
   # Other platforms: https://github.com/nektos/act#installation
   ```

3. **Install GitHub CLI** (for repository secrets):
   ```bash
   # macOS
   brew install gh
   
   # Other platforms: https://cli.github.com/manual/installation
   ```

## 💻 Primary Interface: Makefile

This repository uses a **Makefile as the primary interface** for all operations. The Makefile orchestrates Terraform and Python scripts to provide a unified experience.

### 🚀 Quick Start

```bash
# 1. Initialize environment and dependencies
make init

# 2. Validate configuration  
make validate

# 3. Deploy infrastructure
make apply

# 4. Generate credential templates
make credentials

# 5. View current status
make status
```

### 📋 All Available Commands

Run `make help` to see all available commands:

```bash
make help           # Show all available commands
make init           # Initialize terraform and install Python dependencies
make plan           # Run terraform plan to preview changes
make apply          # Deploy infrastructure with terraform apply
make destroy        # Destroy infrastructure with terraform destroy
make clean          # Comprehensive cleanup of all AWS resources (destructive!)
make credentials    # Generate credential template files
make setup-github   # Set up GitHub repository secrets
make dev-deploy     # Full local development deployment (clean slate)
make validate       # Validate terraform configuration and Python code
make status         # Show current infrastructure status
```

## 🛠️ Deployment Methods

The Makefile supports **multiple underlying deployment methods** while providing a consistent interface:

### 1. � Act (Local GitHub Actions Testing) - **Recommended for Development**

Act runs GitHub Actions workflows locally using Docker, providing the closest simulation to the production environment.

#### Setup Act Environment

1. **Configure AWS credentials** in `.secrets` file:
   ```bash
   # Create .secrets file (already configured in .actrc)
   cat > .secrets << EOF
   AWS_ACCESS_KEY_ID=your_admin_access_key_here
   AWS_SECRET_ACCESS_KEY=your_admin_secret_key_here  
   AWS_REGION=us-east-1
   EOF
   ```

2. **Run the workflow** (the `.actrc` file automatically loads secrets):
   ```bash
   # Complete infrastructure deployment (includes clean destroy first)
   act -W .github/workflows/terraform.yaml
   
   # With verbose output for debugging
   act -W .github/workflows/terraform.yaml --verbose
   
   # Specify specific job
   act -W .github/workflows/terraform.yaml --job terraform
   ```

#### What Act Does Differently

- ✅ **Clean slate testing**: Automatically runs `terraform destroy` before apply
- ✅ **Manual Terraform install**: Downloads and installs Terraform 1.5.6
- ✅ **Access key authentication**: Uses AWS credentials from secrets file
- ✅ **Debug output**: Shows file listings and environment details
- ✅ **Docker isolation**: Runs in consistent Ubuntu container environment

### 2. 🤖 GitHub Actions (Production CI/CD)

Automatic deployment triggered by pushes to main branch or manual workflow dispatch.

#### Setup GitHub Actions

1. **Configure repository secrets** using GitHub CLI:
   ```bash
   # Set the three required secrets (run these after infrastructure exists)
   gh secret set AWS_ACCESS_KEY_ID --body 'YOUR_BOOTSTRAP_ACCESS_KEY_ID'
   gh secret set AWS_SECRET_ACCESS_KEY --body 'YOUR_BOOTSTRAP_SECRET_ACCESS_KEY'  
   gh secret set AWS_REGION --body 'us-east-1'
   
   # Verify secrets are set
   gh secret list
   ```

   > **Note**: The credentials above are examples from our testing. Use your actual admin user credentials created by running the infrastructure once locally first.

2. **Trigger deployment**:
   ```bash
   # Automatic trigger - push to main
   git add .
   git commit -m "Deploy infrastructure"
   git push origin main
   
   # Manual trigger
   gh workflow run terraform.yaml
   ```

3. **Monitor workflow**:
   ```bash
   # Check workflow status
   gh run list --workflow="terraform.yaml" --limit 5
   
   # View specific run details
   gh run view <run-id>
   
   # View real-time logs
   gh run view --log <run-id>
   ```

#### What GitHub Actions Does

- ✅ **Production deployment**: Uses access key authentication
- ✅ **Automatic triggers**: Runs on push to main branch
- ✅ **Manual dispatch**: Can be triggered via CLI or GitHub web interface
- ✅ **Standard workflow**: Plan → Apply (no destroy step)
- ✅ **Terraform setup**: Uses HashiCorp's setup-terraform action

### 3. 🌐 Direct Git Push

The simplest method - just push code changes to trigger automatic deployment.

```bash
# Make infrastructure changes to pave_infra.tf
# Then commit and push
git add pave_infra.tf
git commit -m "Update infrastructure configuration"
git push origin main

# Monitor deployment
gh run list --workflow="terraform.yaml" --limit 3
```

### 4. 🔧 Direct Terraform (Traditional)

Standard Terraform workflow for direct infrastructure management.

#### Setup Local Terraform

1. **Configure AWS credentials**:
   ```bash
   # Option 1: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   
   # Option 2: AWS CLI profile
   aws configure --profile pave
   export AWS_PROFILE=pave
   ```

2. **Run Terraform commands**:
   ```bash
   # Initialize (first time)
   terraform init
   
   # Plan changes
   terraform plan
   
   # Apply infrastructure
   terraform apply
   
   # Destroy when needed
   terraform destroy
   ```

#### Terraform Command Reference

```bash
# View current state
terraform show
terraform state list

# Validate configuration
terraform validate
terraform fmt

# Target specific resources
terraform apply -target="aws_iam_user.admin_user"
terraform destroy -target="aws_s3_bucket.tf_state_bucket"

# Import existing resources
terraform import aws_iam_user.admin_user existing-user-name
```

## 🔐 Credential Management

After successful infrastructure deployment, you'll have two sets of user credentials plus roles.

### Extract Credentials

Use the Makefile credential management:

```bash
# Generate credential template files with AWS Console instructions
make credentials
```

This Python script:

- 🔍 Finds your deployed users automatically using boto3
- 📝 Creates secure template files (`credentials/admin.env`, `credentials/developer.env`)  
- 🔒 Sets proper file permissions (600)
- 📋 Provides step-by-step AWS Console instructions
- ⚠️ Handles the fact that access key secrets can't be retrieved after creation
- 🐍 Uses Python + boto3 instead of shell scripts

### Using Developer Credentials

The developer credentials are designed for your application repositories:

```bash
# Copy developer credentials to your app project
cp credentials/developer.env /path/to/your/app/.env

# View the template with instructions
cat credentials/developer.env
```

### Developer User Permissions

The developer user (`developer-user-{suffix}`) has these AWS permissions:
- ✅ **Amazon S3 Full Access**: Upload/download files, manage buckets for static websites
- ✅ **AWS Lambda Full Access**: Create and deploy serverless functions
- ✅ **Amazon EC2 Read Only Access**: View instances (helpful for debugging)

### Security Best Practices

- 🔒 All credential files are in `.gitignore` 
- 🔒 Files have restrictive permissions (600 - owner read/write only)
- 🔒 Use admin credentials **only** for infrastructure management
- 🔒 Use developer credentials for your application development
- ⚠️ Never commit credential files to version control
- 💡 Consider rotating access keys periodically

## 🧹 Resource Cleanup

### Comprehensive Cleanup

When you need to clean up **ALL** infrastructure resources (useful for testing or complete redeployment):

```bash
# WARNING: This removes ALL pave infrastructure resources
make clean
```

This Python script performs comprehensive cleanup:

- 🗑️ Removes all admin and developer users (all previous deployments)
- 🗑️ Deletes all CICD and developer IAM roles
- 🗑️ Removes all custom IAM policies  
- 🗑️ Empties and deletes all S3 buckets
- 🗑️ Cleans up local Terraform state files
- 📊 Provides detailed progress reporting
- 🐍 Uses Python + boto3 for robust error handling

### Selective Cleanup

For targeted cleanup:

```bash
# List current resources
aws iam list-users --query 'Users[?contains(UserName, `admin-user-`) || contains(UserName, `developer-user-`)].UserName' --output table

# Remove specific deployment
terraform destroy -target="aws_iam_user.admin_user" 
terraform destroy -target="aws_iam_user.developer_user"
```

## 🔄 CI/CD Pipeline Details

### Unified Workflow Intelligence

Our single `terraform.yaml` workflow automatically adapts to different environments:

| Environment | Detection | Authentication | Behavior |
|-------------|-----------|----------------|----------|
| **Local (Act)** | `${{ env.ACT }}` | AWS Access Keys | Destroy → Plan → Apply |
| **GitHub Actions** | `${{ !env.ACT }}` | AWS Access Keys | Plan → Apply |

### Workflow Triggers

```yaml
on:
  push:
    branches: [main]        # Automatic on push
  workflow_dispatch:        # Manual via GitHub CLI or web
```

### Pipeline Steps

1. **Environment Detection**: Automatically detects local vs GitHub execution
2. **AWS Authentication**: Uses access keys from secrets (simplified approach)
3. **Terraform Setup**: Downloads appropriate Terraform version
4. **Infrastructure Deployment**: Plan and apply changes
5. **State Management**: Uses S3 backend for state storage

### Monitoring Pipeline

```bash
# List recent workflow runs
gh run list --limit 10

# Watch running workflow
gh run view --log

# View workflow in browser
gh workflow view terraform.yaml --web
```

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 1. Access Key Issues
```bash
# Problem: Invalid AWS credentials
# Solution: Verify credentials
aws sts get-caller-identity

# Update secrets for GitHub Actions
gh secret set AWS_ACCESS_KEY_ID --body 'new_key'
```

#### 2. Resource Naming Conflicts
```bash
# Problem: Resources already exist
# Solution: Use cleanup script or check for existing resources
./cleanup-all.sh
aws iam list-users --query 'Users[?contains(UserName, `admin-user-`)].UserName'
```

#### 3. Terraform State Issues
```bash
# Problem: State file corruption or conflicts
# Solution: Reinitialize and import existing resources
rm -rf .terraform/
terraform init
terraform import aws_iam_user.admin_user existing-admin-user-name
```

#### 4. Act/Docker Issues
```bash
# Problem: Docker container issues
# Solution: Clean Docker cache and use specific platform
docker system prune -a
act -W .github/workflows/terraform.yaml --platform ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Debug Mode

```bash
# Act with maximum verbosity
act -W .github/workflows/terraform.yaml --verbose --dryrun

# Terraform with debug logging
export TF_LOG=DEBUG
terraform apply

# GitHub Actions debug  
gh run rerun --debug
```

### Validation Commands

```bash
# Validate Terraform configuration
terraform validate
terraform fmt -check

# Test AWS connectivity
aws sts get-caller-identity

# Verify GitHub CLI authentication
gh auth status
```

## 📚 Advanced Usage

### Multiple Environments

Each deployment creates unique resources with random suffixes, allowing multiple environments:

```bash
# Deploy to dev environment  
act -W .github/workflows/terraform.yaml

# Deploy to staging environment
act -W .github/workflows/terraform.yaml --env-file .env.staging

# Each creates separate: admin-user-{different-suffix}
```

### Infrastructure Customization

Key files to modify:
- **`pave_infra.tf`**: Main infrastructure configuration
- **`terraform.yaml`**: Workflow behavior and steps
- **`get-credentials.sh`**: Credential extraction logic

### Integration with Other Projects

```bash
# 1. Deploy this infrastructure first
act -W .github/workflows/terraform.yaml

# 2. Extract developer credentials
./get-credentials.sh

# 3. Copy credentials to your app project
cp credentials/developer.env ../my-app/.env

# 4. Use AWS SDK in your app with the credentials
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Test locally with Act**: `act -W .github/workflows/terraform.yaml`
4. **Commit changes**: `git commit -am "Add my feature"`
5. **Push to branch**: `git push origin feature/my-feature`
6. **Submit pull request**

### Development Workflow

```bash
# 1. Make changes to infrastructure
vim pave_infra.tf

# 2. Test locally
act -W .github/workflows/terraform.yaml

# 3. Clean up after testing
./cleanup-all.sh

# 4. Commit and push
git add . && git commit -m "Update infrastructure" && git push
```

## 📖 Documentation

- **[GITHUB_SETUP.md](GITHUB_SETUP.md)**: Detailed GitHub repository secrets setup
- **[WARP.md](WARP.md)**: Project documentation and context
- **[Act Documentation](https://github.com/nektos/act)**: Local GitHub Actions runner
- **[Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)**: AWS resource documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:

1. **Check existing issues**: [GitHub Issues](https://github.com/bshuler/cvideo-click-pave/issues)
2. **Review troubleshooting section** above
3. **Run diagnostic commands**:
   ```bash
   # System check
   terraform version
   aws --version
   act --version
   gh --version
   
   # Test connectivity
   aws sts get-caller-identity
   gh auth status
   ```
4. **Create new issue** with detailed information including error messages and system details

---

## 🎉 Quick Start Summary

**New Makefile-Based Approach:**

```bash
# 1. Clone and setup
git clone https://github.com/bshuler/cvideo-click-pave.git && cd cvideo-click-pave

# 2. Initialize environment (installs Python deps, runs terraform init)
make init

# 3. Create secrets file with your AWS admin credentials (for local development)
cat > .secrets << EOF
AWS_ACCESS_KEY_ID=your_admin_key
AWS_SECRET_ACCESS_KEY=your_admin_secret
AWS_REGION=us-east-1
EOF

# 4. Deploy infrastructure 
make apply

# 5. Generate credential templates for your app
make credentials

# 6. Set up GitHub Actions (optional - for CI/CD)
make setup-github

# 7. Check current status anytime
make status

# 8. Clean up everything when done
make clean
```

**Alternative Methods Still Available:**

- **Act**: `act -W .github/workflows/terraform.yaml` (local GitHub Actions testing)
- **GitHub Actions**: `git push origin main` (automatic CI/CD)
- **Direct Terraform**: `terraform apply` (traditional approach)

**All methods now use the Makefile for consistency!** 🚀
