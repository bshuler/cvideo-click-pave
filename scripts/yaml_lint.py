#!/usr/bin/env python3
"""
YAML Linter Script

Comprehensive YAML linting using yamllint with custom configuration
for GitHub Actions workflows and other YAML files.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List


def print_status(icon: str, message: str) -> None:
    """Print a status message with an icon."""
    print(f"{icon} {message}")


def find_yaml_files() -> List[str]:
    """Find all YAML files in the project, respecting .gitignore."""
    yaml_files: List[str] = []
    yaml_extensions = {".yaml", ".yml"}

    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [
            d for d in dirs if d not in {".venv", "node_modules", ".git", "__pycache__"}
        ]

        for file in files:
            if any(file.endswith(ext) for ext in yaml_extensions):
                yaml_files.append(os.path.join(root, file))

    return sorted(yaml_files)


def check_github_actions_issues(file_path: Path) -> List[str]:
    """Check for GitHub Actions specific issues."""
    issues: List[str] = []

    if ".github/workflows" not in str(file_path):
        return issues

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Known valid patterns that shouldn't be flagged - documented for future reference
        # valid_patterns = {
        #     "env.ACT",  # Act sets this for local testing
        #     "secrets.AWS_ACCESS_KEY_ID",  # Common repository secret
        #     "secrets.AWS_SECRET_ACCESS_KEY",  # Common repository secret
        #     "secrets.AWS_REGION",  # Common repository secret
        # }

        for i, line in enumerate(lines, 1):
            # Look for potential issues, but skip known valid patterns

            # Check for deprecated actions (example)
            if "actions/checkout@v2" in line:
                issues.append(
                    f"Line {i}: Consider upgrading to actions/checkout@v4 (v2 is deprecated)"
                )

            # Check for potentially problematic GitHub context usage
            if "${{ env.GITHUB_" in line and not line.strip().startswith("#"):
                # GitHub environment variables should use the github context
                issues.append(
                    f"Line {i}: Consider using '${{{{ github.* }}}}' instead of '${{{{ env.GITHUB_* }}}}'"
                )

            # Check for missing quotes around version numbers that might be interpreted as numbers
            if (
                "node-version:" in line.lower()
                and not ('"' in line or "'" in line)
                and any(char.isdigit() for char in line)
            ):
                issues.append(
                    f"Line {i}: Consider quoting Node.js version numbers to avoid YAML interpretation issues"
                )

    except Exception as e:
        issues.append(f"Error reading file: {e}")

    return issues


def run_yamllint(yaml_files: List[str], quiet: bool = False) -> bool:
    """Run yamllint on the provided YAML files.

    Args:
        yaml_files: List of YAML file paths to check
        quiet: Only show failures and final summary

    Returns:
        True if all files pass linting, False otherwise
    """
    if not yaml_files:
        print_status("ℹ️", "No YAML files found to lint")
        return True

    # Create yamllint configuration
    config_content = """
rules:
  line-length:
    max: 120
    allow-non-breakable-words: true
    allow-non-breakable-inline-mappings: true
  comments:
    min-spaces-from-content: 1
  indentation:
    spaces: 2
    indent-sequences: true
    check-multi-line-strings: false
  truthy:
    allowed-values: ['true', 'false', 'on', 'off']
    check-keys: false
  braces:
    min-spaces-inside: 0
    max-spaces-inside: 1
  brackets:
    min-spaces-inside: 0
    max-spaces-inside: 0
  colons:
    max-spaces-before: 0
    max-spaces-after: 1
  commas:
    max-spaces-before: 0
    max-spaces-after: 1
  document-start: disable
  document-end: disable
  empty-lines:
    max: 2
    max-start: 0
    max-end: 1
  hyphens:
    max-spaces-after: 1
  key-duplicates: enable
  new-line-at-end-of-file: enable
  trailing-spaces: enable
  octal-values: disable
"""

    config_file = Path(".yamllint")
    try:
        config_file.write_text(config_content.strip(), encoding="utf-8")

        success = True
        for yaml_file in yaml_files:
            if not quiet:
                print_status("🔍", f"Linting {yaml_file}")

            # Run yamllint on the file
            result = subprocess.run(
                ["yamllint", "-c", str(config_file), yaml_file],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                success = False
                print_status("❌", f"Issues found in {yaml_file}:")
                print(result.stdout)
            else:
                if not quiet:
                    print_status("✅", f"{yaml_file} passes linting")

            # Also check for GitHub Actions specific issues
            github_issues = check_github_actions_issues(Path(yaml_file))
            if github_issues:
                print_status("⚠️", f"GitHub Actions suggestions for {yaml_file}:")
                for issue in github_issues:
                    print(f"  {issue}")

        if success and quiet:
            print_status("✅", f"All {len(yaml_files)} YAML files pass linting")

        return success

    finally:
        # Clean up temporary config file
        if config_file.exists():
            config_file.unlink()


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(description="Lint YAML files")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues (not supported by yamllint)",
    )
    parser.add_argument(
        "files", nargs="*", help="Specific files to lint (default: all YAML files)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show failures and final summary",
    )

    args = parser.parse_args()

    if args.fix and not args.quiet:
        print_status(
            "⚠️",
            "yamllint does not support automatic fixing. Use --fix for consistency with other linters.",
        )

    # Determine files to process
    if args.files:
        files = [str(Path(f)) for f in args.files if Path(f).exists()]
        if not files:
            if not args.quiet:
                print_status("❌", "No valid files specified")
            return 1
    else:
        files = find_yaml_files()

    # Run yamllint (pass quiet flag to modify behavior)
    success = run_yamllint(files, quiet=args.quiet)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
