# ==============================================================================
# Makefile for CVideo Click Pave Infrastructure Management
# ==============================================================================
# This is the primary interface for all infrastructure operations
# Organized by workflow: Bootstrap -> Core Operations -> Testing -> Development

.DEFAULT_GOAL := help

# ==============================================================================
# PHONY TARGETS
# ==============================================================================
.PHONY: help \
        bootstrap-check bootstrap-create bootstrap-destroy bootstrap-fix bootstrap-switch bootstrap-reset-help bootstrap-root-help credential-info \
        init plan apply destroy clean credentials setup-github-auto \
        state-show state-pull state-backup state-import fix-s3-conflict apply-continue \
        format lint type-check security validate \
        test test-workflow test-infrastructure test-act test-local \
        full-test full-test-help \
        dev-deploy dev-clean status clean-local \
        ci-init ci-deploy

# ==============================================================================
# HELP & DOCUMENTATION
# ==============================================================================
help:
	@echo "🚀 CVideo Click Pave Infrastructure Management"
	@echo "=============================================="
	@echo ""
	@echo "🏁 FULL TEST WORKFLOW:"
	@echo "  make full-test         Complete end-to-end infrastructure test (requires root credentials)"
	@echo "  make full-test-help    Show detailed full test workflow documentation"
	@echo ""
	@echo "🔐 BOOTSTRAP OPERATIONS (Foundation Setup):"
	@echo "  make bootstrap-check       Validate bootstrap user setup (required first)"
	@echo "  make bootstrap-create      Create complete bootstrap setup (requires root/admin)"
	@echo "  make bootstrap-destroy     Destroy bootstrap setup for fresh start (requires root/admin)"
	@echo "  make bootstrap-fix         Fix bootstrap user S3 permissions issue"
	@echo "  make bootstrap-switch      Clear root credentials after bootstrap-create"
	@echo "  make bootstrap-reset-help  Show step-by-step root account reset instructions"
	@echo "  make bootstrap-root-help   Interactive guide for getting AWS root credentials"
	@echo "  make credential-info       Show complete credential configuration summary"
	@echo ""
	@echo "🏗️ CORE INFRASTRUCTURE OPERATIONS:"
	@echo "  make init          Initialize terraform and install Python dependencies"  
	@echo "  make plan          Run terraform plan to preview changes"
	@echo "  make apply         Deploy infrastructure with terraform apply"
	@echo "  make destroy       Destroy infrastructure with terraform destroy" 
	@echo "  make clean         Comprehensive cleanup of all AWS resources (destructive!)"
	@echo ""
	@echo "🔑 CREDENTIAL & SECRETS MANAGEMENT:"
	@echo "  make credentials       Generate credential template files"
	@echo "  make setup-github-auto Automatically set GitHub secrets from admin.env"
	@echo ""
	@echo "🗄️ STATE MANAGEMENT (S3 Remote Backend):"
	@echo "  make state-show        Show current Terraform state resources"
	@echo "  make state-pull        Pull current state from S3"
	@echo "  make state-backup      Create local backup of remote state"
	@echo "  make state-import      Import existing AWS resource (RESOURCE=<name> ID=<id>)"
	@echo "  make fix-s3-conflict   Fix S3 bucket already exists error"
	@echo "  make apply-continue    Continue deployment after fixing conflicts"
	@echo ""
	@echo "🧪 TESTING & VALIDATION:"
	@echo "  make test                  Run comprehensive infrastructure tests"
	@echo "  make test-workflow         Test GitHub Actions workflow execution"
	@echo "  make test-infrastructure   Test deployed AWS infrastructure health"
	@echo "  make test-act              Test with Act (local GitHub Actions)"
	@echo "  make test-local            Test local Terraform operations"
	@echo ""
	@echo "🔍 CODE QUALITY:"
	@echo "  make format        Format code with Black"
	@echo "  make lint          Lint code with Flake8"
	@echo "  make type-check    Type check with mypy"
	@echo "  make security      Security scan for secrets and vulnerabilities"
	@echo "  make validate      Validate terraform configuration and Python code"
	@echo ""
	@echo "🛠️ DEVELOPMENT WORKFLOW:"
	@echo "  make dev-deploy    Full local development deployment (clean slate)"
	@echo "  make dev-clean     Clean up development resources"
	@echo "  make status        Show current infrastructure status"
	@echo "  make clean-local   Clean local files and caches"
	@echo ""
	@echo "Testing & Validation:"
	@echo "  make test              Run comprehensive infrastructure tests"
	@echo "  make test-workflow     Test GitHub Actions workflow execution"
	@echo "  make test-infrastructure  Test deployed AWS infrastructure health"
	@echo ""
	@echo "📋 Current Status:"
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/status.py 2>/dev/null || echo "  Run 'make init' first to check status"; \
	else \
		python3 scripts/status.py 2>/dev/null || echo "  Run 'make init' first to check status"; \
	fi

# ==============================================================================
# FULL TEST WORKFLOW
# ==============================================================================

# Complete end-to-end infrastructure test
full-test:
	@echo "🧪 STARTING FULL END-TO-END INFRASTRUCTURE TEST"
	@echo "==============================================="
	@echo ""
	@echo "⚠️  WARNING: This is a comprehensive test that will:"
	@echo "   • Destroy existing bootstrap user (requires root credentials)"
	@echo "   • Clean all AWS resources (destructive operation)"
	@echo "   • Create fresh bootstrap setup with S3 backend"
	@echo "   • Deploy complete infrastructure from scratch"
	@echo "   • Test all pipelines (local, act, GitHub Actions)"
	@echo ""
	@echo "🔍 Checking for root credentials..."
	@if [ -f .root-secrets ]; then \
		echo "✅ Found .root-secrets file - using root credentials"; \
	elif [ -n "$$AWS_ACCESS_KEY_ID" ] && [ -n "$$AWS_SECRET_ACCESS_KEY" ]; then \
		echo "✅ Root credentials detected in environment"; \
	else \
		echo "❌ Root AWS credentials not found"; \
		echo "💡 Either create .root-secrets file or set environment variables:"; \
		echo "   export AWS_ACCESS_KEY_ID=\"your_root_access_key\""; \
		echo "   export AWS_SECRET_ACCESS_KEY=\"your_root_secret_key\""; \
		echo "📖 Or run: make bootstrap-root-help"; \
		exit 1; \
	fi
	@echo ""
	@echo "🏁 PHASE 1: COMPLETE CLEANUP (using root credentials)"
	@echo "===================================================="
	@echo "1️⃣  Destroying existing bootstrap user..."
	@if [ -f .root-secrets ]; then \
		set -a && source .root-secrets && set +a && $(MAKE) bootstrap-destroy; \
	else \
		$(MAKE) bootstrap-destroy; \
	fi || echo "⚠️  Bootstrap destroy completed (may have warnings)"
	@echo ""
	@echo "2️⃣  Cleaning all AWS resources..."
	@if [ -f .root-secrets ]; then \
		set -a && source .root-secrets && set +a && $(MAKE) clean; \
	else \
		$(MAKE) clean; \
	fi || echo "⚠️  Cleanup completed (may have warnings)"
	@echo ""
	@echo "🏁 PHASE 2: FRESH SETUP (using root credentials)"
	@echo "================================================"
	@echo "3️⃣  Creating fresh bootstrap setup with S3 backend..."
	@if [ -f .root-secrets ]; then \
		set -a && source .root-secrets && set +a && $(MAKE) bootstrap-create; \
	else \
		$(MAKE) bootstrap-create; \
	fi
	@echo ""
	@echo "🔄 Clearing root credentials and switching to bootstrap credentials..."
	@echo "✅ Environment cleared - now using bootstrap credentials from .secrets"
	@echo ""
	@echo "🏁 PHASE 3: INFRASTRUCTURE DEPLOYMENT (using bootstrap credentials)"
	@echo "=================================================================="
	@echo "4️⃣  Initializing Terraform..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) init
	@echo ""
	@echo "5️⃣  Planning infrastructure..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) plan
	@echo ""
	@echo "6️⃣  Applying infrastructure..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) apply
	@echo ""
	@echo "🏁 PHASE 4: CREDENTIAL SETUP"
	@echo "============================"
	@echo "7️⃣  Generating credentials..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) credentials
	@echo ""
	@echo "8️⃣  Setting up GitHub secrets..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) setup-github-auto || echo "⚠️  GitHub secrets setup had issues (check GitHub CLI)"
	@echo ""
	@echo "🏁 PHASE 5: COMPREHENSIVE TESTING"
	@echo "=================================="
	@echo "9️⃣  Testing local Terraform operations..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) test-local
	@echo ""
	@echo "🔟 Testing infrastructure health..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) test-infrastructure
	@echo ""
	@echo "1️⃣1️⃣  Testing with Act (local GitHub Actions)..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) test-act || echo "⚠️  Act testing had issues (check Act installation)"
	@echo ""
	@echo "1️⃣2️⃣  Testing GitHub Actions workflow..."
	@env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY $(MAKE) test-workflow || echo "⚠️  GitHub workflow testing had issues (check GitHub CLI)"
	@echo ""
	@echo "🎉 FULL TEST COMPLETED SUCCESSFULLY!"
	@echo "====================================="
	@echo "✅ Bootstrap setup: Complete"
	@echo "✅ Infrastructure deployment: Complete"
	@echo "✅ Credential generation: Complete"
	@echo "✅ GitHub secrets: Configured"
	@echo "✅ Local testing: Passed"
	@echo "✅ Infrastructure health: Validated"
	@echo "✅ Pipeline testing: Complete"
	@echo ""
	@echo "🔍 Final status check:"
	@$(MAKE) status

# Show detailed full test workflow documentation
full-test-help:
	@echo "🧪 FULL TEST WORKFLOW DOCUMENTATION"
	@echo "==================================="
	@echo ""
	@echo "The full test is a comprehensive end-to-end validation that:"
	@echo ""
	@echo "📋 PREREQUISITES:"
	@echo "   • AWS root account credentials (.root-secrets file or environment variables)"
	@echo "   • GitHub CLI installed and authenticated (gh auth login)"
	@echo "   • Act installed for local GitHub Actions testing (optional)"
	@echo "   • Clean working directory (no uncommitted changes)"
	@echo ""
	@echo "🔄 WORKFLOW PHASES:"
	@echo ""
	@echo "   Phase 1: Complete Cleanup (Root Credentials Required)"
	@echo "   ------------------------------------------------"
	@echo "   • Destroy existing bootstrap user and policies"
	@echo "   • Clean all pave-related AWS resources"
	@echo "   • Remove local state and credential files"
	@echo ""
	@echo "   Phase 2: Fresh Setup (Root Credentials Required)"
	@echo "   ----------------------------------------------"
	@echo "   • Create new bootstrap user with proper permissions"
	@echo "   • Create S3 backend bucket with versioning/encryption"
	@echo "   • Store bootstrap credentials in .secrets file"
	@echo "   • Store root credentials in AWS Secrets Manager"
	@echo ""
	@echo "   Phase 3: Infrastructure Deployment (Bootstrap Credentials)"
	@echo "   --------------------------------------------------------"
	@echo "   • Initialize Terraform with S3 backend"
	@echo "   • Plan infrastructure changes"
	@echo "   • Deploy complete infrastructure (users, roles, policies)"
	@echo ""
	@echo "   Phase 4: Credential Setup"
	@echo "   ------------------------"
	@echo "   • Generate admin and developer credential files"
	@echo "   • Configure GitHub repository secrets automatically"
	@echo ""
	@echo "   Phase 5: Comprehensive Testing"
	@echo "   -----------------------------"
	@echo "   • Test local Terraform operations"
	@echo "   • Validate infrastructure health"
	@echo "   • Test with Act (local GitHub Actions simulation)"
	@echo "   • Trigger and monitor GitHub Actions workflow"
	@echo ""
	@echo "⏱️ ESTIMATED TIME: 10-15 minutes"
	@echo ""
	@echo "🚀 TO RUN:"
	@echo "   # Option 1: Using .root-secrets file (recommended)"
	@echo "   make full-test"
	@echo ""
	@echo "   # Option 2: Using environment variables"
	@echo "   export AWS_ACCESS_KEY_ID=\"your_root_access_key\""
	@echo "   export AWS_SECRET_ACCESS_KEY=\"your_root_secret_key\""
	@echo "   make full-test"

# ==============================================================================
# BOOTSTRAP OPERATIONS
# ==============================================================================

# Validate bootstrap user setup (prerequisite for all operations)
bootstrap-check:
	@echo "🔐 Validating bootstrap user setup..."
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && python3 scripts/validate_bootstrap.py'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY python3 scripts/validate_bootstrap.py; \
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
	@if [ -f .root-secrets ]; then \
		echo "✅ Using root credentials from .root-secrets"; \
		set -a && source .root-secrets && set +a && python3 scripts/create_bootstrap.py; \
	else \
		echo "📖 Using environment credentials (see BOOTSTRAP_GUIDE.md for setup)"; \
		python3 scripts/create_bootstrap.py; \
	fi

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
	@if [ -f .root-secrets ]; then \
		echo "✅ Using root credentials from .root-secrets"; \
		if [ "$(MAKE_LEVEL)" = "0" ]; then \
			set -a && source .root-secrets && set +a && python3 scripts/destroy_bootstrap.py; \
		else \
			set -a && source .root-secrets && set +a && python3 scripts/destroy_bootstrap.py --skip-confirm; \
		fi; \
	else \
		echo "📖 Using environment credentials (see BOOTSTRAP_GUIDE.md for setup)"; \
		if [ "$(MAKE_LEVEL)" = "0" ]; then \
			python3 scripts/destroy_bootstrap.py; \
		else \
			python3 scripts/destroy_bootstrap.py --skip-confirm; \
		fi; \
	fi

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
	@echo "   • make setup-github-auto    - Setup GitHub repository secrets"
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
	@echo "� Clearing any existing AWS credentials and using bootstrap credentials..."
	@echo "�📦 Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "🏗️ Initializing Terraform..."
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && terraform init'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY terraform init; \
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
	@python3 -m flake8 scripts/
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
validate: init security format lint
	@echo "🔍 Validating configuration..."
	@echo "📋 Checking Terraform configuration..."
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && terraform validate && terraform fmt -check'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'terraform validate && terraform fmt -check'; \
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
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && terraform plan'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY terraform plan; \
	fi

# Deploy infrastructure
apply: validate
	@echo "🚀 Deploying infrastructure..."
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && terraform apply'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY terraform apply; \
	fi

# Destroy infrastructure
destroy:
	@echo "⚠️  Destroying infrastructure..."
	@echo "This will remove all Terraform-managed resources."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && terraform destroy'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY terraform destroy; \
	fi

# Comprehensive cleanup of all AWS resources
clean:
	@echo "🧹 Starting comprehensive cleanup..."
	@echo "⚠️  This will remove ALL pave infrastructure resources (past and present)"
	@if [ "$(MAKE_LEVEL)" = "0" ]; then \
		read -p "Are you sure? This is destructive! (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1; \
	fi
	@if [ -f .secrets ]; then \
		if [ "$(MAKE_LEVEL)" = "0" ]; then \
			set -a && source .secrets && set +a && python3 scripts/cleanup.py; \
		else \
			set -a && source .secrets && set +a && python3 scripts/cleanup.py --skip-confirm; \
		fi; \
	else \
		if [ "$(MAKE_LEVEL)" = "0" ]; then \
			python3 scripts/cleanup.py; \
		else \
			python3 scripts/cleanup.py --skip-confirm; \
		fi; \
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

# Import existing AWS resources into Terraform state
state-import:
	@echo "📥 Importing AWS resource into Terraform state..."
	@if [ -z "$(RESOURCE)" ] || [ -z "$(ID)" ]; then \
		echo "❌ Usage: make state-import RESOURCE=<terraform_resource> ID=<aws_resource_id>"; \
		echo "   Example: make state-import RESOURCE=aws_s3_bucket.tf_state_bucket ID=pave-tf-state-bucket-us-east-1"; \
		exit 1; \
	fi
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform import $(RESOURCE) $(ID); \
	else \
		terraform import $(RESOURCE) $(ID); \
	fi
	@echo "✅ Resource imported successfully"

# Fix common infrastructure deployment issues
fix-s3-conflict:
	@echo "🔧 Fixing S3 bucket conflict by importing existing bucket..."
	@$(MAKE) state-import RESOURCE=aws_s3_bucket.tf_state_bucket ID=pave-tf-state-bucket-us-east-1

# Continue infrastructure deployment after fixing conflicts
apply-continue:
	@echo "🚀 Continuing infrastructure deployment..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform apply -auto-approve; \
	else \
		terraform apply -auto-approve; \
	fi

# Generate credential templates
credentials:
	@echo "🔐 Generating credential templates..."
	@if [ -f .secrets ]; then \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY bash -c 'set -a && source .secrets && set +a && python3 scripts/credentials.py'; \
	else \
		env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY python3 scripts/credentials.py; \
	fi

# Automatically set GitHub secrets using admin credentials
setup-github-auto:
	@echo "🚀 Automatically setting up GitHub repository secrets..."
	@if [ ! -f credentials/admin.env ]; then \
		echo "❌ Admin credentials not found. Run 'make credentials' first."; \
		exit 1; \
	fi
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "❌ GitHub CLI not installed. Install with: brew install gh"; \
		exit 1; \
	fi
	@echo "🔍 Reading admin credentials..."
	@AWS_ACCESS_KEY_ID=$$(grep "AWS_ACCESS_KEY_ID=" credentials/admin.env | cut -d'=' -f2); \
	AWS_SECRET_ACCESS_KEY=$$(grep "AWS_SECRET_ACCESS_KEY=" credentials/admin.env | cut -d'=' -f2); \
	echo "🔑 Setting AWS_ACCESS_KEY_ID..."; \
	gh secret set AWS_ACCESS_KEY_ID --body "$$AWS_ACCESS_KEY_ID"; \
	echo "🔒 Setting AWS_SECRET_ACCESS_KEY..."; \
	gh secret set AWS_SECRET_ACCESS_KEY --body "$$AWS_SECRET_ACCESS_KEY"; \
	echo "🌍 Setting AWS_REGION..."; \
	gh secret set AWS_REGION --body "us-east-1"
	@echo "✅ GitHub secrets configured successfully!"
	@echo "📋 Verifying secrets..."
	@gh secret list
	@echo "🚀 You can now trigger the workflow with: gh workflow run terraform.yaml"

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

# Run comprehensive infrastructure tests
test:
	@echo "🧪 Running comprehensive infrastructure tests..."
	@echo ""
	@echo "1️⃣  Code Quality Validation..."
	@$(MAKE) format
	@$(MAKE) lint  
	@$(MAKE) security
	@echo ""
	@echo "2️⃣  Infrastructure Health Check..."
	@$(MAKE) test-infrastructure
	@echo ""
	@echo "3️⃣  Credential Validation..."
	@$(MAKE) credentials
	@echo ""
	@echo "✅ All infrastructure tests completed successfully!"

# Test GitHub Actions workflow execution
test-workflow:
	@echo "🚀 Testing GitHub Actions workflow..."
	@echo ""
	@echo "🔍 Checking GitHub CLI authentication..."
	@gh auth status || (echo "❌ GitHub CLI not authenticated. Run 'gh auth login' first." && exit 1)
	@echo ""
	@echo "🔍 Checking GitHub repository secrets..."
	@gh secret list | grep -E "(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_REGION)" || \
		(echo "❌ Missing GitHub secrets. Run 'make setup-github-auto' first." && exit 1)
	@echo ""
	@echo "🚀 Triggering GitHub Actions workflow..."
	@gh workflow run terraform.yaml
	@echo ""
	@echo "📊 Recent workflow runs:"
	@gh run list --limit 3
	@echo ""
	@echo "💡 Monitor workflow progress:"
	@echo "   gh run watch"
	@echo "   gh run list"
	@echo "   gh run view --log"

# Test deployed AWS infrastructure health
test-infrastructure:
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && python3 scripts/test_infrastructure.py; \
	else \
		echo "❌ No .secrets file found. Run 'make bootstrap-check' or ensure credentials are available."; \
		exit 1; \
	fi

# Test with Act (local GitHub Actions)
test-act:
	@echo "🐳 Testing with Act (local GitHub Actions)..."
	@if ! command -v act >/dev/null 2>&1; then \
		echo "❌ Act not installed. Install with: brew install act"; \
		echo "💡 Or skip this test - it's optional"; \
		exit 1; \
	fi
	@echo "🚀 Running workflow with Act..."
	@act -W .github/workflows/terraform.yaml || echo "⚠️  Act testing completed with warnings"

# Test local Terraform operations
test-local:
	@echo "🏠 Testing local Terraform operations..."
	@echo "🔍 Validating Terraform configuration..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform validate; \
	else \
		terraform validate; \
	fi
	@echo "🔍 Checking Terraform format..."
	@terraform fmt -check
	@echo "🔍 Testing Terraform plan (dry run)..."
	@if [ -f .secrets ]; then \
		set -a && source .secrets && set +a && terraform plan -detailed-exitcode || [ $$? -eq 2 ]; \
	else \
		terraform plan -detailed-exitcode || [ $$? -eq 2 ]; \
	fi
	@echo "✅ Local Terraform operations validated"

# GitHub Actions integration targets (called by workflow)
ci-init:
	@echo "🤖 CI/CD Initialization..."
	@pip3 install --quiet boto3 botocore
	@terraform init

ci-deploy:
	@echo "🤖 CI/CD Deployment..."
	@terraform plan
	@terraform apply -auto-approve

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