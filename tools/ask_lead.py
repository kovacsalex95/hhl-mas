#!/usr/bin/env python3
"""
ask_lead - Query Lead DEV for clarifications, architectural decisions, or implementation guidance.

Part of the HMAS Bridge Layer.

Usage:
    python tools/ask_lead.py "<question>"
    python tools/ask_lead.py --format json "What authentication method should I use?"
    python tools/ask_lead.py --verbose "How should errors be reported to users?"

Exit codes:
    0 - Success: response received
    1 - Error: Lead DEV unreachable
    2 - Error: invalid query format
    3 - Error: context aggregation failed
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import Config
from lib.context import ContextAggregator, QueryType
from lib.interface import LeadDevInterface


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Query Lead DEV for clarifications or guidance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/ask_lead.py "Should user sessions persist across server restarts?"
  python tools/ask_lead.py --format json "What authentication method should I use?"
  python tools/ask_lead.py --verbose "How should errors be reported to users?"
        """,
    )

    parser.add_argument(
        "question",
        type=str,
        help="The question to ask Lead DEV",
    )

    parser.add_argument(
        "--context",
        type=str,
        default="auto",
        choices=["auto", "minimal", "full"],
        help="Context selection mode (default: auto)",
    )

    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "json", "markdown"],
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include debug information",
    )

    parser.add_argument(
        "--milestone",
        type=str,
        help="Override current milestone identifier",
    )

    parser.add_argument(
        "--phase",
        type=str,
        help="Override current phase identifier",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["interactive", "stub", "api"],
        help="Interface mode: interactive (default), stub (testing), api (future)",
    )

    return parser.parse_args()


def detect_query_type(question: str) -> QueryType:
    """Detect the type of query based on question content."""
    question_lower = question.lower()

    # Architectural keywords
    arch_keywords = [
        "architecture", "design", "pattern", "structure", "approach",
        "should i use", "which", "best practice", "how should",
    ]
    if any(kw in question_lower for kw in arch_keywords):
        return QueryType.ARCHITECTURAL

    # Implementation keywords
    impl_keywords = [
        "implement", "code", "function", "class", "method",
        "how do i", "how to", "syntax", "error", "bug",
    ]
    if any(kw in question_lower for kw in impl_keywords):
        return QueryType.IMPLEMENTATION

    return QueryType.GENERAL


def format_output_text(response_content: str) -> str:
    """Format response for text output."""
    return f"[LEAD DEV RESPONSE]\n{response_content}\n[END RESPONSE]"


def format_output_json(
    response_content: str,
    context_used: list[str],
    success: bool,
) -> str:
    """Format response for JSON output."""
    output = {
        "status": "success" if success else "error",
        "response": response_content,
        "context_used": context_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(output, indent=2)


def format_output_markdown(response_content: str, context_used: list[str]) -> str:
    """Format response for markdown output."""
    parts = [
        "## Lead DEV Response",
        "",
        response_content,
        "",
        "---",
        f"*Context: {', '.join(context_used) if context_used else 'minimal'}*",
    ]
    return "\n".join(parts)


def format_error(message: str, output_format: str) -> str:
    """Format error message according to output format."""
    if output_format == "json":
        return json.dumps({
            "status": "error",
            "error": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2)
    return f"[ERROR] {message}"


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Validate question
    if not args.question or not args.question.strip():
        print(format_error("Invalid query: question cannot be empty", args.format))
        return 2

    question = args.question.strip()

    if args.verbose:
        print(f"[DEBUG] Question: {question}")

    # Initialize components
    try:
        config = Config()
        aggregator = ContextAggregator(config)
        interface = LeadDevInterface(config, verbose=args.verbose, mode=args.mode)
    except Exception as e:
        print(format_error(f"Initialization failed: {e}", args.format))
        return 3

    # Detect query type and aggregate context
    try:
        query_type = detect_query_type(question)

        if args.verbose:
            print(f"[DEBUG] Detected query type: {query_type.value}")

        context = aggregator.aggregate(
            query_type=query_type,
            query_content=question,
            current_phase=args.phase,
            current_milestone=args.milestone,
        )

        if args.verbose:
            print(f"[DEBUG] Context summary:")
            print(aggregator.get_context_summary(context))
    except Exception as e:
        print(format_error(f"Context aggregation failed: {e}", args.format))
        return 3

    # Query Lead DEV
    try:
        response = interface.query(question, context)
    except Exception as e:
        print(format_error(f"Lead DEV unreachable: {e}", args.format))
        return 1

    # Handle response
    if not response.success:
        print(format_error(
            response.error_message or "Unknown error from Lead DEV",
            args.format
        ))
        return response.error_code or 1

    # Format and output response
    if args.format == "json":
        output = format_output_json(
            response.content,
            response.context_used,
            response.success,
        )
    elif args.format == "markdown":
        output = format_output_markdown(response.content, response.context_used)
    else:
        output = format_output_text(response.content)

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
