# Makefile for cvideo-click-pave infrastructure management
# This is the primary interface for all infrastructure operations

.PHONY: help init plan apply destroy clean credentials setup-github dev-deploy dev-clean validate test format lint type-check state-show state-pull state-backup

# Default target
help:
	@echo "🚀 CVideo Click Pave Infrastructure Management"
	@echo ""
	@echo "Bootstrap Setup:"
	@echo "  make bootstrap-check       Validate bootstrap user setup (required first)"
	@echo "  make bootstrap-fix         Fix bootstrap user S3 permissions issue"
	@echo "  make bootstrap-create      Create complete bootstrap setup (requires root/admin)"
	@echo "  make bootstrap-destroy     Destroy bootstrap setup for fresh start (requires root/admin)"
	@echo "  make bootstrap-switch      Clear root credentials after bootstrap-create"
	@echo "  make bootstrap-reset-help  Show step-by-step root account reset instructions"
	@echo "  make bootstrap-root-help   Interactive guide for getting AWS root credentials"
	@echo "  make credential-info       Show complete credential configuration summary"
	@echo ""
	@echo "Core Infrastructure Operations:"
	@echo "  make init          Initialize terraform and install Python dependencies"  
	@echo "  make plan          Run terraform plan to preview changes"
	@echo "  make apply         Deploy infrastructure with terraform apply"
	@echo "  make destroy       Destroy infrastructure with terraform destroy" 
	@echo "  make clean         Comprehensive cleanup of all AWS resources (destructive!)"
	@echo ""
	@echo "State Management (S3 Remote Backend):"
	@echo "  make state-show    Show current Terraform state resources"
	@echo "  make state-pull    Pull current state from S3"
	@echo "  make state-backup  Create local backup of remote state"
	@echo ""
	@echo "Credential Management:"
	@echo "  make credentials   Generate credential template files"
	@echo "  make setup-github  Set up GitHub repository secrets (requires admin creds)"
	@echo ""
	@echo "Development Workflow:"
	@echo "  make dev-deploy    Full local development deployment (clean slate)"
	@echo "  make dev-clean     Clean up development resources"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format        Format code with Black"
	@echo "  make lint          Lint code with Flake8"
	@echo "  make type-check    Type check with mypy"
	@echo "  make security      Security scan for secrets and vulnerabilities"
	@echo "  make validate      Validate terraform configuration and Python code"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run tests (if any exist)"
	@echo ""
	@echo "📋 Current Status:"
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/status.py 2>/dev/null || echo "  Run 'make init' first to check status"; \
	else \
		python3 scripts/status.py 2>/dev/null || echo "  Run 'make init' first to check status"; \
	fi

# Initialize everything needed for development
# Validate bootstrap user setup (prerequisite for all operations)
bootstrap-check:
	@echo "🔐 Validating bootstrap user setup..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/validate_bootstrap.py; \
	else \
		python3 scripts/validate_bootstrap.py; \
	fi

# Fix bootstrap user S3 permissions issue
bootstrap-fix:
	@echo "🔧 Fixing bootstrap user S3 permissions..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/fix_bootstrap_s3.py; \
	else \
		python3 scripts/fix_bootstrap_s3.py; \
	fi

# Create complete bootstrap setup (requires root/admin credentials)
bootstrap-create:
	@echo "🚀 Creating bootstrap user setup..."
	@echo "⚠️  WARNING: This requires AWS root account credentials!"
	@echo "📖 See BOOTSTRAP_GUIDE.md for detailed root account setup instructions"
	@python3 scripts/create_bootstrap.py

# Clear root credentials and switch to bootstrap user (run after bootstrap-create)
bootstrap-switch:
	@echo "🔄 Switching from root to bootstrap credentials..."
	@echo "📝 Root credentials cleared from environment"
	@echo "✅ Now using bootstrap credentials from .secrets file"
	@echo "🔧 Run 'make bootstrap-check' to verify the switch worked"

# Destroy bootstrap setup for fresh start (requires root/admin credentials)
bootstrap-destroy:
	@echo "💥 Destroying bootstrap user setup..."
	@echo "⚠️  WARNING: This requires AWS root account credentials!"
	@echo "📖 See BOOTSTRAP_GUIDE.md for detailed root account setup instructions"
	@python3 scripts/destroy_bootstrap.py

# Show complete bootstrap reset instructions
bootstrap-reset-help:
	@echo "🔧 Complete Bootstrap Reset Process:"
	@echo ""
	@echo "1️⃣  Switch to AWS root account credentials:"
	@echo "   export AWS_ACCESS_KEY_ID=\"your_root_access_key\""
	@echo "   export AWS_SECRET_ACCESS_KEY=\"your_root_secret_key\""
	@echo "   aws sts get-caller-identity  # Should show root ARN"
	@echo ""
	@echo "2️⃣  Destroy current bootstrap setup:"
	@echo "   make bootstrap-destroy"
	@echo ""
	@echo "3️⃣  Create new bootstrap setup (auto-updates .secrets):"
	@echo "   make bootstrap-create"
	@echo ""
	@echo "4️⃣  Clear root credentials and switch to bootstrap:"
	@echo "   unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY"
	@echo ""
	@echo "5️⃣  Test the fix:"
	@echo "   make bootstrap-check"
	@echo ""
	@echo "📖 For detailed instructions see: BOOTSTRAP_GUIDE.md"

# Interactive guide for getting AWS root account credentials
bootstrap-root-help:
	@python3 scripts/get_root_credentials_help.py

# Show credential configuration summary
credential-info:
	@echo "🔐 CVideo Click Pave Credential Configuration"
	@echo "============================================="
	@echo ""
	@echo "📋 Commands using .secrets file (bootstrap credentials):"
	@echo "   • make bootstrap-check      - Validate bootstrap setup"
	@echo "   • make bootstrap-fix        - Fix bootstrap permissions"
	@echo "   • make init                 - Initialize Terraform"
	@echo "   • make plan                 - Plan infrastructure changes"
	@echo "   • make apply                - Deploy infrastructure"
	@echo "   • make destroy              - Destroy infrastructure"
	@echo "   • make validate             - Validate configuration"
	@echo "   • make clean                - Cleanup all AWS resources"
	@echo "   • make credentials          - Generate credential templates"
	@echo "   • make setup-github         - Setup GitHub repository secrets"
	@echo "   • make status               - Check current status"
	@echo "   • make state-show           - Show Terraform state"
	@echo "   • make state-pull           - Pull Terraform state"
	@echo "   • make state-backup         - Backup Terraform state"
	@echo "   • make dev-deploy           - Development deployment"
	@echo "   • make dev-clean            - Clean development resources"
	@echo ""
	@echo "🔑 Commands using environment variables (root credentials):"
	@echo "   • make bootstrap-create     - Create bootstrap setup"
	@echo "   • make bootstrap-destroy    - Destroy bootstrap setup"
	@echo ""
	@echo "ℹ️  Commands NOT requiring AWS credentials:"
	@echo "   • make bootstrap-root-help  - Interactive credential guide"
	@echo "   • make bootstrap-reset-help - Show reset instructions"
	@echo "   • make bootstrap-switch     - Switch credential context"
	@echo "   • make help                 - Show help"
	@echo "   • make format               - Format code"
	@echo "   • make lint                 - Lint code"
	@echo "   • make test                 - Run tests"
	@echo "   • make clean-local          - Clean local files"
	@echo ""
	@if [ -f .secrets ]; then \
		echo "✅ .secrets file found - bootstrap credentials available"; \
		echo "📝 Current bootstrap user: $$(grep AWS_ACCESS_KEY_ID .secrets | cut -d= -f2)"; \
	else \
		echo "❌ .secrets file not found - run 'make bootstrap-create' first"; \
	fi

# Initialize environment (requires bootstrap user)
init: bootstrap-check
	@echo "🔧 Initializing development environment..."
	@echo "📦 Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "🏗️ Initializing Terraform..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform init; \
	else \
		terraform init; \
	fi
	@echo "✅ Initialization complete!"

# Format Python code with Black
format:
	@echo "🎨 Formatting Python code with Black..."
	@python3 -m black scripts/
	@echo "✅ Code formatting complete!"

# Lint Python code with Flake8
lint:
	@echo "🔍 Linting Python code with Flake8..."
	@python3 -m flake8 scripts/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "✅ Linting complete!"

# Type check Python code with mypy
type-check:
	@echo "🔍 Type checking Python code with mypy..."
	@python3 -m mypy scripts/
	@echo "✅ Type checking complete!"

# Security scan for secrets and vulnerabilities
security:
	@echo "🔒 Running security scan for secrets and vulnerabilities..."
	@echo "🔍 Scanning for exposed secrets..."
	@# Check for common secret patterns in all files except .secrets (which is intentionally excluded)
	@grep -r -n -E "(aws_access_key_id|aws_secret_access_key|password|secret|token|key)" --include="*.py" --include="*.tf" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.md" --exclude-dir=".git" --exclude-dir=".terraform" . | grep -v "\.secrets" | grep -v -E "(# |#|//|/\*|\*)" || echo "✅ No exposed secrets found in code"
	@echo "🔍 Checking for hardcoded AWS credentials..."
	@grep -r -n -E "AKIA[0-9A-Z]{16}" --include="*.py" --include="*.tf" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.md" --exclude-dir=".git" --exclude-dir=".terraform" . | grep -v "\.secrets" || echo "✅ No hardcoded AWS access keys found"
	@echo "🔍 Checking for sensitive file permissions..."
	@if [ -f .secrets ]; then \
		PERMS=$$(stat -f "%A" .secrets 2>/dev/null || stat -c "%a" .secrets 2>/dev/null); \
		if [ "$$PERMS" != "600" ]; then \
			echo "⚠️  WARNING: .secrets file has permissions $$PERMS, should be 600"; \
			chmod 600 .secrets; \
			echo "🔧 Fixed .secrets permissions to 600"; \
		else \
			echo "✅ .secrets file has secure permissions (600)"; \
		fi; \
	fi
	@echo "🔍 Checking .gitignore for sensitive files..."
	@if ! grep -q "\.secrets" .gitignore; then \
		echo "⚠️  WARNING: .secrets not in .gitignore"; \
	else \
		echo "✅ .secrets properly excluded from git"; \
	fi
	@if ! grep -q "\*\.tfstate\|terraform\.tfstate" .gitignore; then \
		echo "⚠️  WARNING: terraform state files not in .gitignore"; \
	else \
		echo "✅ terraform state files properly excluded from git"; \
	fi
	@echo "✅ Security scan complete!"

# Validate configuration and dependencies
validate: security format lint
	@echo "🔍 Validating configuration..."
	@echo "📋 Checking Terraform configuration..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform validate && terraform fmt -check; \
	else \
		terraform validate && terraform fmt -check; \
	fi
	@echo "🐍 Checking Python dependencies..."
	@python3 -c "import boto3; print('✅ boto3 available')" 2>/dev/null || (echo "❌ boto3 not found. Run 'make init'" && exit 1)
	@echo "🔑 Checking AWS credentials..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/validate.py; \
	else \
		python3 scripts/validate.py; \
	fi
	@echo "✅ All validations passed!"

# Plan infrastructure changes
plan: validate
	@echo "📋 Planning infrastructure changes..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform plan; \
	else \
		terraform plan; \
	fi

# Deploy infrastructure
apply: validate
	@echo "🚀 Deploying infrastructure..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform apply; \
	else \
		terraform apply; \
	fi

# Destroy infrastructure
destroy:
	@echo "⚠️  Destroying infrastructure..."
	@echo "This will remove all Terraform-managed resources."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform destroy; \
	else \
		terraform destroy; \
	fi

# Comprehensive cleanup of all AWS resources
clean:
	@echo "🧹 Starting comprehensive cleanup..."
	@echo "⚠️  This will remove ALL pave infrastructure resources (past and present)"
	@read -p "Are you sure? This is destructive! (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/cleanup.py; \
	else \
		python3 scripts/cleanup.py; \
	fi

# State Management (S3 Remote Backend)
state-show:
	@echo "📊 Showing Terraform state information..."
	@echo "Backend: S3 (pave-tf-state-bucket-us-east-1)"
	@echo "Resources:"
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform state list; \
	else \
		terraform state list; \
	fi

state-pull:
	@echo "📥 Pulling current state from S3..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform state pull; \
	else \
		terraform state pull; \
	fi

state-backup:
	@echo "💾 Creating local backup of remote state..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform state pull > terraform.tfstate.backup.$(shell date +%Y%m%d-%H%M%S); \
	else \
		terraform state pull > terraform.tfstate.backup.$(shell date +%Y%m%d-%H%M%S); \
	fi
	@echo "✅ State backed up with timestamp"

# Generate credential templates
credentials:
	@echo "🔐 Generating credential templates..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/credentials.py; \
	else \
		python3 scripts/credentials.py; \
	fi

# Set up GitHub repository secrets (requires existing admin credentials)
setup-github:
	@echo "🔧 Setting up GitHub repository secrets..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/github_setup.py; \
	else \
		python3 scripts/github_setup.py; \
	fi

# Development workflow - clean slate deployment
dev-deploy:
	@echo "🔄 Starting development deployment (clean slate)..."
	@echo "Step 1: Clean up any existing resources"
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/cleanup.py --skip-confirm; \
	else \
		python3 scripts/cleanup.py --skip-confirm; \
	fi
	@echo "Step 2: Deploy fresh infrastructure"
	@$(MAKE) apply
	@echo "Step 3: Generate credentials"
	@$(MAKE) credentials
	@echo "✅ Development deployment complete!"

# Clean development resources
dev-clean:
	@echo "🧹 Cleaning development resources..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/cleanup.py --dev-only; \
	else \
		python3 scripts/cleanup.py --dev-only; \
	fi

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
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/status.py; \
	else \
		python3 scripts/status.py; \
	fi

# Clean local state and caches
clean-local:
	@echo "🧹 Cleaning local files..."
	@rm -rf .terraform/
	@rm -f terraform.tfstate*
	@rm -rf credentials/
	@rm -f requirements.txt
	@echo "✅ Local cleanup complete. Run 'make init' to reinitialize."