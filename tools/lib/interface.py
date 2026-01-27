"""
Lead DEV communication interface for HMAS Bridge Layer.

This module provides the interface for communicating with the Lead DEV (Gemini).
Supports multiple modes:
- interactive: User provides responses via CLI input
- stub: Returns mock responses for testing
- api: Gemini API integration for automated Lead DEV responses
"""

import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .config import Config
from .gemini_provider import (
    GeminiProvider,
    GeminiProviderError,
    GeminiAPIKeyError,
)


class InterfaceMode(Enum):
    """Communication modes for Lead DEV interface."""
    INTERACTIVE = "interactive"
    STUB = "stub"
    API = "api"


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

    Supports multiple communication modes:
    - interactive: Displays context and prompts user for input via CLI
    - stub: Returns mock responses for testing
    - api: Future Gemini API integration

    The mode can be set via config or constructor parameter.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        verbose: bool = False,
        mode: Optional[str] = None,
    ):
        """
        Initialize the Lead DEV interface.

        Args:
            config: Configuration instance. If None, creates a new one.
            verbose: Whether to print debug information.
            mode: Interface mode override ('interactive', 'stub', 'api').
                  If None, reads from config or defaults to 'interactive'.
        """
        self.config = config or Config()
        self.verbose = verbose

        # Determine mode: explicit > config > default
        if mode:
            self._mode = InterfaceMode(mode)
        else:
            config_mode = self.config.get("bridge.lead_dev", "mode")
            if config_mode:
                self._mode = InterfaceMode(config_mode)
            else:
                self._mode = InterfaceMode.INTERACTIVE  # Default to interactive

        # Lazy-initialized Gemini provider for API mode
        self._gemini_provider: Optional[GeminiProvider] = None

    def _get_gemini_provider(self) -> GeminiProvider:
        """Get or create the Gemini provider instance."""
        if self._gemini_provider is None:
            self._gemini_provider = GeminiProvider(verbose=self.verbose)
        return self._gemini_provider

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
        if self._mode == InterfaceMode.STUB:
            return self._stub_query(question, context)
        elif self._mode == InterfaceMode.INTERACTIVE:
            return self._interactive_query(question, context)
        elif self._mode == InterfaceMode.API:
            return self._api_query(question, context)
        else:
            raise ValueError(f"Unknown interface mode: {self._mode}")

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
        if self._mode == InterfaceMode.STUB:
            return self._stub_report_progress(phase, status, message, milestone, context)
        elif self._mode == InterfaceMode.INTERACTIVE:
            return self._interactive_report_progress(phase, status, message, milestone, context)
        elif self._mode == InterfaceMode.API:
            return self._api_report_progress(phase, status, message, milestone, context)
        else:
            raise ValueError(f"Unknown interface mode: {self._mode}")

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
        if self._mode == InterfaceMode.STUB:
            return self._stub_validate_status(context)
        elif self._mode == InterfaceMode.INTERACTIVE:
            return self._interactive_validate_status(context)
        elif self._mode == InterfaceMode.API:
            return self._api_validate_status(context)
        else:
            raise ValueError(f"Unknown interface mode: {self._mode}")

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

    # =========================================================================
    # Interactive Mode Implementations
    # =========================================================================

    def _print_separator(self, char: str = "=", width: int = 70) -> None:
        """Print a visual separator line."""
        print(char * width, file=sys.stderr)

    def _print_context_summary(self, context: dict[str, str]) -> None:
        """Print a summary of the aggregated context."""
        print("\n[AGGREGATED CONTEXT]", file=sys.stderr)
        self._print_separator("-")

        for key, value in context.items():
            if value:
                # Truncate long values for display
                preview = value[:500] + "..." if len(value) > 500 else value
                print(f"\n--- {key.upper()} ---", file=sys.stderr)
                print(preview, file=sys.stderr)

        self._print_separator("-")
        total_chars = sum(len(v) for v in context.values())
        print(f"Total context size: {total_chars} characters", file=sys.stderr)

    def _get_user_input(self, prompt: str) -> str:
        """
        Prompt the user for input.

        Args:
            prompt: The prompt to display

        Returns:
            User's input as a string
        """
        self._print_separator()
        print(f"\n{prompt}", file=sys.stderr)
        print("(Enter your response, then press Enter twice or Ctrl+D to submit)", file=sys.stderr)
        self._print_separator()

        lines = []
        empty_line_count = 0

        try:
            while True:
                line = input()
                if line == "":
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        # Two consecutive empty lines signals end of input
                        break
                    lines.append(line)
                else:
                    empty_line_count = 0
                    lines.append(line)
        except EOFError:
            # Ctrl+D pressed
            pass

        return "\n".join(lines).strip()

    def _interactive_query(
        self,
        question: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Interactive implementation for query - prompts user for response."""
        self._print_separator("=")
        print("\n[QUERY TO LEAD DEV]", file=sys.stderr)
        print(f"\nQuestion: {question}", file=sys.stderr)

        # Display context summary
        self._print_context_summary(context)

        # Log the query
        self._log_to_file(f"INTERACTIVE QUERY: {question}")

        # Get user response
        user_response = self._get_user_input("Please provide your response as Lead DEV:")

        if not user_response:
            return LeadDevResponse(
                success=False,
                content="",
                error_code=2,
                error_message="No response provided",
            )

        self._log_to_file(f"INTERACTIVE RESPONSE: {user_response[:100]}...")

        # Extract document names from context for reporting
        context_used = []
        if context.get("documents"):
            docs_content = context["documents"]
            for line in docs_content.split("\n"):
                if line.startswith("=== ") and line.endswith(" ==="):
                    doc_name = line[4:-4]
                    context_used.append(doc_name)

        return LeadDevResponse(
            success=True,
            content=user_response,
            context_used=context_used,
        )

    def _interactive_report_progress(
        self,
        phase: int,
        status: str,
        message: Optional[str],
        milestone: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Interactive implementation for progress report - prompts user for acknowledgment."""
        self._print_separator("=")
        print("\n[PROGRESS REPORT TO LEAD DEV]", file=sys.stderr)
        print(f"\nMilestone: {milestone}", file=sys.stderr)
        print(f"Phase: {phase}", file=sys.stderr)
        print(f"Status: {status}", file=sys.stderr)
        if message:
            print(f"Message: {message}", file=sys.stderr)

        # Display context summary
        self._print_context_summary(context)

        # Log the report
        self._log_to_file(f"INTERACTIVE PROGRESS: Phase {phase} ({status}) - {milestone}")

        # Get user acknowledgment/response
        user_response = self._get_user_input(
            "Please acknowledge or provide guidance as Lead DEV:"
        )

        if not user_response:
            # Empty response is acceptable for progress reports
            user_response = f"Acknowledged: Phase {phase} marked as '{status}'"

        self._log_to_file(f"INTERACTIVE ACK: {user_response[:100]}...")

        return LeadDevResponse(
            success=True,
            content=user_response,
        )

    def _interactive_validate_status(
        self,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """Interactive implementation for status validation - prompts user for validation."""
        self._print_separator("=")
        print("\n[STATUS VALIDATION REQUEST]", file=sys.stderr)

        # Display context summary
        self._print_context_summary(context)

        # Log the validation request
        self._log_to_file("INTERACTIVE STATUS CHECK: Validation requested")

        # Get user validation response
        user_response = self._get_user_input(
            "Please validate the current status as Lead DEV (or provide corrections):"
        )

        if not user_response:
            user_response = "Status validated - no issues noted"

        self._log_to_file(f"INTERACTIVE VALIDATION: {user_response[:100]}...")

        return LeadDevResponse(
            success=True,
            content=user_response,
        )

    # =========================================================================
    # API Mode Implementations (Gemini)
    # =========================================================================

    def _api_query(
        self,
        question: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """API implementation for query - uses Gemini API."""
        if self.verbose:
            print("[API MODE] Querying Gemini as Lead DEV...")

        self._log_to_file(f"API QUERY: {question}")

        try:
            provider = self._get_gemini_provider()
            response_text = provider.query(question, context)

            self._log_to_file(f"API RESPONSE: {response_text[:100]}...")

            # Extract document names from context for reporting
            context_used = []
            if context.get("documents"):
                docs_content = context["documents"]
                for line in docs_content.split("\n"):
                    if line.startswith("=== ") and line.endswith(" ==="):
                        doc_name = line[4:-4]
                        context_used.append(doc_name)

            return LeadDevResponse(
                success=True,
                content=response_text,
                context_used=context_used,
            )

        except GeminiAPIKeyError as e:
            self._log_to_file(f"API ERROR (key): {e}")
            return LeadDevResponse(
                success=False,
                content="",
                error_code=1,
                error_message=str(e),
            )

        except GeminiProviderError as e:
            self._log_to_file(f"API ERROR (provider): {e}")
            return LeadDevResponse(
                success=False,
                content="",
                error_code=1,
                error_message=f"Lead DEV API error: {e}",
            )

    def _api_report_progress(
        self,
        phase: int,
        status: str,
        message: Optional[str],
        milestone: str,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """API implementation for progress report - uses Gemini API."""
        if self.verbose:
            print("[API MODE] Reporting progress to Gemini...")

        self._log_to_file(f"API PROGRESS: Phase {phase} ({status}) - {milestone}")

        try:
            provider = self._get_gemini_provider()
            response_text = provider.report_progress(
                phase, status, message, milestone, context
            )

            self._log_to_file(f"API ACK: {response_text[:100]}...")

            return LeadDevResponse(
                success=True,
                content=response_text,
            )

        except GeminiAPIKeyError as e:
            self._log_to_file(f"API ERROR (key): {e}")
            return LeadDevResponse(
                success=False,
                content="",
                error_code=1,
                error_message=str(e),
            )

        except GeminiProviderError as e:
            self._log_to_file(f"API ERROR (provider): {e}")
            # For progress reports, return success with basic ack on API failure
            return LeadDevResponse(
                success=True,
                content=f"Acknowledged: Phase {phase} marked as '{status}' (API unavailable)",
            )

    def _api_validate_status(
        self,
        context: dict[str, str],
    ) -> LeadDevResponse:
        """API implementation for status validation - uses Gemini API."""
        if self.verbose:
            print("[API MODE] Requesting validation from Gemini...")

        self._log_to_file("API STATUS CHECK: Validation requested")

        try:
            provider = self._get_gemini_provider()
            response_text = provider.validate_status(context)

            self._log_to_file(f"API VALIDATION: {response_text[:100]}...")

            return LeadDevResponse(
                success=True,
                content=response_text,
            )

        except GeminiAPIKeyError as e:
            self._log_to_file(f"API ERROR (key): {e}")
            return LeadDevResponse(
                success=False,
                content="",
                error_code=1,
                error_message=str(e),
            )

        except GeminiProviderError as e:
            self._log_to_file(f"API ERROR (provider): {e}")
            return LeadDevResponse(
                success=True,
                content="Status validation completed (API unavailable - skipped remote check)",
            )
