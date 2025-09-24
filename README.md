# CVideo Click Pave - AWS Infrastructure as Code

Fully automated AWS infrastructure provisioning with intelligent workflows, comprehensive error detection, and unified development experience.

## Overview

This repository provides **Infrastructure as Code (IaC)** for AWS using Terraform, with Python automation scripts and a comprehensive Makefile interface. It creates secure, production-ready AWS infrastructure with proper IAM roles, S3 storage, and CI/CD integration.

## Key Features

- **🤖 Fully Automated**: One-command infrastructure deployment
- **🔒 Security First**: Bootstrap user model with protected resources
- **🎯 Intelligent Workflows**: Adapts to local development and GitHub Actions
- **🧪 Comprehensive Testing**: Full test pipeline with validation
- **🛠️ Developer Friendly**: Rich Makefile interface with clear feedback
- **📊 Quality Assurance**: Integrated code formatting, linting, and type checking
- **⚡ Error Detection**: Pylance integration with TypedDict safety monitoring

## 🚀 Quick Start

### Prerequisites

- **AWS Account** with root access (one-time setup only)
- **Terraform** 1.5.6+
- **Python** 3.8+ with pip
- **Docker** (optional, for local testing)
- **GitHub CLI** (optional, for GitHub integration)

### One-Time Bootstrap Setup

**First time only** - requires AWS root account credentials:

1. **Get Root Credentials**:

   ```bash
   make bootstrap-root-help
   ```

2. **Create Bootstrap Infrastructure**:

   ```bash
   make bootstrap-create
   ```

3. **Switch to Bootstrap User**:

   ```bash
   make bootstrap-switch
   ```

After this setup, all operations use secure bootstrap user credentials.

### Deploy Infrastructure

```bash
# Initialize and deploy
make init
make apply

# Generate credentials
make credentials

# Set up GitHub secrets (optional)
make setup-github
```

## 🏗️ What Gets Provisioned

### Core Infrastructure

- **S3 Bucket**: `pave-tf-state-bucket-us-east-1` (Terraform state with versioning)
- **Admin User**: `admin-user` (Full administrative access)
- **Developer User**: `developer-user` (Limited development access)
- **CI/CD Role**: `CICDDeploymentRole` (GitHub Actions deployment)
- **Developer Role**: `DeveloperRole` (Developer role assumption)

### Security Model

- **Bootstrap User**: `bootstrap-user` (Protected, never managed by Terraform)
- **Admin Users**: Cannot delete bootstrap resources (explicit deny policies)
- **Developer Users**: Limited permissions (S3 + Lambda + EC2 read-only)
- **CI/CD Roles**: Specific deployment permissions only

## 🛠️ Development Workflow

### Primary Commands

```bash
# Get help
make help

# Initialize environment
make init

# Deploy infrastructure
make apply

# Run validation and tests
make validate
make test

# Clean up everything
make clean
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Security scan
make security

# Pylance error detection
make pylance-check

# Complete validation
make validate
```

### Testing

```bash
# Full end-to-end test
make full-test

# Local GitHub Actions testing
make test-act

# Infrastructure health check  
make test-infrastructure
```

## 📂 Project Structure

```
```text
├── .github/workflows/
│   └── terraform.yaml         # Unified intelligent workflow
├── scripts/                   # Python automation scripts
│   ├── create_bootstrap.py    # Bootstrap infrastructure creation
│   ├── credentials.py         # Credential management
│   ├── cleanup.py            # Resource cleanup
│   ├── pylance_check_mcp.py  # Pylance error detection
│   └── ...
├── pave_infra.tf             # Main Terraform configuration
├── Makefile                  # Primary interface with rich commands
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Code quality configuration
├── .ai-context.md           # AI assistant guidance
└── credentials/             # Generated credential files (gitignored)
```

## 🔑 Credential Management

The system generates secure credential templates:

```bash
# Generate credentials
make credentials

# View credential info
make credential-info
```

Creates:

- `credentials/admin.env` - Administrator access
- `credentials/developer.env` - Development access

## 🤖 GitHub Integration

Automated GitHub secrets setup:

```bash
# Set repository secrets
make setup-github

# Test GitHub Actions
make test-workflow
```

## 🧪 Testing & Validation

### Full Test Pipeline

```bash
# Complete end-to-end test (requires root credentials)
make full-test YES=1
```

This runs:

1. Complete cleanup
2. Fresh bootstrap setup
3. Infrastructure deployment
4. Credential generation
5. GitHub secrets configuration
6. Comprehensive testing (local, Act, GitHub Actions)

### Individual Tests

```bash
make test-local           # Local Terraform operations
make test-act            # Local GitHub Actions with Act
make test-infrastructure # AWS infrastructure health
make test-workflow       # GitHub Actions workflow
```

## 🔒 Security Features

- **Secret Detection**: Automated scanning for exposed credentials
- **File Permissions**: Secure 600 permissions for credential files
- **TypedDict Safety**: Runtime error prevention with Pylance integration
- **Bootstrap Protection**: Core resources never deleted by automation
- **Access Key Management**: Safe credential rotation and management

## 🌍 Environment Support

- **Local Development**: Direct Terraform + Python scripts
- **Act Testing**: Local GitHub Actions simulation
- **GitHub Actions**: Production CI/CD pipeline
- **Shared State**: S3 remote backend for consistency

## 📊 Monitoring & Status

```bash
# Check current status
make status

# View Terraform state
make state-show

# Create state backup
make state-backup
```

## 🧹 Cleanup & Maintenance

```bash
# Clean local files
make clean-local

# Comprehensive AWS cleanup (destructive!)
make clean

# Clean and redeploy
make dev-deploy
```

## 🆘 Troubleshooting

### Common Issues

1. **Bootstrap Setup**: Run `make bootstrap-check` to validate
2. **Credentials**: Use `make credential-info` for status
3. **State Issues**: Use `make state-pull` to sync
4. **Permission Errors**: Verify AWS credentials with `make bootstrap-check`

### Getting Help

```bash
make help                    # Show all commands
make bootstrap-root-help     # Root credential setup
make bootstrap-reset-help    # Reset instructions  
make full-test-help         # Full test documentation
```

## 🔄 Advanced Operations

### State Management

```bash
make state-show              # View current state
make state-pull             # Pull remote state
make state-backup           # Create backup
make state-import RESOURCE=<name> ID=<id>  # Import resource
```

### Bootstrap Management

```bash
make bootstrap-check        # Validate bootstrap setup
make bootstrap-create       # Create bootstrap (root required)
make bootstrap-destroy      # Destroy bootstrap (root required)
make bootstrap-fix          # Fix S3 permissions
```

## 💡 Best Practices

1. **Always run validation**: `make validate` before commits
2. **Use full test pipeline**: `make full-test` for comprehensive validation
3. **Monitor credentials**: Regular `make credential-info` checks
4. **Backup state**: `make state-backup` before major changes
5. **Clean deployments**: Use `make dev-deploy` for clean slate testing

## 🤝 Contributing

1. **Code Quality**: All changes must pass `make validate`
2. **Testing**: Use `make full-test` to verify end-to-end functionality
3. **Documentation**: Update relevant `.md` files
4. **Security**: Run `make security` to check for exposed secrets

## 📋 System Requirements

- **OS**: macOS, Linux, Windows (WSL)
- **Python**: 3.8+ with pip and virtualenv
- **Terraform**: 1.5.6+ (automatically installed by scripts)
- **AWS CLI**: Optional (scripts use boto3 directly)
- **Docker**: Required for Act testing
- **Git**: Required for GitHub integration

---

**🎯 Ready to get started?** Run `make help` to see all available commands!
