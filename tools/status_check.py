#!/usr/bin/env python3
"""
status_check - Validate current execution state against the active plan.

Part of the HMAS Bridge Layer.

Usage:
    python tools/status_check.py
    python tools/status_check.py --verbose
    python tools/status_check.py --fix

Exit codes:
    0 - Aligned: no issues detected
    1 - Warning: minor issues (can proceed)
    2 - Misaligned: significant drift detected
    3 - Error: cannot determine status
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.context import ContextAggregator, QueryType
from lib.interface import LeadDevInterface


@dataclass
class StatusResult:
    """Result of status check."""
    aligned: bool
    warnings: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    git_branch: str = ""
    git_clean: bool = True
    git_uncommitted_count: int = 0
    last_commit_hash: str = ""
    last_commit_message: str = ""
    current_milestone: str = ""
    current_phase: str = ""
    total_phases: str = ""
    completed_phases: int = 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate current execution state against the active plan.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/status_check.py
  python tools/status_check.py --verbose
  python tools/status_check.py --fix
        """,
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed status information",
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt automatic remediation of minor issues",
    )

    parser.add_argument(
        "--milestone",
        type=str,
        help="Check specific milestone instead of current",
    )

    return parser.parse_args()


def run_git_command(args: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def check_git_state(config: Config) -> tuple[dict, list[str], list[str]]:
    """
    Check git repository state.

    Returns:
        Tuple of (git_info dict, warnings list, issues list)
    """
    git_info = {
        "branch": "",
        "clean": True,
        "uncommitted_count": 0,
        "last_commit_hash": "",
        "last_commit_message": "",
    }
    warnings: list[str] = []
    issues: list[str] = []

    project_root = config.project_root

    # Check current branch
    success, branch = run_git_command(["branch", "--show-current"], project_root)
    if success:
        git_info["branch"] = branch
    else:
        issues.append("Cannot determine current git branch")

    # Check for uncommitted changes
    success, status = run_git_command(["status", "--porcelain"], project_root)
    if success:
        if status:
            lines = [l for l in status.split("\n") if l.strip()]
            git_info["clean"] = False
            git_info["uncommitted_count"] = len(lines)
            warnings.append(f"Uncommitted changes detected ({len(lines)} files)")
    else:
        warnings.append("Cannot check git status")

    # Get last commit info
    success, log = run_git_command(
        ["log", "-1", "--format=%h %s"],
        project_root
    )
    if success and log:
        parts = log.split(" ", 1)
        git_info["last_commit_hash"] = parts[0]
        git_info["last_commit_message"] = parts[1] if len(parts) > 1 else ""
    else:
        warnings.append("Cannot retrieve last commit information")

    return git_info, warnings, issues


def check_documentation_state(config: Config) -> tuple[dict, list[str], list[str]]:
    """
    Check documentation state.

    Returns:
        Tuple of (doc_info dict, warnings list, issues list)
    """
    doc_info = {
        "milestone": "",
        "phase": "",
        "total_phases": "",
    }
    warnings: list[str] = []
    issues: list[str] = []

    # Check architecture file exists
    if not config.architecture_file.exists():
        issues.append("ARCHITECTURE.md not found")

    # Check milestones directory
    if not config.milestones_path.exists():
        warnings.append("Milestones directory not found")
    else:
        # Find current milestone
        milestone_files = list(config.milestones_path.glob("M*_*.md"))
        if milestone_files:
            # Use the first milestone (could be enhanced to track current)
            doc_info["milestone"] = milestone_files[0].stem
        else:
            warnings.append("No milestone specifications found")

    return doc_info, warnings, issues


def detect_milestone(config: Config) -> str:
    """Attempt to detect current milestone from project state."""
    milestones_path = config.milestones_path
    if milestones_path.exists():
        milestone_files = list(milestones_path.glob("M*_*.md"))
        if milestone_files:
            return milestone_files[0].stem
    return "Unknown"


def format_aligned_output(result: StatusResult) -> str:
    """Format output for aligned status."""
    lines = [
        "[STATUS CHECK - ALIGNED]",
        f"Milestone: {result.current_milestone}",
    ]

    if result.current_phase:
        phase_str = f"Current Phase: {result.current_phase}"
        if result.total_phases:
            phase_str += f" of {result.total_phases}"
        lines.append(phase_str)

    if result.completed_phases > 0:
        lines.append(f"Completed Phases: {result.completed_phases}")

    lines.append(f"Git Status: {'Clean' if result.git_clean else 'Modified'}")

    if result.last_commit_hash:
        lines.append(f"Last Commit: {result.last_commit_hash} \"{result.last_commit_message}\"")

    lines.append("[END STATUS]")
    return "\n".join(lines)


def format_warning_output(result: StatusResult) -> str:
    """Format output for warning status."""
    lines = [
        "[STATUS CHECK - WARNING]",
        f"Milestone: {result.current_milestone}",
    ]

    if result.current_phase:
        phase_str = f"Current Phase: {result.current_phase}"
        if result.total_phases:
            phase_str += f" of {result.total_phases}"
        lines.append(phase_str)

    lines.append("Warnings:")
    for warning in result.warnings:
        lines.append(f"  - {warning}")

    lines.append("Recommendation: Review warnings before proceeding")
    lines.append("[END STATUS]")
    return "\n".join(lines)


def format_misaligned_output(result: StatusResult) -> str:
    """Format output for misaligned status."""
    lines = [
        "[STATUS CHECK - MISALIGNED]",
        f"Milestone: {result.current_milestone}",
        "Issues:",
    ]

    for issue in result.issues:
        lines.append(f"  - {issue}")

    if result.warnings:
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")

    lines.append("Action Required: Run 'ask_lead' for remediation guidance")
    lines.append("[END STATUS]")
    return "\n".join(lines)


def format_error_output(message: str) -> str:
    """Format output for error status."""
    lines = [
        "[STATUS CHECK - ERROR]",
        f"Error: {message}",
        "Cannot determine current status.",
        "[END STATUS]",
    ]
    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        print("[DEBUG] Starting status check...")

    # Initialize components
    try:
        config = Config()
        aggregator = ContextAggregator(config)
        interface = LeadDevInterface(config, verbose=args.verbose)
    except Exception as e:
        print(format_error_output(f"Initialization failed: {e}"))
        return 3

    # Initialize result
    result = StatusResult(aligned=True)

    # Override milestone if specified
    if args.milestone:
        result.current_milestone = args.milestone
    else:
        result.current_milestone = detect_milestone(config)

    if args.verbose:
        print(f"[DEBUG] Checking milestone: {result.current_milestone}")

    # Check git state
    try:
        git_info, git_warnings, git_issues = check_git_state(config)
        result.git_branch = git_info["branch"]
        result.git_clean = git_info["clean"]
        result.git_uncommitted_count = git_info["uncommitted_count"]
        result.last_commit_hash = git_info["last_commit_hash"]
        result.last_commit_message = git_info["last_commit_message"]
        result.warnings.extend(git_warnings)
        result.issues.extend(git_issues)

        if args.verbose:
            print(f"[DEBUG] Git branch: {result.git_branch}")
            print(f"[DEBUG] Git clean: {result.git_clean}")
            print(f"[DEBUG] Last commit: {result.last_commit_hash}")
    except Exception as e:
        result.issues.append(f"Git check failed: {e}")

    # Check documentation state
    try:
        doc_info, doc_warnings, doc_issues = check_documentation_state(config)
        if not result.current_milestone and doc_info["milestone"]:
            result.current_milestone = doc_info["milestone"]
        result.current_phase = doc_info.get("phase", "")
        result.total_phases = doc_info.get("total_phases", "")
        result.warnings.extend(doc_warnings)
        result.issues.extend(doc_issues)

        if args.verbose:
            print(f"[DEBUG] Documentation check complete")
    except Exception as e:
        result.issues.append(f"Documentation check failed: {e}")

    # Aggregate context for potential Lead DEV validation
    try:
        context = aggregator.aggregate(
            query_type=QueryType.STATUS,
            query_content="Status check validation",
            current_phase=result.current_phase,
            current_milestone=result.current_milestone,
            include_git_status=True,
        )

        if args.verbose:
            print("[DEBUG] Context aggregated for validation")
            print(aggregator.get_context_summary(context))
    except Exception as e:
        result.warnings.append(f"Context aggregation warning: {e}")

    # Optionally consult Lead DEV for validation (stub mode)
    if args.verbose:
        try:
            response = interface.validate_status(context)
            if args.verbose:
                print("[DEBUG] Lead DEV validation response:")
                print(response.content)
        except Exception:
            pass  # Non-critical in stub mode

    # Handle --fix option
    if args.fix and result.warnings:
        if args.verbose:
            print("[DEBUG] Attempting automatic fixes...")

        # Currently, no automatic fixes implemented
        # Future: could implement things like stashing uncommitted changes
        print("[INFO] Automatic fixes not yet implemented. Review warnings manually.")

    # Determine final status and output
    if result.issues:
        result.aligned = False
        print(format_misaligned_output(result))
        return 2
    elif result.warnings:
        print(format_warning_output(result))
        return 1
    else:
        print(format_aligned_output(result))
        return 0


if __name__ == "__main__":
    sys.exit(main())
