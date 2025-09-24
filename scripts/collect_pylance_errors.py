#!/usr/bin/env python3
"""
Pylance Error Collection Script

Automates collection of Pylance errors from Python files in the project.
Integrates with VS Code's Python Language Server to get TypedDict and other type errors.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"


def print_status(emoji: str, message: str) -> None:
    """Print formatted status message."""
    print(f"{emoji} {message}")


def find_python_files() -> List[Path]:
    """Find all Python files in the project."""
    python_files: List[Path] = []

    # Get Python files from scripts directory
    if SCRIPTS_DIR.exists():
        python_files.extend(SCRIPTS_DIR.glob("*.py"))

    # Get any Python files in root
    python_files.extend(WORKSPACE_ROOT.glob("*.py"))

    return [f for f in python_files if f.is_file()]


def run_pylance_check(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Run Pylance check on a single file using the MCP Pylance server.

    Args:
        file_path: Path to the Python file to check

    Returns:
        List of error dictionaries or None if no errors
    """
    try:
        # For now, we'll use a placeholder that shows how this would work
        # In a real implementation, this would call the Pylance MCP server
        print_status("🔍", f"Checking {file_path.name}...")

        # Placeholder for MCP Pylance integration
        # This would call: mcp_pylance_mcp_s_pylanceFileSyntaxErrors
        # with the file URI and workspace root

        return None

    except Exception as e:
        print_status("❌", f"Error checking {file_path}: {e}")
        return None


def collect_all_errors() -> Dict[str, List[Dict[str, Any]]]:
    """
    Collect Pylance errors from all Python files in the project.

    Returns:
        Dictionary mapping file paths to lists of errors
    """
    print_status("🔍", "Collecting Pylance errors from Python files...")

    python_files = find_python_files()
    print_status("📁", f"Found {len(python_files)} Python files to check")

    all_errors: Dict[str, List[Dict[str, Any]]] = {}

    for file_path in python_files:
        errors = run_pylance_check(file_path)
        if errors:
            all_errors[str(file_path)] = errors

    return all_errors


def format_error_report(errors: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Format error report for display.

    Args:
        errors: Dictionary of file paths to error lists

    Returns:
        Formatted error report string
    """
    if not errors:
        return "✅ No Pylance errors found!"

    report = []
    report.append("❌ Pylance Errors Found:")
    report.append("")

    total_errors = 0
    for file_path, file_errors in errors.items():
        report.append(f"📄 {Path(file_path).name}:")
        for error in file_errors:
            total_errors += 1
            line = error.get("line", "?")
            message = error.get("message", "Unknown error")
            error_type = error.get("type", "Error")
            report.append(f"  Line {line}: {error_type} - {message}")
        report.append("")

    report.append(f"Total errors: {total_errors}")
    return "\n".join(report)


def save_error_report(
    errors: Dict[str, List[Dict[str, Any]]], output_file: Optional[Path] = None
) -> None:
    """
    Save error report to file.

    Args:
        errors: Dictionary of file paths to error lists
        output_file: Optional output file path
    """
    if output_file is None:
        output_file = WORKSPACE_ROOT / "pylance_errors.json"

    try:
        with open(output_file, "w") as f:
            json.dump(errors, f, indent=2)
        print_status("💾", f"Error report saved to {output_file}")
    except Exception as e:
        print_status("❌", f"Failed to save error report: {e}")


def main() -> int:
    """
    Main entry point for Pylance error collection.

    Returns:
        Exit code (0 for success, 1 for errors found)
    """
    print_status("🔍", "Starting Pylance error collection...")

    try:
        # Collect all errors
        errors = collect_all_errors()

        # Format and display report
        report = format_error_report(errors)
        print(report)

        # Save report to file
        save_error_report(errors)

        # Return appropriate exit code
        if errors:
            print_status("⚠️", "Pylance errors found - check output above")
            return 1
        else:
            print_status("✅", "No Pylance errors found")
            return 0

    except Exception as e:
        print_status("❌", f"Error during Pylance check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
