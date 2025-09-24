# Security Scanning Documentation

This repository implements **professional-grade security scanning** using multiple industry-standard tools to ensure comprehensive security coverage across all aspects of the infrastructure and code.

## 🔒 Security Scanning Overview

### Multi-Layer Security Approach

Our security scanning strategy employs multiple specialized tools:

1. **🐍 Bandit** - Python security vulnerability scanner
2. **🏗️ Checkov** - Infrastructure as Code (Terraform) security scanner  
3. **📦 Safety** - Python dependency vulnerability scanner
4. **🔍 Custom Secret Detection** - Enhanced credential/secret pattern matching
5. **🔐 File Permission Auditing** - Secure file permission verification
6. **📝 Configuration Validation** - .gitignore and security config checks

### Why Multiple Tools?

Each tool specializes in different attack vectors:
- **Bandit**: Catches Python-specific security antipatterns (SQL injection, hardcoded passwords, etc.)
- **Checkov**: Identifies infrastructure misconfigurations (overly permissive IAM, unencrypted storage, etc.)
- **Safety**: Detects known vulnerabilities in Python dependencies
- **Secret Detection**: Finds accidentally committed credentials or API keys
- **Permission Auditing**: Prevents privilege escalation through file system misconfigurations

## 🚀 Quick Start

### Local Security Scanning

```bash
# Run all security scans
make security

# Run in quiet mode (only show issues)
make security QUIET=1

# Run comprehensive validation including security
make validate
```

### Individual Tool Usage

```bash
# Python security scan
bandit -r . --exclude .git,.terraform,.venv

# Infrastructure security scan  
checkov -d . --framework terraform

# Dependency vulnerability scan
safety check

# Custom comprehensive scan
python3 scripts/security_scan.py
```

## 📊 Understanding Results

### Security Scan Output

```bash
🔒 Starting comprehensive security scan...
🐍 Running Bandit (Python security scanner)...
✅ Bandit: No Python security issues found
🏗️ Running Checkov (Infrastructure security scanner)...  
❌ Checkov found 21 infrastructure security issues
📦 Running Safety (Dependency vulnerability scanner)...
✅ Safety: No vulnerable dependencies found
🔍 Running enhanced secret detection...
⚠️ Secret detection found 3 potential secrets
🔐 Checking file permissions...
✅ File permissions: All sensitive files properly secured
❌ Security scan failed - 24 issues found
📊 Summary: 5 tools run, 0 skipped
📝 Detailed results saved to logs/security-scan-results.json
```

### Report Files

After running security scans, detailed reports are generated:

- `logs/security-scan-results.json` - Comprehensive JSON report with all findings
- `logs/bandit-report.json` - Detailed Bandit findings
- `logs/checkov-report.json` - Infrastructure security issues
- `logs/safety-report.json` - Dependency vulnerabilities

### Understanding Severity Levels

#### 🚨 Critical Issues (Build-Blocking)
- Hardcoded AWS credentials
- SQL injection vulnerabilities  
- Public S3 buckets with sensitive data
- Known high-severity CVEs in dependencies

#### ⚠️ High Priority Issues
- Overly permissive IAM policies
- Unencrypted data storage
- Missing security headers
- Medium-severity dependency vulnerabilities

#### ℹ️ Low Priority Issues  
- Coding style security recommendations
- Minor configuration improvements
- Informational security notices

## 🔧 Tool-Specific Configuration

### Bandit Configuration

Bandit scans Python code for security issues. Key settings:

```bash
# Skip certain checks for scripts
--skip B101,B601  # Allow assert statements and shell usage in scripts

# Exclude directories
--exclude .git,.terraform,.venv,__pycache__
```

**Common Bandit Issues:**
- `B108`: Hardcoded temporary file usage
- `B501`: Requests with verify=False
- `B506`: Use of YAML load without Loader

### Checkov Configuration

Checkov analyzes Terraform for security misconfigurations:

```bash
# Focus on Terraform files
--framework terraform

# Output formats
--output json --output cli

# Quiet mode for CI/CD
--quiet
```

**Common Checkov Issues:**
- `CKV_AWS_63`: IAM policies with wildcard actions
- `CKV_AWS_288`: IAM policies allowing data exfiltration  
- `CKV_AWS_18`: S3 buckets without access logging

### Safety Configuration

Safety checks Python dependencies against vulnerability databases:

```bash
# Check requirements.txt
safety check --file requirements.txt

# JSON output for automation
safety check --json
```

### Custom Secret Detection

Our enhanced secret detection looks for:

```python
# Actual credential patterns (not just parameter names)
AKIA[0-9A-Z]{16}                    # AWS Access Keys
aws_secret_access_key.*[A-Za-z0-9+/]{40}  # AWS Secret Keys  
api_key.*[A-Za-z0-9]{32,}           # API Keys
(password|secret|token).*[A-Za-z0-9+/=]{20,}  # Generic secrets
```

**Excluded Patterns:**
- Template strings (`YOUR_API_KEY`, `REPLACE_WITH_ACTUAL`)
- Documentation examples
- Test fixtures
- Comments and documentation

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Our security workflow (`.github/workflows/security.yml`) runs:

1. **On Every Push/PR** - Full security scan
2. **Daily Scheduled Scans** - Catch new vulnerabilities
3. **Manual Triggers** - For security audits

### Workflow Features

- **Parallel Execution** - Multiple tools run simultaneously
- **Artifact Upload** - Reports saved for 30 days
- **PR Comments** - Security results posted to pull requests
- **Build Blocking** - Critical issues fail the build
- **Flexible Scanning** - Can run individual tools or full suite

### Setting Up Secrets

For enhanced security scanning, configure these GitHub secrets:

```bash
# Optional - for Snyk integration
SNYK_TOKEN=your_snyk_api_token

# For AWS resource scanning (if needed)
AWS_ACCESS_KEY_ID=readonly_scanner_key
AWS_SECRET_ACCESS_KEY=readonly_scanner_secret
```

## 🛠️ Troubleshooting

### Common Issues

#### "Command not found" errors
```bash
# Ensure all tools are installed
pip install -r requirements.txt

# Verify tools are available
bandit --version
checkov --version  
safety --version
```

#### False Positive Secrets
```bash
# Add patterns to exclude in scripts/security_scan.py
exclude_patterns = [
    "YOUR_", "REPLACE_", "TEMPLATE", "EXAMPLE",
    "bootstrap-credentials", ".pyi", "# ", "//"
]
```

#### Checkov Infrastructure Issues
```bash
# Skip specific checks if they don't apply
checkov -d . --skip-check CKV_AWS_63,CKV_AWS_288

# Or use checkov configuration file
# .checkov.yml with skip patterns
```

### Performance Optimization

For large repositories:

```bash
# Exclude unnecessary directories
--exclude .git,.terraform,.venv,node_modules,__pycache__

# Use parallel processing
export CHECKOV_RUNNER_THREADS=4

# Focus on changed files only (in CI)
checkov --framework terraform $(git diff --name-only --diff-filter=AM | grep '\.tf$')
```

## 📈 Security Metrics

### Key Performance Indicators

Track these security metrics:

- **Mean Time to Detection (MTTD)** - How quickly issues are found
- **Mean Time to Resolution (MTTR)** - How quickly issues are fixed  
- **Security Debt** - Total outstanding security issues
- **Vulnerability Density** - Issues per lines of code
- **False Positive Rate** - Accuracy of security tools

### Reporting Dashboard

Consider integrating with:
- **GitHub Security** - Built-in vulnerability alerts
- **Snyk** - Dependency vulnerability management
- **SonarQube** - Code quality and security metrics
- **DefectDojo** - Security findings aggregation

## 🔐 Security Best Practices

### Development Workflow

1. **Pre-commit Hooks** - Run basic security checks before commits
2. **Branch Protection** - Require security scans to pass before merge
3. **Regular Updates** - Keep security tools and dependencies current
4. **Security Training** - Educate team on secure coding practices

### Infrastructure Security

1. **Least Privilege** - Minimal IAM permissions
2. **Defense in Depth** - Multiple security layers  
3. **Regular Audits** - Periodic security reviews
4. **Incident Response** - Plan for security breaches

### Monitoring and Alerting

1. **Real-time Alerts** - Immediate notification of critical issues
2. **Trend Analysis** - Track security posture over time
3. **Compliance Reporting** - Regular security status reports
4. **Automated Remediation** - Fix common issues automatically

## 📚 Additional Resources

### Documentation
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Checkov Documentation](https://www.checkov.io/1.Welcome/Quick%20Start.html)
- [Safety Documentation](https://pyup.io/safety/)
- [OWASP Security Guidelines](https://owasp.org/)

### Training
- [Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Infrastructure Security](https://docs.aws.amazon.com/security/)
- [Python Security](https://python-security.readthedocs.io/)

### Tools and Services
- [GitHub Advanced Security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)  
- [Snyk](https://snyk.io/) - Developer-first security platform
- [Semgrep](https://semgrep.dev/) - Static analysis at scale
- [SonarQube](https://www.sonarqube.org/) - Code quality and security

---

## 🎯 Next Steps

1. **Enable GitHub Advanced Security** - If you have GitHub Pro/Enterprise
2. **Add Snyk Integration** - For enhanced dependency scanning
3. **Implement Pre-commit Hooks** - Catch issues before they reach the repo  
4. **Set up Security Monitoring** - Real-time alerting for new vulnerabilities
5. **Regular Security Audits** - Periodic comprehensive security reviews

For questions or improvements to this security setup, please create an issue or contact the infrastructure team.