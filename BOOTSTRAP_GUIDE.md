# Bootstrap User Management Guide

This guide provides step-by-step instructions for managing the bootstrap user setup, including how to switch to AWS root account credentials from the CLI.

## 🔑 AWS Root Account CLI Setup

### Step 1: Get Root Account Access Keys

1. **Log into AWS Console** as the root user (using your AWS account email and password)
1. **Go to Security Credentials**:
   - Click on your account name (top right)
   - Select "Security credentials" from dropdown
1. **Create Access Keys**:
   - Scroll down to "Access keys" section
   - Click "Create access key"
   - Select "Command Line Interface (CLI)" use case
   - Check the confirmation box
   - Click "Create access key"
   - **IMPORTANT**: Download the .csv file or copy the keys immediately
   - Store these securely (they won't be shown again)

### Step 2: Configure AWS CLI with Root Credentials

#### Option A: Temporary Environment Variables (Recommended)

```bash
# Export root credentials for this session only
export AWS_ACCESS_KEY_ID="your_root_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_root_secret_access_key"
export AWS_DEFAULT_REGION="us-east-1"

# Verify root access
aws sts get-caller-identity
# Should show: "arn:aws:iam::ACCOUNT_ID:root"
```

#### Option B: AWS CLI Profile

```bash
# Create a root profile
aws configure --profile root
# Enter your root access keys when prompted

# Use the root profile
export AWS_PROFILE=root

# Verify root access
aws sts get-caller-identity --profile root
```

#### Option C: Temporary .secrets file

```bash
# Backup current .secrets
cp .secrets .secrets.backup

# Create temporary root .secrets
cat > .secrets << EOF
AWS_ACCESS_KEY_ID=your_root_access_key_id
AWS_SECRET_ACCESS_KEY=your_root_secret_access_key
AWS_DEFAULT_REGION=us-east-1
EOF

# Verify root access
aws sts get-caller-identity
```

## 🚨 Complete Bootstrap Reset Process

### Phase 1: Switch to Root Credentials

```bash
# Option A: Use environment variables (recommended)
export AWS_ACCESS_KEY_ID="your_root_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_root_secret_access_key"
export AWS_DEFAULT_REGION="us-east-1"

# Verify you're running as root
aws sts get-caller-identity
# Expected output: "arn:aws:iam::ACCOUNT_ID:root"
```

### Phase 2: Destroy Current Bootstrap Setup

```bash
# Destroy the broken bootstrap setup
make bootstrap-destroy

# This will:
# - Delete bootstrap-user and all access keys
# - Delete PaveBootstrapRole 
# - Delete BootstrapTerraformPolicy and PaveBootstrapPolicy
```

### Phase 3: Create New Bootstrap Setup

```bash
# Create proper bootstrap setup with correct permissions
make bootstrap-create

# This will:
# - Create bootstrap-user with proper tags
# - Create PaveBootstrapPolicy with full S3 permissions
# - Create PaveBootstrapRole
# - Generate new access keys
# - Display the new credentials
```

### Phase 4: Update Local Credentials

```bash
# Update .secrets with the NEW bootstrap credentials (displayed by bootstrap-create)
cat > .secrets << EOF
AWS_ACCESS_KEY_ID=NEW_BOOTSTRAP_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=NEW_BOOTSTRAP_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=us-east-1
EOF

# Clear root environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_PROFILE
```

### Phase 5: Verify the Fix

```bash
# Test the new bootstrap setup
make bootstrap-check

# Should show all green checkmarks:
# ✅ Running as bootstrap user
# ✅ Bootstrap user found
# ✅ Bootstrap role found  
# ✅ Permission check passed: List IAM users
# ✅ Permission check passed: List IAM roles
# ✅ Permission check passed: List S3 buckets
```

### Phase 6: Test Infrastructure Operations

```bash
# Now you can run normal operations
make init          # Initialize terraform
make plan          # Preview infrastructure changes
make apply         # Deploy infrastructure
```

## 🔒 Security Best Practices

### Root Account Cleanup

After completing the bootstrap setup:

1. **Delete Root Access Keys**:

   ```bash
   # List root access keys
   aws iam list-access-keys --profile root

   # Delete the root access keys
   aws iam delete-access-key --access-key-id YOUR_ROOT_KEY_ID --profile root
   ```

1. **Remove Root Credentials from CLI**:

   ```bash
   # Clear environment variables
   unset AWS_ACCESS_KEY_ID
   unset AWS_SECRET_ACCESS_KEY
   unset AWS_PROFILE

   # Remove root profile (if used)
   aws configure --profile root
   # Enter empty values to clear
   ```

1. **Enable MFA on Root Account** (via AWS Console)

### Bootstrap User Security

The new bootstrap setup includes:

- **Protected Resources**: Bootstrap user/role/policy are tagged and protected from deletion
- **Principle of Least Privilege**: Sufficient permissions for infrastructure management
- **Audit Trail**: All actions are logged in CloudTrail

## 🆘 Troubleshooting

### "Access Denied" Errors

If you get access denied errors during bootstrap operations:

1. **Verify Root Access**:

   ```bash
   aws sts get-caller-identity
   # Must show: "arn:aws:iam::ACCOUNT_ID:root"
   ```

1. **Check Region**:

   ```bash
   echo $AWS_DEFAULT_REGION
   # Should be: us-east-1
   ```

1. **Test Root Permissions**:

   ```bash
   aws iam list-users
   aws s3 ls
   ```

### "Entity Already Exists" Errors

If resources already exist:

1. **Run destroy first**:

   ```bash
   make bootstrap-destroy
   ```

1. **Then recreate**:

   ```bash
   make bootstrap-create
   ```

### Emergency Recovery

If you get locked out completely:

1. **Use AWS Console** with root account
1. **Manually delete resources**:
   - IAM > Users > bootstrap-user (delete)
   - IAM > Roles > PaveBootstrapRole (delete)
   - IAM > Policies > BootstrapTerraformPolicy (delete)
   - IAM > Policies > PaveBootstrapPolicy (delete)
1. **Run bootstrap-create** with root credentials

## 📋 Quick Reference Commands

```bash
# Complete reset process (as root)
export AWS_ACCESS_KEY_ID="root_key"
export AWS_SECRET_ACCESS_KEY="root_secret"
aws sts get-caller-identity  # Verify root
make bootstrap-destroy       # Clean slate
make bootstrap-create        # Create proper setup
# Update .secrets with new bootstrap credentials
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
make bootstrap-check         # Verify success
```
