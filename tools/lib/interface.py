"""
Lead DEV communication interface for HMAS Bridge Layer.

This module provides the interface for communicating with the Lead DEV (Gemini).
Currently implemented as a stub that simulates responses for testing.
"""

from datetime import datetime, timezone
from typing import Optional

from .config import Config


class LeadDevResponse:
    """Response from Lead DEV."""

    def __init__(
        self,
        success: bool,
        content: str,
        error_code: int = 0,
        error_message: Optional[str] = None,
        context_used: Optional[list[str]] = None,
    ):
        self.success = success
        self.content = content
        self.error_code = error_code
        self.error_message = error_message
        self.context_used = context_used or []
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert response to dictionary for JSON output."""
        return {
            "status": "success" if self.success else "error",
            "response": self.content,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "context_used": self.context_used,
            "timestamp": self.timestamp.isoformat(),
        }


class LeadDevInterface:
    """
    Interface for communicating with Lead DEV.

    Currently implemented as a stub that:
    - Prints the query/report that would be sent
    - Returns a mock response indicating the tool is working
    - Logs the context that would be aggregated

    Future implementations will integrate with Gemini CLI.
    """

    def __init__(self, config: Optional[Config] = None, verbose: bool = False):
        """
        Initialize the Lead DEV interface.

        Args:
            config: Configuration instance. If None, creates a new one.
            verbose: Whether to print debug information.
        """
        self.config = config or Config()
        self.verbose = verbose
        self._stub_mode = True  # Always stub mode for now

    def query(
        self,
        question: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """
        Send a query to Lead DEV and get a response.

        Args:
            question: The question to ask
            context: Aggregated context dictionary

        Returns:
            LeadDevResponse with the result
        """
        if self._stub_mode:
            return self._stub_query(question, context)

        # Future: Implement actual Gemini CLI integration
        raise NotImplementedError("Live Lead DEV integration not yet implemented")

    def report_progress(
        self,
        phase: int,
        status: str,
        message: Optional[str],
        milestone: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """
        Send a progress report to Lead DEV.

        Args:
            phase: Phase number
            status: Status value (done, blocked, review)
            message: Optional details
            milestone: Milestone identifier
            context: Aggregated context dictionary

        Returns:
            LeadDevResponse with acknowledgment
        """
        if self._stub_mode:
            return self._stub_report_progress(phase, status, message, milestone, context)

        # Future: Implement actual Gemini CLI integration
        raise NotImplementedError("Live Lead DEV integration not yet implemented")

    def validate_status(
        self,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """
        Request status validation from Lead DEV.

        Args:
            context: Aggregated context dictionary including git status

        Returns:
            LeadDevResponse with validation result
        """
        if self._stub_mode:
            return self._stub_validate_status(context)

        # Future: Implement actual Gemini CLI integration
        raise NotImplementedError("Live Lead DEV integration not yet implemented")

    def _log_to_file(self, message: str) -> None:
        """Log message to the configured log file."""
        log_file_path = self.config.get("output", "log_file")
        if not log_file_path:
            return

        # Ensure directory exists
        log_path = self.config.project_root / log_file_path
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).isoformat()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            if self.verbose:
                print(f"[ERROR] Failed to write to log file: {e}")

    def _stub_query(
        self,
        question: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Stub implementation for query."""
        if self.verbose:
            print("[STUB MODE] Query to Lead DEV:")
            print(f"  Question: {question}")
            print(f"  Context size: {sum(len(v) for v in context.values())} chars")

        self._log_to_file(f"QUERY: {question}")

        # Extract document names from context for reporting
        context_used = []
        if context.get("documents"):
            # Parse document headers from aggregated content
            docs_content = context["documents"]
            for line in docs_content.split("\n"):
                if line.startswith("=== ") and line.endswith(" ==="):
                    doc_name = line[4:-4]
                    context_used.append(doc_name)

        response_content = (
            f"[STUB RESPONSE]\n"
            f"This is a stub response for testing purposes.\n"
            f"In production, this query would be sent to Lead DEV (Gemini):\n\n"
            f"Question: {question}\n\n"
            f"The Lead DEV would process this with the provided context and return "
            f"architectural guidance or clarification."
        )

        self._log_to_file(f"RESPONSE: {response_content[:100]}...")

        return LeadDevResponse(
            success=True,
            content=response_content,
            context_used=context_used,
        )

    def _stub_report_progress(
        self,
        phase: int,
        status: str,
        message: Optional[str],
        milestone: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Stub implementation for progress report."""
        if self.verbose:
            print("[STUB MODE] Progress report to Lead DEV:")
            print(f"  Phase: {phase}")
            print(f"  Status: {status}")
            print(f"  Milestone: {milestone}")
            if message:
                print(f"  Message: {message}")

        self._log_to_file(f"PROGRESS: Phase {phase} ({status}) - {milestone} - {message or ''}")

        response_content = (
            f"[STUB ACKNOWLEDGMENT]\n"
            f"Progress report received (stub mode).\n"
            f"In production, Lead DEV would update global state:\n"
            f"  - Phase {phase} marked as '{status}'\n"
            f"  - Milestone: {milestone}\n"
        )

        if status == "blocked":
            response_content += "  - Blocker flagged for CTO/Lead attention\n"
        elif status == "review":
            response_content += "  - Stakeholders notified for review\n"

        return LeadDevResponse(
            success=True,
            content=response_content,
        )

    def _stub_validate_status(
        self,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Stub implementation for status validation."""
        if self.verbose:
            print("[STUB MODE] Status validation request to Lead DEV:")
            print(f"  Context size: {sum(len(v) for v in context.values())} chars")

        self._log_to_file("STATUS CHECK: Validation requested")

        response_content = (
            f"[STUB VALIDATION]\n"
            f"Status validation processed (stub mode).\n"
            f"In production, Lead DEV would validate current state against the plan."
        )

        return LeadDevResponse(
            success=True,
            content=response_content,
        )
