#!/usr/bin/env python3
"""
handoff - Session handoff tool for context renewal between milestones.

Part of the HMAS Bridge Layer (Milestone 5).

Generates a "System Prompt" or "Initialization Block" that sums up the current
state of the project, enabling seamless session transitions for long-running projects.

Usage:
    python tools/handoff.py                         # Use current milestone
    python tools/handoff.py --milestone M5          # Specify milestone explicitly
    python tools/handoff.py --next                  # Target the next milestone
    python tools/handoff.py --include-audit         # Include latest audit log summary
    python tools/handoff.py --compact               # Shorter output for smaller context

Exit codes:
    0 - Success: handoff prompt generated
    1 - Error: required files not found
    2 - Error: invalid arguments
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a session handoff prompt for context renewal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/handoff.py                         # Generate for current milestone
  python tools/handoff.py --milestone M5          # Generate for specific milestone
  python tools/handoff.py --next                  # Generate for next milestone
  python tools/handoff.py --include-audit         # Include audit log summary
  python tools/handoff.py --compact               # Shorter, more focused output
        """,
    )

    parser.add_argument(
        "--milestone", "-m",
        type=str,
        help="Specify the target milestone (e.g., M5)",
    )

    parser.add_argument(
        "--next", "-n",
        action="store_true",
        help="Target the next milestone after the current one",
    )

    parser.add_argument(
        "--include-audit", "-a",
        action="store_true",
        help="Include summary from the latest audit log",
    )

    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Generate a more compact prompt (for smaller context windows)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include debug information to stderr",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Write output to file instead of stdout",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto mode: write context to .gemini/next_context.txt for the Infinity Loop",
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


def find_milestone_by_id(milestones_path: Path, milestone_id: str) -> Optional[Path]:
    """Find a milestone file by its ID (e.g., M5)."""
    # Normalize the milestone ID
    if not milestone_id.upper().startswith("M"):
        milestone_id = f"M{milestone_id}"
    else:
        milestone_id = milestone_id.upper()

    # Search for matching files
    for mf in milestones_path.glob(f"{milestone_id}_*.md"):
        return mf

    return None


def find_latest_audit_log(audit_path: Path) -> Optional[Path]:
    """Find the most recent audit log file."""
    if not audit_path.exists():
        return None

    audit_files = list(audit_path.glob("*.md"))
    if not audit_files:
        return None

    # Sort by modification time, most recent first
    audit_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return audit_files[0]


def extract_milestone_info(milestone_path: Path) -> dict[str, str]:
    """Extract key information from a milestone file."""
    content = milestone_path.read_text(encoding="utf-8")
    info = {
        "title": "",
        "objective": "",
        "phases": "",
        "success_criteria": "",
        "full_content": content,
    }

    # Extract title (first # heading)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        info["title"] = title_match.group(1).strip()

    # Extract objective section
    obj_match = re.search(r"##\s*Objective\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if obj_match:
        info["objective"] = obj_match.group(1).strip()

    # Extract phases section
    phases_match = re.search(r"##\s*Phases\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if phases_match:
        info["phases"] = phases_match.group(1).strip()

    # Extract success criteria
    criteria_match = re.search(r"##\s*Success Criteria\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if criteria_match:
        info["success_criteria"] = criteria_match.group(1).strip()

    return info


def extract_architecture_summary(arch_path: Path, compact: bool = False) -> str:
    """Extract a summary of the architecture document."""
    if not arch_path.exists():
        return "(Architecture document not found)"

    content = arch_path.read_text(encoding="utf-8")

    if compact:
        # Extract just the core principles section
        principles_match = re.search(
            r"##\s*2\.\s*Core Principles\s*\n(.*?)(?=\n##\s*3\.|\Z)",
            content,
            re.DOTALL
        )
        if principles_match:
            return f"## Core Principles\n{principles_match.group(1).strip()}"
        # Fallback to first 1500 chars
        return content[:1500] + "..." if len(content) > 1500 else content

    # For full mode, include more sections
    # Extract sections 1-3 (Technology Stack, Core Principles, Bridge Layer overview)
    sections = []

    # Section 1: Technology Stack
    tech_match = re.search(
        r"##\s*1\.\s*Technology Stack\s*\n(.*?)(?=\n##\s*2\.|\Z)",
        content,
        re.DOTALL
    )
    if tech_match:
        sections.append(f"## Technology Stack\n{tech_match.group(1).strip()}")

    # Section 2: Core Principles
    principles_match = re.search(
        r"##\s*2\.\s*Core Principles\s*\n(.*?)(?=\n##\s*3\.|\Z)",
        content,
        re.DOTALL
    )
    if principles_match:
        sections.append(f"## Core Principles\n{principles_match.group(1).strip()}")

    if sections:
        return "\n\n".join(sections)

    # Fallback
    return content[:3000] + "..." if len(content) > 3000 else content


def extract_roadmap_status(roadmap_path: Path) -> str:
    """Extract the current roadmap status."""
    if not roadmap_path.exists():
        return "(Roadmap not found)"

    return roadmap_path.read_text(encoding="utf-8")


def extract_audit_summary(audit_path: Path, compact: bool = False) -> Optional[str]:
    """Extract a summary from the latest audit log."""
    latest_audit = find_latest_audit_log(audit_path)
    if not latest_audit:
        return None

    content = latest_audit.read_text(encoding="utf-8")

    if compact:
        # Extract just the summary section
        summary_match = re.search(
            r"##\s*(Validation Summary|Summary|Final Status)\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            return f"[From {latest_audit.name}]\n{summary_match.group(0).strip()}"
        # Fallback to first 500 chars
        return f"[From {latest_audit.name}]\n{content[:500]}..."

    # Full audit content
    return f"[From {latest_audit.name}]\n{content}"


def generate_handoff_prompt(
    milestone_info: dict[str, str],
    architecture_summary: str,
    roadmap_status: str,
    audit_summary: Optional[str] = None,
    compact: bool = False,
) -> str:
    """Generate the complete handoff prompt."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build the prompt
    sections = []

    # Header
    header = f"""System Prompt for Senior DEV (Claude):

You are the **Senior DEV** (Claude Code) in the Hierarchical Multi-Agent System (HMAS).

**Current Context:**
- **Project:** HMAS
- **Current Milestone:** {milestone_info.get('title', 'Unknown')}
- **Generated:** {timestamp}
"""
    sections.append(header)

    # Objective (from milestone)
    if milestone_info.get("objective"):
        obj_section = f"""**Objective:**
{milestone_info['objective']}
"""
        sections.append(obj_section)

    # Architecture summary
    if not compact:
        arch_section = f"""---
## Architecture Summary

{architecture_summary}
"""
        sections.append(arch_section)

    # Roadmap status
    roadmap_section = f"""---
## Current Roadmap

{roadmap_status}
"""
    sections.append(roadmap_section)

    # Milestone details (phases)
    if milestone_info.get("phases"):
        phases_section = f"""---
## Current Milestone Phases

{milestone_info['phases']}
"""
        sections.append(phases_section)

    # Success criteria
    if milestone_info.get("success_criteria"):
        criteria_section = f"""---
## Success Criteria

{milestone_info['success_criteria']}
"""
        sections.append(criteria_section)

    # Audit summary (if requested)
    if audit_summary:
        audit_section = f"""---
## Latest Audit Summary

{audit_summary}
"""
        sections.append(audit_section)

    # Command Protocols section
    protocols = """---
## Command Protocols (Macros)

Use these shorthand commands to interact with the Bridge Layer efficiently:

| Macro | Expands To | Purpose |
|-------|------------|---------|
| `>> STATUS` | `python tools/status_check.py` | Check alignment and environment state |
| `>> DONE` | `python tools/report_progress.py --phase <N> --status done --mode api` | Report current phase completed |
| `>> BLOCK` | `python tools/report_progress.py --phase <N> --status blocked --mode api` | Report current phase blocked |
| `>> ASK <query>` | `python tools/ask_lead.py --mode api "<query>"` | Query Lead DEV for guidance |
| `>> HANDOFF` | `python tools/handoff.py --auto` | Prepare context for next session, then exit |

**Note:** Replace `<N>` with the current phase number. After `>> HANDOFF`, exit the session immediately.
"""
    sections.append(protocols)

    # Footer with instructions
    footer = """---
## Instructions

1. Review the context above to understand the current project state.
2. Check `docs/01_milestones/` for the detailed milestone specification.
3. Use `>> STATUS` to verify alignment.
4. Use `>> ASK <query>` for clarifications from Lead DEV.
5. Proceed with the current phase tasks.
6. Use `>> DONE` after completing each phase.
7. Use `>> HANDOFF` when context window is exhausted or milestone is complete.

**Key Files:**
- `docs/00_global/ARCHITECTURE.md` - System architecture
- `docs/00_global/ROADMAP.md` - Project progress
- `docs/01_milestones/` - Milestone specifications
- `tools/` - Bridge Layer tools
"""
    sections.append(footer)

    return "\n".join(sections)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Initialize configuration
    try:
        config = Config()
    except Exception as e:
        print(f"[ERROR] Configuration initialization failed: {e}", file=sys.stderr)
        return 1

    milestones_path = config.milestones_path
    audit_path = config.docs_path / "99_audit"

    # Determine target milestone
    milestone_path: Optional[Path] = None
    milestone_id: str = ""

    if args.milestone:
        # User specified a milestone
        milestone_path = find_milestone_by_id(milestones_path, args.milestone)
        if not milestone_path:
            print(f"[ERROR] Milestone {args.milestone} not found", file=sys.stderr)
            return 2
        milestone_id = args.milestone.upper()

    elif args.next:
        # Find current and determine next
        current = find_current_milestone(milestones_path)
        if current is None:
            print("[ERROR] No current milestone found", file=sys.stderr)
            return 1

        current_id, _, current_num = current
        next_num = current_num + 1
        next_id = f"M{next_num}"

        milestone_path = find_milestone_by_id(milestones_path, next_id)
        if not milestone_path:
            # Next milestone doesn't exist yet - use current but note the transition
            if args.verbose:
                print(f"[INFO] Next milestone ({next_id}) not found, using current ({current_id})", file=sys.stderr)
            milestone_path = find_milestone_by_id(milestones_path, current_id)
            milestone_id = current_id
        else:
            milestone_id = next_id

    else:
        # Use current milestone
        current = find_current_milestone(milestones_path)
        if current is None:
            print("[ERROR] No milestones found", file=sys.stderr)
            return 1

        milestone_id, milestone_path, _ = current

    if args.verbose:
        print(f"[INFO] Target milestone: {milestone_id} ({milestone_path.name})", file=sys.stderr)

    # Extract all information
    milestone_info = extract_milestone_info(milestone_path)
    architecture_summary = extract_architecture_summary(
        config.architecture_file,
        compact=args.compact
    )
    roadmap_status = extract_roadmap_status(config.roadmap_file)

    audit_summary = None
    if args.include_audit:
        audit_summary = extract_audit_summary(audit_path, compact=args.compact)
        if audit_summary and args.verbose:
            print("[INFO] Included audit log summary", file=sys.stderr)

    # Generate the handoff prompt
    prompt = generate_handoff_prompt(
        milestone_info=milestone_info,
        architecture_summary=architecture_summary,
        roadmap_status=roadmap_status,
        audit_summary=audit_summary,
        compact=args.compact,
    )

    # Output
    if args.auto:
        # Auto mode: write to .gemini/next_context.txt for the Infinity Loop
        gemini_dir = config.project_root / ".gemini"
        gemini_dir.mkdir(exist_ok=True)
        output_path = gemini_dir / "next_context.txt"
        try:
            output_path.write_text(prompt, encoding="utf-8")
            print(f"[HANDOFF] Context written to: {output_path}")
            print("[HANDOFF] Exit session now. The Infinity Loop will restart with fresh context.")
        except Exception as e:
            print(f"[ERROR] Failed to write context file: {e}", file=sys.stderr)
            return 1
    elif args.output:
        try:
            output_path = Path(args.output)
            output_path.write_text(prompt, encoding="utf-8")
            print(f"[OK] Handoff prompt written to: {output_path}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to write output file: {e}", file=sys.stderr)
            return 1
    else:
        print(prompt)

    return 0


if __name__ == "__main__":
    sys.exit(main())
