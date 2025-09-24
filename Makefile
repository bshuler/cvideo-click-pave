# Makefile for cvideo-click-pave infrastructure management
# This is the primary interface for all infrastructure operations

.PHONY: help init plan apply destroy clean credentials setup-github dev-deploy dev-clean validate test

# Default target
help:
	@echo "🚀 CVVideo Click Pave Infrastructure Management"
	@echo ""
	@echo "Bootstrap Setup:"
	@echo "  make bootstrap-check   Validate bootstrap user setup (required first)"
	@echo ""
	@echo "Core Infrastructure Operations:"
	@echo "  make init          Initialize terraform and install Python dependencies"  
	@echo "  make plan          Run terraform plan to preview changes"
	@echo "  make apply         Deploy infrastructure with terraform apply"
	@echo "  make destroy       Destroy infrastructure with terraform destroy" 
	@echo "  make clean         Comprehensive cleanup of all AWS resources (destructive!)"
	@echo ""
	@echo "Credential Management:"
	@echo "  make credentials   Generate credential template files"
	@echo "  make setup-github  Set up GitHub repository secrets (requires admin creds)"
	@echo ""
	@echo "Development Workflow:"
	@echo "  make dev-deploy    Full local development deployment (clean slate)"
	@echo "  make dev-clean     Clean up development resources"
	@echo ""
	@echo "Validation & Testing:"
	@echo "  make validate      Validate terraform configuration and Python code"
	@echo "  make test          Run tests (if any exist)"
	@echo ""
	@echo "📋 Current Status:"
	@python3 scripts/status.py 2>/dev/null || echo "  Run 'make init' first to check status"

# Initialize everything needed for development
# Validate bootstrap user setup (prerequisite for all operations)
bootstrap-check:
	@echo "🔐 Validating bootstrap user setup..."
	@python3 scripts/validate_bootstrap.py

# Initialize environment (requires bootstrap user)
init: bootstrap-check
	@echo "🔧 Initializing development environment..."
	@echo "📦 Installing Python dependencies..."
	@pip3 install --quiet boto3 botocore
	@echo "📋 Writing requirements.txt..."
	@echo "boto3>=1.28.0" > requirements.txt
	@echo "botocore>=1.31.0" >> requirements.txt
	@echo "🏗️ Initializing Terraform..."
	@terraform init
	@echo "✅ Initialization complete!"

# Validate configuration and dependencies
validate:
	@echo "🔍 Validating configuration..."
	@echo "📋 Checking Terraform configuration..."
	@terraform validate
	@terraform fmt -check
	@echo "🐍 Checking Python dependencies..."
	@python3 -c "import boto3; print('✅ boto3 available')" 2>/dev/null || (echo "❌ boto3 not found. Run 'make init'" && exit 1)
	@echo "🔑 Checking AWS credentials..."
	@python3 scripts/validate.py
	@echo "✅ All validations passed!"

# Plan infrastructure changes
plan: validate
	@echo "📋 Planning infrastructure changes..."
	@terraform plan

# Deploy infrastructure
apply: validate
	@echo "🚀 Deploying infrastructure..."
	@terraform apply

# Destroy infrastructure
destroy:
	@echo "⚠️  Destroying infrastructure..."
	@echo "This will remove all Terraform-managed resources."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@terraform destroy

# Comprehensive cleanup of all AWS resources
clean:
	@echo "🧹 Starting comprehensive cleanup..."
	@echo "⚠️  This will remove ALL pave infrastructure resources (past and present)"
	@read -p "Are you sure? This is destructive! (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@python3 scripts/cleanup.py

# Generate credential templates
credentials:
	@echo "🔐 Generating credential templates..."
	@python3 scripts/credentials.py

# Set up GitHub repository secrets (requires existing admin credentials)
setup-github:
	@echo "🔧 Setting up GitHub repository secrets..."
	@python3 scripts/github_setup.py

# Development workflow - clean slate deployment
dev-deploy:
	@echo "🔄 Starting development deployment (clean slate)..."
	@echo "Step 1: Clean up any existing resources"
	@python3 scripts/cleanup.py --skip-confirm
	@echo "Step 2: Deploy fresh infrastructure"
	@$(MAKE) apply
	@echo "Step 3: Generate credentials"
	@$(MAKE) credentials
	@echo "✅ Development deployment complete!"

# Clean development resources
dev-clean:
	@echo "🧹 Cleaning development resources..."
	@python3 scripts/cleanup.py --dev-only

# Run tests
test:
	@echo "🧪 Running tests..."
	@echo "ℹ️  No tests defined yet"

# GitHub Actions integration targets (called by workflow)
ci-init:
	@echo "🤖 CI/CD Initialization..."
	@pip3 install --quiet boto3 botocore
	@terraform init

ci-deploy:
	@echo "🤖 CI/CD Deployment..."
	@terraform plan
	@terraform apply -auto-approve

# Local Act testing
act-deploy:
	@echo "🐳 Act deployment..."
	@act -W .github/workflows/terraform.yaml

# Status check
status:
	@python3 scripts/status.py

# Clean local state and caches
clean-local:
	@echo "🧹 Cleaning local files..."
	@rm -rf .terraform/
	@rm -f terraform.tfstate*
	@rm -rf credentials/
	@rm -f requirements.txt
	@echo "✅ Local cleanup complete. Run 'make init' to reinitialize."