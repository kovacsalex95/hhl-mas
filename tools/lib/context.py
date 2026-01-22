"""
Context aggregation logic for HMAS Bridge Layer.

Aggregates relevant documentation to provide context to Lead DEV
when processing queries or reports.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from .config import Config


class QueryType(Enum):
    """Types of queries for context selection."""
    ARCHITECTURAL = "architectural"
    IMPLEMENTATION = "implementation"
    PROGRESS = "progress"
    STATUS = "status"
    GENERAL = "general"


class ContextAggregator:
    """Aggregates relevant documentation context for Bridge Layer queries."""

    # Approximate characters per token (conservative estimate)
    CHARS_PER_TOKEN = 4

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the context aggregator.

        Args:
            config: Configuration instance. If None, creates a new one.
        """
        self.config = config or Config()

    def aggregate(
        self,
        query_type: QueryType,
        query_content: str,
        current_phase: Optional[str] = None,
        current_milestone: Optional[str] = None,
        include_git_status: bool = False,
    ) -> dict[str, str]:
        """
        Aggregate relevant context based on query type.

        Args:
            query_type: Type of query for context selection
            query_content: The actual query or report content
            current_phase: Current phase identifier (e.g., "1")
            current_milestone: Current milestone (e.g., "M1_Documentation")
            include_git_status: Whether to include git status in context

        Returns:
            Dictionary with context components:
            - "query": The query content
            - "phase": Current phase info
            - "documents": Aggregated document contents
            - "git_status": Git status (if requested)
        """
        context: dict[str, str] = {
            "query": query_content,
            "phase": self._format_phase_info(current_phase, current_milestone),
        }

        # Select and aggregate documents based on query type
        documents = self._select_documents(query_type, current_milestone)
        context["documents"] = self._aggregate_documents(documents)

        if include_git_status:
            context["git_status"] = self._get_git_status()

        # Apply size limits
        context = self._apply_size_limits(context)

        return context

    def _format_phase_info(
        self,
        phase: Optional[str],
        milestone: Optional[str]
    ) -> str:
        """Format phase and milestone info for context."""
        parts = []
        if milestone:
            parts.append(f"Milestone: {milestone}")
        if phase:
            parts.append(f"Phase: {phase}")
        return "\n".join(parts) if parts else "Phase: Unknown"

    def _select_documents(
        self,
        query_type: QueryType,
        milestone: Optional[str]
    ) -> list[Path]:
        """
        Select documents to include based on query type.

        Following the aggregation rules from ARCHITECTURE.md:
        - Architectural question: ARCHITECTURE.md, ROADMAP.md, relevant milestone spec
        - Implementation question: Current milestone spec, ARCHITECTURE.md
        - Progress report: Current milestone spec, Technical Plan
        - Status check: Current milestone spec, Technical Plan, git status
        """
        documents: list[Path] = []

        # Always include architecture for non-trivial queries
        if query_type in (QueryType.ARCHITECTURAL, QueryType.IMPLEMENTATION, QueryType.GENERAL):
            if self.config.architecture_file.exists():
                documents.append(self.config.architecture_file)

        # Include roadmap for architectural/scope questions
        if query_type == QueryType.ARCHITECTURAL:
            if self.config.roadmap_file.exists():
                documents.append(self.config.roadmap_file)

        # Include current milestone spec
        if milestone:
            milestone_file = self._find_milestone_spec(milestone)
            if milestone_file and milestone_file.exists():
                documents.append(milestone_file)

        return documents

    def _find_milestone_spec(self, milestone: str) -> Optional[Path]:
        """Find the milestone specification file."""
        milestones_path = self.config.milestones_path

        if not milestones_path.exists():
            return None

        # Try common naming patterns
        patterns = [
            f"{milestone}.md",
            f"{milestone.replace('_', ' ')}.md",
            f"M{milestone.lstrip('M')}.md" if milestone.startswith('M') else f"M{milestone}.md",
        ]

        # Also search for files containing the milestone name
        for file in milestones_path.glob("*.md"):
            if milestone.lower() in file.name.lower():
                return file

        for pattern in patterns:
            file_path = milestones_path / pattern
            if file_path.exists():
                return file_path

        return None

    def _aggregate_documents(self, documents: list[Path]) -> str:
        """Read and aggregate document contents."""
        aggregated: list[str] = []

        for doc_path in documents:
            try:
                content = doc_path.read_text()
                header = f"=== {doc_path.name} ==="
                aggregated.append(f"{header}\n{content}")
            except Exception:
                # Skip unreadable documents
                continue

        return "\n\n".join(aggregated)

    def _get_git_status(self) -> str:
        """Get current git status."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.config.project_root,
                timeout=10
            )
            status = result.stdout.strip()
            if not status:
                return "Git Status: Clean (no uncommitted changes)"
            return f"Git Status:\n{status}"
        except Exception as e:
            return f"Git Status: Unable to determine ({e})"

    def _apply_size_limits(self, context: dict[str, str]) -> dict[str, str]:
        """Apply token size limits to context, truncating if necessary."""
        max_tokens = self.config.max_context_tokens
        max_chars = max_tokens * self.CHARS_PER_TOKEN

        # Calculate current size
        total_chars = sum(len(v) for v in context.values())

        if total_chars <= max_chars:
            return context

        # Truncate documents first (preserve query and phase info)
        if "documents" in context:
            query_phase_chars = len(context.get("query", "")) + len(context.get("phase", ""))
            git_chars = len(context.get("git_status", ""))
            available_for_docs = max_chars - query_phase_chars - git_chars

            if available_for_docs > 0:
                docs = context["documents"]
                if len(docs) > available_for_docs:
                    # Truncate with indicator
                    context["documents"] = docs[:available_for_docs - 50] + "\n\n[... truncated for size limit ...]"
            else:
                context["documents"] = "[Documents omitted due to size limit]"

        return context

    def get_context_summary(self, context: dict[str, str]) -> str:
        """Get a summary of what context was aggregated (for logging/verbose mode)."""
        summary_parts = [f"Query: {len(context.get('query', ''))} chars"]

        if context.get("phase"):
            summary_parts.append(f"Phase info: {context['phase']}")

        if context.get("documents"):
            doc_size = len(context["documents"])
            summary_parts.append(f"Documents: {doc_size} chars")

        if context.get("git_status"):
            summary_parts.append("Git status: included")

        total = sum(len(v) for v in context.values())
        summary_parts.append(f"Total context: ~{total // self.CHARS_PER_TOKEN} tokens")

        return "\n".join(summary_parts)
