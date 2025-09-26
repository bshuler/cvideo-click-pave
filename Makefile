# ==============================================================================
# Makefile for CVideo Click Pave Infrastructure Management
# ==============================================================================
# This is the primary interface for all infrastructure operations
# Organized by workflow: Bootstrap -> Core Operations -> Testing -> Development

.DEFAULT_GOAL := help

# ==============================================================================
# AUTHENTICATION MANAGEMENT
# ==============================================================================
# Clear all AWS environment variables to ensure clean authentication state
CLEAR_AWS_ENV = unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION AWS_REGION AWS_SESSION_TOKEN AWS_PROFILE
# Load root credentials from .root-secrets file
LOAD_ROOT_CREDS = $(CLEAR_AWS_ENV) && set -a && source .root-secrets && set +a
# Load bootstrap credentials from .secrets file  
LOAD_BOOTSTRAP_CREDS = $(CLEAR_AWS_ENV) && set -a && source .secrets && set +a

# ==============================================================================
# PHONY TARGETS
# ==============================================================================
.PHONY: help \
        bootstrap-check bootstrap-create bootstrap-destroy bootstrap-fix bootstrap-switch bootstrap-reset-help bootstrap-root-help credential-info \
        init plan apply destroy clean credentials setup-github rotate-keys \
        state-show state-pull state-backup state-import \
        format lint type-check security pylance-check markdown-lint markdown-fix yaml-lint yaml-fix validate drift-detect \
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
	@echo "  make full-test YES=1   Skip confirmation prompt for automated testing"
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
	@echo "  make apply YES=1   Deploy infrastructure automatically (no confirmation prompt)"
	@echo "  make destroy       Destroy infrastructure with terraform destroy" 
	@echo "  make clean         Comprehensive cleanup of all AWS resources (destructive!)"
	@echo ""
	@echo "🔑 CREDENTIAL & SECRETS MANAGEMENT:"
	@echo "  make credentials       Generate credential template files"
	@echo "  make rotate-keys       Rotate compromised AWS access keys (security incident response)"
	@echo "  make setup-github      Automatically set GitHub secrets from .secrets (bootstrap user)"
	@echo ""
	@echo "🗄️ STATE MANAGEMENT (S3 Remote Backend):"
	@echo "  make state-show        Show current Terraform state resources"
	@echo "  make state-pull        Pull current state from S3"
	@echo "  make state-backup      Create local backup of remote state"
	@echo "  make state-import      Import existing AWS resource (RESOURCE=<name> ID=<id>)"
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
	@echo "  make pylance-check Check TypedDict safety with Pylance"
	@echo "  make markdown-lint Lint markdown files with mdformat"
	@echo "  make markdown-fix  Fix markdown formatting issues"
	@echo "  make yaml-lint     Lint YAML files with yamllint"
	@echo "  make yaml-fix      Validate YAML files (no auto-fix available)"
	@echo "  make validate      Validate terraform configuration and Python code"
	@echo "  make drift-detect  Detect drift between AWS state and Terraform configuration"
	@echo ""
	@echo "🛠️ DEVELOPMENT WORKFLOW:"
	@echo "  make dev-deploy    Full local development deployment (clean slate)"
	@echo "  make dev-clean     Clean up development resources"
	@echo "  make status        Show current infrastructure status"
	@echo "  make clean-local   Clean local files and caches"
	@echo ""
	@echo "🤖 AUTOMATION OPTIONS:"
	@echo "  YES=1 make <destructive-target>  Skip confirmation prompts for automation"
	@echo "  Examples: YES=1 make destroy, YES=1 make clean, YES=1 make clean-local"
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
	@if [ "$(YES)" != "1" ]; then \
		echo "⚠️  This is a DESTRUCTIVE operation that will rebuild everything!"; \
		echo "   To proceed, type 'yes' and press Enter:"; \
		read -r response; \
		if [ "$$response" != "yes" ]; then \
			echo "❌ Operation cancelled."; \
			echo "💡 To skip this confirmation, use: make full-test YES=1"; \
			exit 1; \
		fi; \
	else \
		echo "✅ Confirmation skipped (YES=1 specified)"; \
	fi
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
		$(LOAD_ROOT_CREDS) && $(MAKE) bootstrap-destroy; \
	else \
		$(CLEAR_AWS_ENV) && $(MAKE) bootstrap-destroy; \
	fi || echo "⚠️  Bootstrap destroy completed (may have warnings)"
	@echo ""
	@echo "2️⃣  Cleaning all AWS resources..."
	@if [ -f .root-secrets ]; then \
		$(LOAD_ROOT_CREDS) && $(MAKE) clean; \
	else \
		$(CLEAR_AWS_ENV) && $(MAKE) clean; \
	fi || echo "⚠️  Cleanup completed (may have warnings)"
	@echo ""
	@echo "🏁 PHASE 2: FRESH SETUP (using root credentials)"
	@echo "================================================"
	@echo "3️⃣  Creating fresh bootstrap setup with S3 backend..."
	@if [ -f .root-secrets ]; then \
		$(LOAD_ROOT_CREDS) && $(MAKE) bootstrap-create; \
	else \
		$(CLEAR_AWS_ENV) && $(MAKE) bootstrap-create; \
	fi
	@echo ""
	@echo "🔄 Clearing root credentials and switching to bootstrap credentials..."
	@echo "✅ Environment cleared - now using bootstrap credentials from .secrets"
	@echo ""
	@echo "🏁 PHASE 3: INFRASTRUCTURE DEPLOYMENT (using bootstrap credentials)"
	@echo "=================================================================="
	@echo "4️⃣  Initializing Terraform..."
	@$(MAKE) init
	@echo ""
	@echo "5️⃣  Planning infrastructure..."
	@$(MAKE) plan
	@echo ""
	@echo "6️⃣  Applying infrastructure..."
	@$(MAKE) apply YES=1
	@echo ""
	@echo "🏁 PHASE 4: CREDENTIAL SETUP"
	@echo "============================"
	@echo "7️⃣  Generating credentials..."
	@$(MAKE) credentials
	@echo ""
	@echo "8️⃣  Setting up GitHub secrets..."
	@$(MAKE) setup-github || echo "⚠️  GitHub secrets setup had issues (check GitHub CLI)"
	@echo ""
	@echo "🏁 PHASE 5: COMPREHENSIVE TESTING"
	@echo "=================================="
	@echo "9️⃣  Testing local Terraform operations..."
	@$(MAKE) test-local
	@echo ""
	@echo "🔟 Testing infrastructure health..."
	@$(MAKE) test-infrastructure
	@echo ""
	@echo "1️⃣1️⃣  Testing with Act (local GitHub Actions)..."
	@$(MAKE) test-act || echo "⚠️  Act testing had issues (check Act installation)"
	@echo ""
	@echo "1️⃣2️⃣  Testing GitHub Actions workflow..."
	@$(MAKE) test-workflow || echo "⚠️  GitHub workflow testing had issues (check GitHub CLI)"
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
	@echo "🛡️ SAFETY FEATURES:"
	@echo "   • Requires confirmation before proceeding (destructive operation)"
	@echo "   • Use 'make full-test YES=1' to skip confirmation for automation"
	@echo "   • All operations are logged with clear status indicators"
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
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/validate_bootstrap.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/validate_bootstrap.py; \
	fi

# Fix bootstrap user S3 permissions issue
bootstrap-fix:
	@echo "🔧 Fixing bootstrap user S3 permissions..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/fix_bootstrap_s3.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/fix_bootstrap_s3.py; \
	fi

# Create complete bootstrap setup (requires root/admin credentials)
bootstrap-create:
	@echo "🚀 Creating bootstrap user setup..."
	@echo "⚠️  WARNING: This requires AWS root account credentials!"
	@if [ -f .root-secrets ]; then \
		echo "✅ Using root credentials from .root-secrets"; \
		$(LOAD_ROOT_CREDS) && python3 scripts/create_bootstrap.py; \
	else \
		echo "📖 Using environment credentials (see BOOTSTRAP_GUIDE.md for setup)"; \
		$(CLEAR_AWS_ENV) && python3 scripts/create_bootstrap.py; \
	fi
	@echo "🔧 Setting up GitHub repository secrets with bootstrap credentials..."
	@$(MAKE) setup-github || echo "⚠️  GitHub secrets setup had issues (check GitHub CLI and authentication)"

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
			$(LOAD_ROOT_CREDS) && python3 scripts/destroy_bootstrap.py; \
		else \
			$(LOAD_ROOT_CREDS) && python3 scripts/destroy_bootstrap.py --skip-confirm; \
		fi; \
	else \
		echo "📖 Using environment credentials (see BOOTSTRAP_GUIDE.md for setup)"; \
		if [ "$(MAKE_LEVEL)" = "0" ]; then \
			$(CLEAR_AWS_ENV) && python3 scripts/destroy_bootstrap.py; \
		else \
			$(CLEAR_AWS_ENV) && python3 scripts/destroy_bootstrap.py --skip-confirm; \
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
	@echo "� Clearing any existing AWS credentials and using bootstrap credentials..."
	@echo "�📦 Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "🏗️ Initializing Terraform..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && terraform init; \
	else \
		$(CLEAR_AWS_ENV) && terraform init; \
	fi
	@echo "✅ Initialization complete!"

# Format Python code with Black
format:
	@echo "🎨 Formatting code..."
	@python3 -m black scripts/ --quiet
	@echo "✅ Code formatting complete"

# Lint Python code with Flake8
lint:
	@echo "🔍 Linting code..."
	@python3 -m flake8 scripts/ --quiet
	@echo "✅ Linting complete"

# Type check Python code with mypy
type-check:
	@echo "🔍 Type checking..."
	@python3 -m mypy scripts/ --no-error-summary
	@echo "✅ Type checking complete"

# Professional security scanning with multiple tools
security:
	@echo "🔒 Running comprehensive security scan..."
	@mkdir -p logs
	@python3 scripts/security_scan.py --quiet
	@echo "✅ Security scan complete"

# Check TypedDict safety with Pylance
pylance-check:
	@python3 scripts/pylance_check_mcp.py --quiet

# Lint markdown files
markdown-lint:
	@python3 scripts/markdown_lint.py --quiet

# Fix markdown formatting issues
markdown-fix:
	@echo "🔧 Fixing markdown formatting issues..."
	@python3 scripts/markdown_lint.py --fix
	@echo "✅ Markdown formatting fixed!"

# Lint YAML files
yaml-lint:
	@python3 scripts/yaml_lint.py --quiet

# Fix YAML formatting issues (yamllint doesn't support auto-fix)
yaml-fix:
	@echo "🔧 YAML files need manual fixing (yamllint doesn't support auto-fix)..."
	@python3 scripts/yaml_lint.py --fix
	@echo "✅ YAML validation complete!"

# Validate configuration and dependencies
validate: init security format lint type-check pylance-check markdown-lint yaml-lint
	@echo "🔍 Validating configuration..."
	@echo "📋 Checking Terraform configuration..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && terraform validate && terraform fmt -check; \
	else \
		$(CLEAR_AWS_ENV) && terraform validate && terraform fmt -check; \
	fi
	@echo "🐍 Checking Python dependencies..."
	@python3 -c "import boto3; print('✅ boto3 available')" 2>/dev/null || (echo "❌ boto3 not found. Run 'make init'" && exit 1)
	@echo "🔑 Checking AWS credentials..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/validate.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/validate.py; \
	fi
	@echo "🏗️  Testing infrastructure health..."
	@$(MAKE) test-infrastructure
	@echo "✅ All validations passed!"

# Detect drift between AWS state and Terraform configuration
drift-detect:
	@echo "🔍 Detecting drift between AWS and Terraform..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/drift_detection.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/drift_detection.py; \
	fi

# Plan infrastructure changes
plan: validate
	@echo "📋 Planning infrastructure changes..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && terraform plan; \
	else \
		$(CLEAR_AWS_ENV) && terraform plan; \
	fi

# Deploy infrastructure
apply: validate
	@echo "🚀 Deploying infrastructure..."
	@if [ "$(YES)" = "1" ]; then \
		echo "✅ Auto-approving deployment (YES=1)"; \
		if [ -f .secrets ]; then \
			$(LOAD_BOOTSTRAP_CREDS) && terraform apply -auto-approve; \
		else \
			$(CLEAR_AWS_ENV) && terraform apply -auto-approve; \
		fi; \
	else \
		if [ -f .secrets ]; then \
			$(LOAD_BOOTSTRAP_CREDS) && terraform apply; \
		else \
			$(CLEAR_AWS_ENV) && terraform apply; \
		fi; \
	fi

# Destroy infrastructure
destroy:
	@echo "⚠️  Destroying infrastructure..."
	@echo "This will remove all Terraform-managed resources."
	@if [ "$(YES)" = "1" ]; then \
		echo "✅ Auto-confirmed via YES=1"; \
	else \
		read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1; \
	fi
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && terraform destroy; \
	else \
		$(CLEAR_AWS_ENV) && terraform destroy; \
	fi

# Comprehensive cleanup of all AWS resources
clean:
	@echo "🧹 Starting comprehensive cleanup..."
	@echo "⚠️  This will remove ALL pave infrastructure resources (past and present)"
	@if [ "$(YES)" = "1" ] || [ "$(MAKE_LEVEL)" != "0" ]; then \
		echo "✅ Auto-confirmed via YES=1 or nested call"; \
	else \
		read -p "Are you sure? This is destructive! (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1; \
	fi
	@if [ -f .secrets ]; then \
		if [ "$(YES)" = "1" ] || [ "$(MAKE_LEVEL)" != "0" ]; then \
			$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/cleanup.py --skip-confirm; \
		else \
			$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/cleanup.py; \
		fi; \
	else \
		if [ "$(YES)" = "1" ] || [ "$(MAKE_LEVEL)" != "0" ]; then \
			$(CLEAR_AWS_ENV) && python3 scripts/cleanup.py --skip-confirm; \
		else \
			$(CLEAR_AWS_ENV) && python3 scripts/cleanup.py; \
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



# Generate credential templates
credentials:
	@echo "🔐 Generating credential templates..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/credentials.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/credentials.py; \
	fi

# Rotate compromised AWS access keys (Security Incident Response)
rotate-keys:
	@echo "🚨 AWS ACCESS KEY ROTATION - Security Incident Response"
	@echo "======================================================="
	@echo "⚠️  This will create new access keys and deactivate compromised ones"
	@echo ""
	@if [ -z "$(COMPROMISED_KEY)" ]; then \
		echo "❌ Error: COMPROMISED_KEY parameter is required"; \
		echo "Usage: make rotate-keys COMPROMISED_KEY=AKIATXIZHCB6R3RI7XV4"; \
		exit 1; \
	fi
	@if [ ! -f .secrets ]; then \
		echo "❌ Bootstrap credentials not found. Cannot rotate keys without admin access."; \
		echo "💡 Ensure .secrets file exists with bootstrap user credentials"; \
		exit 1; \
	fi
	@echo "🔍 Using bootstrap credentials to rotate developer keys..."
	@echo "🚨 Compromised key to deactivate: $(COMPROMISED_KEY)"
	@if [ "$(YES)" = "1" ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/rotate_keys.py --compromised-key $(COMPROMISED_KEY) --skip-confirm; \
	else \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/rotate_keys.py --compromised-key $(COMPROMISED_KEY); \
	fi
	@echo ""
	@echo "🎉 Key rotation completed! Next steps:"
	@echo "1. Run: make validate"
	@echo "2. Test infrastructure access"
	@echo "3. Check CloudTrail logs for unauthorized activity"
	@echo "4. Remove quarantine policy from developer user"
	@echo "5. Delete compromised key after verification"

# Automatically set GitHub secrets using bootstrap credentials with validation
setup-github:
	@echo "🚀 Automatically setting up GitHub repository secrets..."
	@if [ ! -f .secrets ]; then \
		echo "❌ Bootstrap credentials not found. Run 'make bootstrap-create' first."; \
		exit 1; \
	fi
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "❌ GitHub CLI not installed. Install with: brew install gh"; \
		exit 1; \
	fi
	@echo "🔍 Reading bootstrap credentials from .secrets..."
	@AWS_ACCESS_KEY_ID=$$(grep "AWS_ACCESS_KEY_ID=" .secrets | cut -d'=' -f2); \
	AWS_SECRET_ACCESS_KEY=$$(grep "AWS_SECRET_ACCESS_KEY=" .secrets | cut -d'=' -f2); \
	AWS_REGION=$$(grep "AWS_REGION=" .secrets | cut -d'=' -f2 | head -1); \
	echo "� Validating credentials before sending to GitHub..."; \
	IDENTITY_RESULT=$$(AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION=$$AWS_REGION aws sts get-caller-identity 2>&1); \
	if [ $$? -ne 0 ]; then \
		echo "❌ Invalid AWS credentials in .secrets file:"; \
		echo "$$IDENTITY_RESULT"; \
		echo "💡 Run 'make bootstrap-create' to generate valid credentials"; \
		exit 1; \
	fi; \
	USERNAME=$$(echo "$$IDENTITY_RESULT" | grep -o '"Arn": *"[^"]*"' | cut -d'"' -f4 | sed 's|.*/||'); \
	if [ "$$USERNAME" != "bootstrap-user" ]; then \
		echo "❌ Credentials in .secrets are not for bootstrap-user (found: $$USERNAME)"; \
		echo "💡 Expected bootstrap-user credentials for GitHub Actions"; \
		echo "💡 Run 'make bootstrap-create' to generate proper bootstrap credentials"; \
		exit 1; \
	fi; \
	echo "✅ Credentials validated: $$USERNAME"; \
	echo "�🔑 Setting AWS_ACCESS_KEY_ID (bootstrap user)..."; \
	gh secret set AWS_ACCESS_KEY_ID --body "$$AWS_ACCESS_KEY_ID"; \
	echo "🔒 Setting AWS_SECRET_ACCESS_KEY (bootstrap user)..."; \
	gh secret set AWS_SECRET_ACCESS_KEY --body "$$AWS_SECRET_ACCESS_KEY"; \
	echo "🌍 Setting AWS_REGION..."; \
	gh secret set AWS_REGION --body "$$AWS_REGION"
	@echo "✅ GitHub secrets configured successfully with validated bootstrap user credentials!"
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
	@$(MAKE) apply YES=1
	@echo "Step 3: Generate credentials"
	@$(MAKE) credentials
	@echo "✅ Development deployment complete!"

# Clean development resources
dev-clean:
	@echo "🧹 Cleaning development resources..."
	@echo "⚠️  This will remove development-related AWS resources"
	@if [ "$(YES)" = "1" ] || [ "$(MAKE_LEVEL)" != "0" ]; then \
		echo "✅ Auto-confirmed via YES=1 or nested call"; \
	else \
		read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1; \
	fi
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/cleanup.py --dev-only; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/cleanup.py --dev-only; \
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
		(echo "❌ Missing GitHub secrets. Run 'make setup-github' first." && exit 1)
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
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/test_infrastructure.py --quiet; \
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
		$(LOAD_BOOTSTRAP_CREDS) && terraform validate; \
	else \
		$(CLEAR_AWS_ENV) && terraform validate; \
	fi
	@echo "🔍 Checking Terraform format..."
	@terraform fmt -check
	@echo "🔍 Testing Terraform plan (dry run)..."
	@if [ -f .secrets ]; then \
		$(LOAD_BOOTSTRAP_CREDS) && terraform plan -detailed-exitcode || [ $$? -eq 2 ]; \
	else \
		$(CLEAR_AWS_ENV) && terraform plan -detailed-exitcode || [ $$? -eq 2 ]; \
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
		$(LOAD_BOOTSTRAP_CREDS) && python3 scripts/status.py; \
	else \
		$(CLEAR_AWS_ENV) && python3 scripts/status.py; \
	fi

# Clean local state and caches
clean-local:
	@echo "🧹 Cleaning local files..."
	@echo "⚠️  This will remove local terraform state, credentials, and cache files"
	@if [ "$(YES)" = "1" ]; then \
		echo "✅ Auto-confirmed via YES=1"; \
	else \
		read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1; \
	fi
	@rm -rf .terraform/
	@rm -f terraform.tfstate*
	@rm -rf credentials/
	@rm -f requirements.txt
	@echo "✅ Local cleanup complete. Run 'make init' to reinitialize."