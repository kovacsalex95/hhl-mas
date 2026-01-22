#!/usr/bin/env python3
"""
report_progress - Report phase/milestone completion status to Lead DEV.

Part of the HMAS Bridge Layer.

Usage:
    python tools/report_progress.py --phase 1 --status done
    python tools/report_progress.py --phase 2 --status blocked --message "Waiting for API credentials"
    python tools/report_progress.py --phase 3 --status review --message "Authentication flow ready for UAT"

Exit codes:
    0 - Success: progress recorded
    1 - Error: Lead DEV unreachable
    2 - Error: invalid arguments
    3 - Error: phase not found in plan
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.context import ContextAggregator, QueryType
from lib.interface import LeadDevInterface


# Valid status values
VALID_STATUSES = ["done", "blocked", "review"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Report phase/milestone completion status to Lead DEV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Status values:
  done     - Phase completed successfully
  blocked  - Cannot proceed without intervention
  review   - Ready for human or Lead review

Examples:
  python tools/report_progress.py --phase 1 --status done
  python tools/report_progress.py --phase 2 --status blocked --message "Waiting for API credentials"
  python tools/report_progress.py --phase 3 --status review --message "Authentication flow ready for UAT"
        """,
    )

    parser.add_argument(
        "--phase",
        type=int,
        required=True,
        help="Phase number from Technical Plan",
    )

    parser.add_argument(
        "--status",
        type=str,
        required=True,
        choices=VALID_STATUSES,
        help="Status: done, blocked, or review",
    )

    parser.add_argument(
        "--message",
        type=str,
        help="Additional details or notes",
    )

    parser.add_argument(
        "--milestone",
        type=str,
        help="Override current milestone identifier",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include debug information",
    )

    return parser.parse_args()


def detect_milestone(config: Config) -> str:
    """Attempt to detect current milestone from project state."""
    # Try to find milestone from milestones directory
    milestones_path = config.milestones_path
    if milestones_path.exists():
        milestone_files = list(milestones_path.glob("M*_*.md"))
        if milestone_files:
            # Return the first milestone found (could be enhanced)
            return milestone_files[0].stem

    return "Unknown"


def format_output(
    phase: int,
    status: str,
    milestone: str,
    message: str | None,
    timestamp: datetime,
) -> str:
    """Format the progress report output."""
    lines = [
        "[PROGRESS RECORDED]",
        f"Phase: {phase}",
        f"Status: {status}",
        f"Milestone: {milestone}",
    ]

    if message:
        lines.append(f"Message: {message}")

    # Add action required for blocked status
    if status == "blocked":
        lines.append("Action Required: CTO/Lead DEV intervention")

    lines.append(f"Timestamp: {timestamp.isoformat()}")
    lines.append("[END REPORT]")

    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format error message."""
    return f"[ERROR] {message}"


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Validate phase number
    if args.phase < 1:
        print(format_error("Invalid arguments: phase must be a positive integer"))
        return 2

    # Validate status
    if args.status not in VALID_STATUSES:
        print(format_error(f"Invalid arguments: status must be one of {VALID_STATUSES}"))
        return 2

    if args.verbose:
        print(f"[DEBUG] Phase: {args.phase}")
        print(f"[DEBUG] Status: {args.status}")
        if args.message:
            print(f"[DEBUG] Message: {args.message}")

    # Initialize components
    try:
        config = Config()
        aggregator = ContextAggregator(config)
        interface = LeadDevInterface(config, verbose=args.verbose)
    except Exception as e:
        print(format_error(f"Initialization failed: {e}"))
        return 2

    # Determine milestone
    milestone = args.milestone or detect_milestone(config)

    if args.verbose:
        print(f"[DEBUG] Milestone: {milestone}")

    # Aggregate context for progress report
    try:
        context = aggregator.aggregate(
            query_type=QueryType.PROGRESS,
            query_content=f"Progress report: Phase {args.phase} - {args.status}",
            current_phase=str(args.phase),
            current_milestone=milestone,
        )

        if args.verbose:
            print(f"[DEBUG] Context summary:")
            print(aggregator.get_context_summary(context))
    except Exception as e:
        print(format_error(f"Context aggregation failed: {e}"))
        return 3

    # Report progress to Lead DEV
    try:
        response = interface.report_progress(
            phase=args.phase,
            status=args.status,
            message=args.message,
            milestone=milestone,
            context=context,
        )
    except Exception as e:
        print(format_error(f"Lead DEV unreachable: {e}"))
        return 1

    # Handle response
    if not response.success:
        error_msg = response.error_message or "Unknown error from Lead DEV"
        print(format_error(error_msg))

        # Return appropriate error code
        if response.error_code == 3:
            return 3  # Phase not found
        return response.error_code or 1

    # Format and output progress report
    timestamp = datetime.now(timezone.utc)
    output = format_output(
        phase=args.phase,
        status=args.status,
        milestone=milestone,
        message=args.message,
        timestamp=timestamp,
    )

    print(output)

    # In verbose mode, also show the stub response
    if args.verbose:
        print("\n[DEBUG] Lead DEV response:")
        print(response.content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
