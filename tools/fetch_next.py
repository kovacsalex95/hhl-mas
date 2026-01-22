#!/usr/bin/env python3
"""
fetch_next - Continuous progression tool for fetching the next milestone.

Part of the HMAS Inception Engine (Milestone 4).

Usage:
    python tools/fetch_next.py                    # Auto-detect current milestone
    python tools/fetch_next.py --milestone M3    # Specify completed milestone
    python tools/fetch_next.py --force           # Skip confirmation for overwrite

Exit codes:
    0 - Success: next milestone generated
    1 - Error: Lead DEV unreachable
    2 - Error: current milestone not found or incomplete
    3 - Error: file generation failed
    4 - Error: user cancelled operation
"""

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.interface import LeadDevInterface


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch the next milestone after completing the current one.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/fetch_next.py                    # Auto-detect completed milestone
  python tools/fetch_next.py --milestone M3    # Mark M3 as complete and fetch M4
  python tools/fetch_next.py --dry-run          # Preview without writing files
  python tools/fetch_next.py --force            # Skip confirmation prompts
        """,
    )

    parser.add_argument(
        "--milestone", "-m",
        type=str,
        help="Specify the milestone that was just completed (e.g., M3)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include debug information",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force operation without confirmation prompts",
    )

    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip archiving the current milestone",
    )

    return parser.parse_args()


def find_current_milestone(milestones_path: Path) -> Optional[tuple[str, Path, int]]:
    """
    Find the current/latest milestone in the milestones directory.

    Returns:
        Tuple of (milestone_id, file_path, milestone_number) or None
    """
    milestone_files = list(milestones_path.glob("M*_*.md"))
    if not milestone_files:
        return None

    # Parse milestone numbers and find the highest
    milestone_pattern = re.compile(r"M(\d+)_(.+)\.md$")
    milestones = []

    for mf in milestone_files:
        match = milestone_pattern.match(mf.name)
        if match:
            num = int(match.group(1))
            milestones.append((f"M{num}", mf, num))

    if not milestones:
        return None

    # Return the highest numbered milestone
    milestones.sort(key=lambda x: x[2], reverse=True)
    return milestones[0]


def check_milestone_complete(milestone_path: Path) -> tuple[bool, list[str]]:
    """
    Check if all checklist items in a milestone are complete.

    Returns:
        Tuple of (is_complete, incomplete_items)
    """
    content = milestone_path.read_text(encoding="utf-8")
    incomplete = []

    # Find unchecked items: - [ ]
    unchecked_pattern = re.compile(r"^[\s]*-\s*\[\s*\]\s*(.+)$", re.MULTILINE)
    matches = unchecked_pattern.findall(content)

    for item in matches:
        incomplete.append(item.strip())

    return len(incomplete) == 0, incomplete


def archive_milestone(
    milestone_path: Path,
    history_path: Path,
    verbose: bool = False,
) -> bool:
    """
    Archive a completed milestone to the history directory.

    Returns:
        True if successful, False otherwise
    """
    try:
        history_path.mkdir(parents=True, exist_ok=True)

        # Create archived filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        archive_name = f"{milestone_path.stem}_{timestamp}.md"
        archive_path = history_path / archive_name

        # Handle duplicate names
        counter = 1
        while archive_path.exists():
            archive_name = f"{milestone_path.stem}_{timestamp}_{counter}.md"
            archive_path = history_path / archive_name
            counter += 1

        shutil.copy2(milestone_path, archive_path)

        if verbose:
            print(f"[OK] Archived: {milestone_path.name} -> {archive_path}")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to archive milestone: {e}")
        return False


def extract_milestone_context(milestone_path: Path) -> str:
    """Extract relevant context from the completed milestone."""
    content = milestone_path.read_text(encoding="utf-8")

    # Extract the objective section
    objective = ""
    obj_match = re.search(r"##\s*Objective\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if obj_match:
        objective = obj_match.group(1).strip()

    # Extract success criteria
    criteria = ""
    criteria_match = re.search(r"##\s*Success Criteria\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if criteria_match:
        criteria = criteria_match.group(1).strip()

    return f"Objective: {objective}\n\nSuccess Criteria:\n{criteria}"


def construct_next_milestone_prompt(
    milestone_id: str,
    milestone_context: str,
    architecture_summary: str,
) -> str:
    """Construct the prompt for requesting the next milestone."""
    return f"""MILESTONE PROGRESSION REQUEST

Milestone {milestone_id} has been completed successfully.

## Completed Milestone Summary
{milestone_context}

## Project Architecture Context
{architecture_summary}

## Request

Based on the completed milestone and project architecture, please define the next logical milestone.

Generate a milestone specification with:

1. **Objective** - Clear goal for this milestone
2. **Phases** - 2-4 implementation phases with checklist items
3. **Success Criteria** - Measurable completion criteria
4. **Deliverables** - Expected outputs

## Response Format

### MILESTONE_START ###
(full milestone specification in markdown)
### MILESTONE_END ###
"""


def parse_milestone_response(response_content: str) -> Optional[str]:
    """
    Parse the Lead DEV response to extract milestone content.

    Returns:
        Milestone content or None
    """
    ms_start = response_content.find("### MILESTONE_START ###")
    ms_end = response_content.find("### MILESTONE_END ###")

    if ms_start != -1 and ms_end != -1:
        content = response_content[ms_start + len("### MILESTONE_START ###"):ms_end].strip()
        if content and content != "(full milestone specification in markdown)":
            return content

    return None


def generate_stub_next_milestone(
    current_num: int,
    milestone_context: str,
) -> tuple[str, str]:
    """
    Generate a stub next milestone for testing.

    Returns:
        Tuple of (milestone_content, suggested_title)
    """
    next_num = current_num + 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    content = f"""# Milestone {next_num}: Continuation

> Generated by HMAS Inception Engine on {timestamp}

## Objective

Continue development based on the progress from Milestone {current_num}.

Previous milestone context:
{milestone_context[:500]}{'...' if len(milestone_context) > 500 else ''}

## Phases

### Phase 1: Review & Planning
- [ ] Review Milestone {current_num} deliverables
- [ ] Identify areas for improvement
- [ ] Plan next implementation steps

### Phase 2: Implementation
- [ ] Implement core features for this milestone
- [ ] Integrate with existing codebase
- [ ] Handle edge cases and error scenarios

### Phase 3: Testing & Documentation
- [ ] Write tests for new functionality
- [ ] Update documentation
- [ ] Perform integration testing

## Success Criteria

- [ ] All Phase tasks completed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Ready for next milestone progression

## Deliverables

1. Implementation of milestone objectives
2. Updated test suite
3. Documentation updates
"""

    return content, "Continuation"


def get_architecture_summary(config: Config) -> str:
    """Read and summarize the architecture document."""
    arch_path = config.architecture_file
    if not arch_path.exists():
        return "(No architecture document found)"

    try:
        content = arch_path.read_text(encoding="utf-8")
        # Return first 1000 chars as summary
        return content[:1000] + ("..." if len(content) > 1000 else "")
    except Exception:
        return "(Could not read architecture document)"


def confirm_action(prompt: str) -> bool:
    """Ask user for confirmation."""
    try:
        response = input(f"{prompt} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Initialize configuration
    try:
        config = Config()
    except Exception as e:
        print(f"[ERROR] Configuration initialization failed: {e}")
        return 3

    milestones_path = config.milestones_path
    history_path = config.docs_path / "history"

    # Find or validate current milestone
    if args.milestone:
        # User specified a milestone
        milestone_id = args.milestone.upper()
        if not milestone_id.startswith("M"):
            milestone_id = f"M{milestone_id}"

        # Find the corresponding file
        milestone_files = list(milestones_path.glob(f"{milestone_id}_*.md"))
        if not milestone_files:
            print(f"[ERROR] Milestone {milestone_id} not found in {milestones_path}")
            return 2

        milestone_path = milestone_files[0]
        milestone_num = int(re.search(r"M(\d+)", milestone_id).group(1))
    else:
        # Auto-detect current milestone
        result = find_current_milestone(milestones_path)
        if result is None:
            print(f"[ERROR] No milestones found in {milestones_path}")
            return 2

        milestone_id, milestone_path, milestone_num = result

    if args.verbose:
        print(f"[INFO] Current milestone: {milestone_id} ({milestone_path.name})")

    # Check if milestone is complete
    is_complete, incomplete_items = check_milestone_complete(milestone_path)

    if not is_complete:
        print(f"[WARNING] Milestone {milestone_id} has {len(incomplete_items)} incomplete items:")
        for item in incomplete_items[:5]:
            print(f"  - [ ] {item}")
        if len(incomplete_items) > 5:
            print(f"  ... and {len(incomplete_items) - 5} more")

        if not args.force:
            if not confirm_action("Proceed anyway?"):
                print("[CANCELLED] Operation cancelled by user")
                return 4

    # Check if next milestone already exists
    next_num = milestone_num + 1
    next_id = f"M{next_num}"
    existing_next = list(milestones_path.glob(f"{next_id}_*.md"))

    if existing_next:
        print(f"[WARNING] {next_id} already exists: {existing_next[0].name}")

        # Check if the existing next milestone is incomplete
        is_next_complete, next_incomplete = check_milestone_complete(existing_next[0])
        if not is_next_complete:
            print(f"[ERROR] {next_id} exists and is incomplete ({len(next_incomplete)} items remaining)")
            if not args.force:
                print("Use --force to overwrite")
                return 2
            if not confirm_action(f"Overwrite incomplete {next_id}?"):
                print("[CANCELLED] Operation cancelled by user")
                return 4

    # Archive current milestone (unless --no-archive)
    if not args.no_archive and not args.dry_run:
        if args.verbose:
            print(f"[INFO] Archiving {milestone_id}...")
        if not archive_milestone(milestone_path, history_path, args.verbose):
            if not args.force:
                if not confirm_action("Archive failed. Continue anyway?"):
                    return 3

    # Extract context from completed milestone
    milestone_context = extract_milestone_context(milestone_path)
    architecture_summary = get_architecture_summary(config)

    # Query Lead DEV for next milestone
    try:
        interface = LeadDevInterface(config, verbose=args.verbose)
        prompt = construct_next_milestone_prompt(
            milestone_id,
            milestone_context,
            architecture_summary,
        )

        if args.verbose:
            print("[INFO] Querying Lead DEV for next milestone...")

        response = interface.query(prompt, {
            "milestone": milestone_context,
            "architecture": architecture_summary,
        })

        if not response.success:
            print(f"[ERROR] Lead DEV returned error: {response.error_message}")
            return 1

        # Parse response
        milestone_content = parse_milestone_response(response.content)
        suggested_title = "Continuation"

        # If parsing failed (stub mode), generate stub content
        if milestone_content is None or "[STUB" in response.content:
            if args.verbose:
                print("[INFO] Using stub generation (Lead DEV in stub mode)")
            milestone_content, suggested_title = generate_stub_next_milestone(
                milestone_num,
                milestone_context,
            )

    except Exception as e:
        print(f"[ERROR] Lead DEV communication failed: {e}")
        return 1

    # Determine output filename
    next_filename = f"M{next_num}_{suggested_title}.md"
    next_path = milestones_path / next_filename

    # Handle existing file
    if next_path.exists() and not args.force:
        # Try alternate names
        counter = 1
        while next_path.exists():
            next_filename = f"M{next_num}_{suggested_title}_{counter}.md"
            next_path = milestones_path / next_filename
            counter += 1

    # Write output
    if args.dry_run:
        print("[DRY RUN] Would write the following file:")
        print(f"\n--- {next_path} ---")
        print(milestone_content[:800] + "..." if len(milestone_content) > 800 else milestone_content)
    else:
        try:
            next_path.write_text(milestone_content, encoding="utf-8")
            if args.verbose:
                print(f"[OK] Written: {next_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write milestone file: {e}")
            return 3

    # Summary
    print(f"\n[PROGRESSION COMPLETE]")
    print(f"  Completed:   {milestone_id} ({milestone_path.name})")
    if not args.no_archive and not args.dry_run:
        print(f"  Archived to: {history_path}")
    print(f"  Next:        {next_id} ({next_path.name})")
    print("\nNext steps:")
    print(f"  1. Review the generated milestone: {next_path}")
    print("  2. Update status_check.py config if needed")
    print(f"  3. Start implementing {next_id} Phase 1")

    return 0


if __name__ == "__main__":
    sys.exit(main())
