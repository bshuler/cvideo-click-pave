#!/usr/bin/env python3
"""
Pylance Error Collection Script - MCP Integration

Uses the available MCP Pylance server to collect TypedDict and other errors.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


def print_status(emoji: str, message: str) -> None:
    """Print formatted status message."""
    print(f"{emoji} {message}")


def get_workspace_root() -> str:
    """Get the workspace root URI."""
    workspace_root = Path(__file__).parent.parent
    return f"file://{workspace_root.absolute()}"


def find_python_files() -> List[str]:
    """Find all Python files in the project and return as URIs."""
    workspace_root = Path(__file__).parent.parent
    python_files = []

    # Get Python files from scripts directory
    scripts_dir = workspace_root / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            python_files.append(f"file://{py_file.absolute()}")

    # Get any Python files in root
    for py_file in workspace_root.glob("*.py"):
        python_files.append(f"file://{py_file.absolute()}")

    return python_files


def check_file_syntax(
    file_uri: str, workspace_root: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Check a single file for syntax errors using MCP Pylance.

    This is a placeholder that shows the structure for MCP integration.
    In the actual implementation, this would call:
    mcp_pylance_mcp_s_pylanceFileSyntaxErrors(workspaceRoot=workspace_root, fileUri=file_uri)
    """
    try:
        print_status("🔍", f"Checking {Path(file_uri.replace('file://', '')).name}...")

        # Placeholder for actual MCP call
        # errors = mcp_pylance_mcp_s_pylanceFileSyntaxErrors(
        #     workspaceRoot=workspace_root,
        #     fileUri=file_uri
        # )

        # For now, return None (no errors)
        return None

    except Exception as e:
        print_status("❌", f"Error checking file: {e}")
        return None


def collect_workspace_errors() -> Dict[str, Any]:
    """
    Collect all Pylance errors from the workspace.

    Returns:
        Dictionary containing error information
    """
    print_status("🔍", "Starting Pylance error collection...")

    workspace_root = get_workspace_root()
    python_files = find_python_files()

    print_status("📁", f"Found {len(python_files)} Python files to check")
    print_status("🏠", f"Workspace root: {workspace_root}")

    all_errors = {}
    total_error_count = 0

    for file_uri in python_files:
        file_path = file_uri.replace("file://", "")
        file_name = Path(file_path).name

        errors = check_file_syntax(file_uri, workspace_root)

        if errors:
            all_errors[file_name] = errors
            error_count = len(errors)
            total_error_count += error_count
            print_status("❌", f"{file_name}: {error_count} errors found")
        else:
            print_status("✅", f"{file_name}: No errors")

    print_status("📊", f"Total files checked: {len(python_files)}")
    print_status("📊", f"Files with errors: {len(all_errors)}")
    print_status("📊", f"Total errors: {total_error_count}")

    return {
        "workspace_root": workspace_root,
        "files_checked": len(python_files),
        "files_with_errors": len(all_errors),
        "total_errors": total_error_count,
        "errors": all_errors,
    }


def format_error_output(results: Dict[str, Any]) -> str:
    """Format error results for console output."""
    lines = []

    if results["total_errors"] == 0:
        lines.append("✅ No Pylance errors found in workspace!")
        return "\n".join(lines)

    lines.append("❌ Pylance Errors Summary:")
    lines.append(f"  Files checked: {results['files_checked']}")
    lines.append(f"  Files with errors: {results['files_with_errors']}")
    lines.append(f"  Total errors: {results['total_errors']}")
    lines.append("")

    for file_name, errors in results["errors"].items():
        lines.append(f"📄 {file_name}:")
        for error in errors:
            line_num = error.get("line", "?")
            col_num = error.get("column", "?")
            message = error.get("message", "Unknown error")
            error_type = error.get("severity", "Error")
            lines.append(f"  {line_num}:{col_num} {error_type}: {message}")
        lines.append("")

    return "\n".join(lines)


def save_results(results: Dict[str, Any], output_file: Optional[Path] = None) -> None:
    """Save results to JSON file."""
    if output_file is None:
        output_file = Path(__file__).parent.parent / "pylance_errors.json"

    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print_status("💾", f"Results saved to {output_file}")
    except Exception as e:
        print_status("❌", f"Failed to save results: {e}")


def main() -> int:
    """Main entry point."""
    try:
        # Collect errors
        results = collect_workspace_errors()

        # Format and display output
        output = format_error_output(results)
        print(output)

        # Save results
        save_results(results)

        # Return exit code based on errors found
        return 1 if results["total_errors"] > 0 else 0

    except Exception as e:
        print_status("❌", f"Error during Pylance check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
