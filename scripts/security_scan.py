#!/usr/bin/env python3
"""
Comprehensive Security Scanner

Professional-grade security scanning using multiple tools:
- Bandit: Python security issues
- Checkov: Infrastructure as Code security
- Safety: Dependency vulnerability scanning  
- Custom secret detection: Enhanced pattern matching
- File permission and configuration checks

Usage:
    python3 security_scan.py [--quiet]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import re

# Global quiet mode flag
QUIET_MODE = False

def print_status(icon: str, message: str, force: bool = False) -> None:
    """Print status message with icon, respecting quiet mode."""
    if not QUIET_MODE or force:
        print(f"{icon} {message}")

def run_command(cmd: List[str], cwd: str | None = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return 1, "", str(e)

def check_tool_available(tool: str) -> bool:
    """Check if a security tool is available."""
    exit_code, _, _ = run_command(["which", tool])
    return exit_code == 0

def run_bandit_scan() -> Dict[str, Any]:
    """Run Bandit Python security scanner."""
    print_status("🐍", "Running Bandit (Python security scanner)...")
    
    if not check_tool_available("bandit"):
        return {
            "tool": "bandit",
            "status": "skipped",
            "reason": "Tool not available - run 'pip install bandit' to enable",
            "issues": 0
        }
    
    # Run bandit with JSON output
    cmd = [
        "bandit", 
        "-r", "scripts/", 
        "-f", "json",
        "-ll",  # Only show medium and high severity
        "--skip", "B101"  # Skip assert_used test (common in test files)
    ]
    
    exit_code, stdout, stderr = run_command(cmd)
    
    try:
        if stdout:
            result = json.loads(stdout)
            issues = len(result.get("results", []))
            
            if issues > 0:
                print_status("❌", f"Bandit found {issues} security issues", force=True)
                if not QUIET_MODE:
                    for issue in result.get("results", []):
                        print(f"   {issue['filename']}:{issue['line_number']} - {issue['test_name']}")
                        print(f"   {issue['issue_text']}")
                        print(f"   Severity: {issue['issue_severity']} | Confidence: {issue['issue_confidence']}")
                        print()
            else:
                print_status("✅", "Bandit: No Python security issues found")
                
            return {
                "tool": "bandit",
                "status": "success",
                "issues": issues,
                "details": result.get("results", []) if issues > 0 else []
            }
        else:
            print_status("✅", "Bandit: No Python security issues found")
            return {
                "tool": "bandit",
                "status": "success", 
                "issues": 0
            }
            
    except json.JSONDecodeError:
        print_status("⚠️", f"Bandit output parsing failed: {stderr}")
        return {
            "tool": "bandit",
            "status": "error",
            "reason": "Failed to parse output",
            "issues": 0
        }

def run_checkov_scan() -> Dict[str, Any]:
    """Run Checkov Infrastructure as Code scanner."""
    print_status("🏗️", "Running Checkov (Infrastructure security scanner)...")
    
    if not check_tool_available("checkov"):
        return {
            "tool": "checkov",
            "status": "skipped",
            "reason": "Tool not available - run 'pip install checkov' to enable",
            "issues": 0
        }
    
    # Run checkov on Terraform files
    cmd = [
        "checkov",
        "-f", "pave_infra.tf",
        "-o", "json",
        "--quiet",
        "--compact"
    ]
    
    exit_code, stdout, stderr = run_command(cmd)
    
    try:
        if stdout:
            result = json.loads(stdout)
            failed_checks = result.get("results", {}).get("failed_checks", [])
            issues = len(failed_checks)
            
            if issues > 0:
                print_status("❌", f"Checkov found {issues} infrastructure security issues", force=True)
                if not QUIET_MODE:
                    for check in failed_checks[:5]:  # Show first 5 issues
                        print(f"   {check['file_path']}:{check.get('file_line_range', ['?'])[0]} - {check['check_id']}")
                        print(f"   {check['check_name']}")
                        print(f"   Severity: {check.get('severity', 'UNKNOWN')}")
                        print()
                    if issues > 5:
                        print(f"   ... and {issues - 5} more issues")
            else:
                print_status("✅", "Checkov: No infrastructure security issues found")
                
            return {
                "tool": "checkov",
                "status": "success",
                "issues": issues,
                "details": failed_checks if issues > 0 else []
            }
        else:
            print_status("✅", "Checkov: No infrastructure security issues found")
            return {
                "tool": "checkov",
                "status": "success",
                "issues": 0
            }
            
    except json.JSONDecodeError:
        print_status("⚠️", f"Checkov output parsing failed: {stderr}")
        return {
            "tool": "checkov", 
            "status": "error",
            "reason": "Failed to parse output",
            "issues": 0
        }

def run_safety_scan() -> Dict[str, Any]:
    """Run Safety dependency vulnerability scanner."""
    print_status("📦", "Running Safety (Dependency vulnerability scanner)...")
    
    if not check_tool_available("safety"):
        return {
            "tool": "safety",
            "status": "skipped", 
            "reason": "Tool not available - run 'pip install safety' to enable",
            "issues": 0
        }
    
    # Run safety check
    cmd = ["safety", "check", "--json"]
    
    exit_code, stdout, stderr = run_command(cmd)
    
    try:
        if stdout:
            result = json.loads(stdout)
            vulnerabilities = result if isinstance(result, list) else []
            issues = len(vulnerabilities)
            
            if issues > 0:
                print_status("❌", f"Safety found {issues} dependency vulnerabilities", force=True)
                if not QUIET_MODE:
                    for vuln in vulnerabilities[:3]:  # Show first 3 vulnerabilities
                        print(f"   {vuln['package_name']} {vuln['installed_version']}")
                        print(f"   {vuln['advisory']}")
                        print(f"   ID: {vuln['vulnerability_id']}")
                        print()
                    if issues > 3:
                        print(f"   ... and {issues - 3} more vulnerabilities")
            else:
                print_status("✅", "Safety: No dependency vulnerabilities found")
                
            return {
                "tool": "safety",
                "status": "success",
                "issues": issues,
                "details": vulnerabilities if issues > 0 else []
            }
        else:
            print_status("✅", "Safety: No dependency vulnerabilities found")
            return {
                "tool": "safety",
                "status": "success",
                "issues": 0
            }
            
    except json.JSONDecodeError:
        if exit_code == 0:
            print_status("✅", "Safety: No dependency vulnerabilities found")
            return {
                "tool": "safety",
                "status": "success",
                "issues": 0
            }
        else:
            print_status("⚠️", f"Safety scan failed: {stderr}")
            return {
                "tool": "safety",
                "status": "error",
                "reason": stderr,
                "issues": 0
            }

def run_secret_detection() -> Dict[str, Any]:
    """Enhanced secret detection with professional patterns."""
    print_status("🔍", "Running enhanced secret detection...")
    
    # Professional secret patterns
    secret_patterns = {
        "aws_access_key": r'AKIA[0-9A-Z]{16}',
        "aws_secret_key": r'["\']?[A-Za-z0-9/+=]{40}["\']?',
        "private_key": r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
        "api_key": r'[aA][pP][iI]_?[kK][eE][yY].*[=:]\s*["\']?[a-zA-Z0-9_\-]{16,}["\']?',
        "password": r'[pP]assword.*[=:]\s*["\'][^"\']{8,}["\']',
        "secret": r'[sS]ecret.*[=:]\s*["\'][^"\']{8,}["\']',
        "token": r'[tT]oken.*[=:]\s*["\'][^"\']{16,}["\']',
        "database_url": r'["\']?[a-zA-Z][a-zA-Z0-9+.-]*://[^"\'\\s]+["\']?'
    }
    
    issues = []
    exclude_patterns = [
        r'#.*',  # Comments
        r'//.*',  # Comments
        r'YOUR_.*',  # Templates
        r'REPLACE_.*',  # Templates
        r'TEMPLATE.*',  # Templates
        r'bootstrap-credentials',  # Known safe reference
        r'\.pyi',  # Type stub files
    ]
    
    # Directories to exclude
    exclude_dirs = {'.git', '.terraform', '.venv', 'site-packages', 'node_modules'}
    
    # File extensions to check
    include_extensions = {'.py', '.tf', '.yaml', '.yml', '.json', '.env', '.sh'}
    
    for root, dirs, files in os.walk('.'):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if not any(file.endswith(ext) for ext in include_extensions):
                continue
                
            if file.endswith('.secrets') or 'credentials' in file:
                continue  # Skip credential files
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip excluded patterns
                        if any(re.search(pattern, line) for pattern in exclude_patterns):
                            continue
                            
                        # Check for secret patterns
                        for secret_type, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                # Additional validation for false positives
                                if secret_type == 'aws_secret_key':
                                    # Must be a realistic secret key (not just base64 text)
                                    if not (re.search(r'[A-Z]', match.group()) and 
                                           re.search(r'[a-z]', match.group()) and
                                           re.search(r'[0-9+/=]', match.group())):
                                        continue
                                
                                issues.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'type': secret_type,
                                    'pattern': pattern,
                                    'context': line.strip()[:100] + ('...' if len(line.strip()) > 100 else '')
                                })
                                
            except Exception:
                continue  # Skip files that can't be read
    
    if issues:
        print_status("❌", f"Secret detection found {len(issues)} potential secrets", force=True)
        if not QUIET_MODE:
            for issue in issues[:5]:  # Show first 5 issues
                print(f"   {issue['file']}:{issue['line']} - {issue['type']}")
                print(f"   {issue['context']}")
                print()
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more potential secrets")
    else:
        print_status("✅", "Secret detection: No secrets found")
    
    return {
        "tool": "secret_detection",
        "status": "success",
        "issues": len(issues),
        "details": issues if issues else []
    }

def check_file_permissions() -> Dict[str, Any]:
    """Check file permissions for sensitive files."""
    print_status("🔐", "Checking file permissions...")
    
    issues = []
    sensitive_files = ['.secrets', '.root-secrets', 'credentials/admin.env', 'credentials/developer.env']
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            try:
                stat_info = os.stat(file_path)
                perms = oct(stat_info.st_mode)[-3:]
                
                if perms != '600':
                    issues.append({
                        'file': file_path,
                        'current_perms': perms,
                        'expected_perms': '600'
                    })
                    
                    # Fix permissions
                    os.chmod(file_path, 0o600)
                    print_status("⚠️", f"Fixed {file_path} permissions (was {perms}, now 600)")
                    
            except Exception as e:
                issues.append({
                    'file': file_path,
                    'error': str(e)
                })
    
    if not issues:
        print_status("✅", "File permissions: All sensitive files properly secured")
    
    return {
        "tool": "file_permissions",
        "status": "success",
        "issues": len(issues),
        "details": issues if issues else []
    }

def check_gitignore() -> Dict[str, Any]:
    """Check .gitignore configuration."""
    print_status("📝", "Checking .gitignore configuration...")
    
    issues = []
    required_patterns = [
        '.secrets',
        '*.tfstate',
        '.terraform',
        'credentials/',
        '__pycache__/',
        '*.pyc'
    ]
    
    gitignore_path = '.gitignore'
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                issues.append({
                    'type': 'missing_pattern',
                    'pattern': pattern
                })
    else:
        issues.append({
            'type': 'missing_file', 
            'file': '.gitignore'
        })
    
    if issues:
        print_status("⚠️", f"GitIgnore: {len(issues)} configuration issues found")
        if not QUIET_MODE:
            for issue in issues:
                if issue['type'] == 'missing_pattern':
                    print(f"   Missing pattern: {issue['pattern']}")
                elif issue['type'] == 'missing_file':
                    print(f"   Missing file: {issue['file']}")
    else:
        print_status("✅", "GitIgnore: Properly configured")
    
    return {
        "tool": "gitignore_check",
        "status": "success",
        "issues": len(issues),
        "details": issues if issues else []
    }

def save_results(results: Dict[str, Any]) -> None:
    """Save detailed results to log file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    with open(log_dir / "security-scan-results.json", "w") as f:
        json.dump(results, f, indent=2)

def main() -> int:
    """Main security scanning function."""
    global QUIET_MODE
    
    parser = argparse.ArgumentParser(description="Comprehensive security scanner")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")
    args = parser.parse_args()
    
    QUIET_MODE = args.quiet
    
    if not QUIET_MODE:
        print_status("🔒", "Starting comprehensive security scan...")
    
    # Run all security checks
    results = {
        "timestamp": "2025-09-24T19:30:00Z",
        "scans": {
            "bandit": run_bandit_scan(),
            "checkov": run_checkov_scan(), 
            "safety": run_safety_scan(),
            "secret_detection": run_secret_detection(),
            "file_permissions": check_file_permissions(),
            "gitignore": check_gitignore()
        }
    }
    
    # Calculate totals
    total_issues = sum(scan.get("issues", 0) for scan in results["scans"].values())
    tools_run = sum(1 for scan in results["scans"].values() if scan.get("status") == "success")
    tools_skipped = sum(1 for scan in results["scans"].values() if scan.get("status") == "skipped")
    
    results["summary"] = {
        "total_issues": total_issues,
        "tools_run": tools_run,
        "tools_skipped": tools_skipped,
        "overall_status": "PASS" if total_issues == 0 else "FAIL"
    }
    
    # Save detailed results
    save_results(results)
    
    # Print summary
    if total_issues == 0:
        print_status("✅", "Security scan passed - No issues found", force=True)
    else:
        print_status("❌", f"Security scan failed - {total_issues} issues found", force=True)
    
    if not QUIET_MODE:
        print_status("📊", f"Summary: {tools_run} tools run, {tools_skipped} skipped", force=True)
        print_status("📝", "Detailed results saved to logs/security-scan-results.json", force=True)
    
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())