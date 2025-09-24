#!/usr/bin/env python3
"""
Comprehensive Markdown Linting Script

This script checks all .md files in the repository for markdown rule violations
using pymarkdownlnt (comprehensive linter) and mdformat (formatter).
It detects issues like MD036, MD040, MD032, and many others that VS Code's markdownlint catches.
"""

import os
import sys
import subprocess
from typing import List, Tuple


def find_markdown_files() -> List[str]:
    """Find all .md files in the repository."""
    markdown_files = []

    # Get all .md files recursively, excluding .git and other ignored directories
    exclude_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".terraform",
        "venv",
        ".venv",
        "site-packages",
    }

    for root, dirs, files in os.walk("."):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))

    return sorted(markdown_files)


def check_markdown_file(file_path: str, fix: bool = False) -> Tuple[bool, str]:
    """
    Check a single markdown file for linting issues using comprehensive rules.

    Args:
        file_path: Path to the markdown file
        fix: Whether to fix issues automatically

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if fix:
            # First run pymarkdown fix for comprehensive rule fixes
            pymarkdown_result = subprocess.run(
                ["pymarkdown", "--config", ".pymarkdown.json", "fix", file_path],
                capture_output=True,
                text=True,
            )

            # Then run mdformat for consistent formatting
            mdformat_result = subprocess.run(
                ["python3", "-m", "mdformat", file_path], capture_output=True, text=True
            )

            if pymarkdown_result.returncode == 0 and mdformat_result.returncode == 0:
                return True, f"✅ Fixed: {file_path}"
            else:
                errors = []
                if pymarkdown_result.returncode != 0:
                    errors.append(f"PyMarkdown: {pymarkdown_result.stderr}")
                if mdformat_result.returncode != 0:
                    errors.append(f"MDFormat: {mdformat_result.stderr}")
                return False, f"❌ Could not fix: {file_path}\n" + "\n".join(errors)
        else:
            # Check with comprehensive pymarkdown linting using config
            result = subprocess.run(
                ["pymarkdown", "--config", ".pymarkdown.json", "scan", file_path],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True, f"✅ Valid: {file_path}"
            else:
                # Format the output to show specific rule violations
                return False, f"❌ Invalid: {file_path}\n{result.stdout.strip()}"

    except Exception as e:
        return False, f"❌ Error processing {file_path}: {str(e)}"


def main():
    """Main function to run markdown linting."""
    import argparse

    parser = argparse.ArgumentParser(description="Lint markdown files using mdformat")
    parser.add_argument(
        "--fix", action="store_true", help="Fix formatting issues automatically"
    )
    parser.add_argument(
        "--files", nargs="*", help="Specific files to check (default: all .md files)"
    )

    args = parser.parse_args()

    if args.files:
        markdown_files = args.files
    else:
        markdown_files = find_markdown_files()

    if not markdown_files:
        print("📝 No markdown files found.")
        return 0

    print(
        f"🔍 {'Fixing' if args.fix else 'Checking'} {len(markdown_files)} markdown files..."
    )
    print()

    all_valid = True
    results = []

    for file_path in markdown_files:
        is_valid, message = check_markdown_file(file_path, args.fix)
        results.append(message)
        if not is_valid:
            all_valid = False

    # Print results
    for result in results:
        print(result)

    print()
    if all_valid:
        print(f"✅ All {len(markdown_files)} markdown files are properly formatted!")
        return 0
    else:
        failed_count = sum(1 for r in results if r.startswith("❌"))
        print(
            f"❌ {failed_count}/{len(markdown_files)} markdown files have formatting issues."
        )
        if not args.fix:
            print("💡 Run with --fix to automatically fix formatting issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
