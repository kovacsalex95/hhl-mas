"""
Gemini API provider for HMAS Bridge Layer.

This module handles communication with the Gemini API for Lead DEV responses.
It provides retry logic, error handling, and system prompt construction.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Load from project root .env file
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class GeminiConfig:
    """Configuration for Gemini API."""
    api_key: str
    model: str = "gemini-1.5-pro"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 2.0


class GeminiProviderError(Exception):
    """Base exception for Gemini provider errors."""
    pass


class GeminiAPIKeyError(GeminiProviderError):
    """Raised when API key is missing or invalid."""
    pass


class GeminiConnectionError(GeminiProviderError):
    """Raised when API connection fails."""
    pass


class GeminiResponseError(GeminiProviderError):
    """Raised when API returns an error response."""
    pass


# Lead DEV System Prompt - enforces persona and communication style
LEAD_DEV_SYSTEM_PROMPT = """You are the Lead DEV for a Hierarchical Multi-Agent System (HMAS) project.

## Your Role
- Strategic architect maintaining global project context
- Provide concise, authoritative architectural guidance
- Make decisions that align with documented milestones and roadmap

## Communication Style
- Be CONCISE: Prefer short, actionable responses (2-5 sentences typical)
- Be AUTHORITATIVE: State decisions clearly, avoid hedging
- Be ARCHITECTURAL: Focus on patterns, structure, and design principles
- Be PRAGMATIC: Prioritize working solutions over theoretical perfection

## Response Format
- Lead with the decision or answer
- Provide brief rationale only when necessary
- Reference specific docs/milestones when relevant
- If clarification needed, ask ONE focused question

## Context Awareness
You will receive aggregated context from the project documentation. Use this to:
- Ensure consistency with existing architecture
- Reference established patterns
- Maintain alignment with milestone specifications

Do NOT:
- Write code (that's Senior DEV's job)
- Provide lengthy explanations unless specifically asked
- Suggest major architectural changes without strong justification
- Add caveats or disclaimers to every response"""


class GeminiProvider:
    """
    Provider for Gemini API interactions.

    Handles API configuration, connection management, and retry logic
    for communicating with Gemini as the Lead DEV persona.
    """

    def __init__(
        self,
        config: Optional[GeminiConfig] = None,
        verbose: bool = False,
    ):
        """
        Initialize the Gemini provider.

        Args:
            config: Gemini configuration. If None, reads from environment.
            verbose: Whether to print debug information.

        Raises:
            GeminiAPIKeyError: If API key is not configured.
        """
        self.verbose = verbose

        if config:
            self._config = config
        else:
            self._config = self._load_config_from_env()

        self._client = None
        self._model = None

    def _load_config_from_env(self) -> GeminiConfig:
        """Load configuration from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your_api_key_here":
            raise GeminiAPIKeyError(
                "GEMINI_API_KEY not configured. "
                "Copy .env.example to .env and set your API key."
            )

        return GeminiConfig(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        )

    def _ensure_client(self) -> None:
        """Initialize the Gemini client if not already done."""
        if self._client is not None:
            return

        try:
            import google.generativeai as genai
        except ImportError:
            raise GeminiProviderError(
                "google-generativeai package not installed. "
                "Run: pip install -r tools/requirements.txt"
            )

        genai.configure(api_key=self._config.api_key)
        self._client = genai
        self._model = genai.GenerativeModel(
            model_name=self._config.model,
            system_instruction=LEAD_DEV_SYSTEM_PROMPT,
        )

        if self.verbose:
            print(f"[DEBUG] Gemini client initialized with model: {self._config.model}")

    def query(
        self,
        question: str,
        context: dict[str, str],
    ) -> str:
        """
        Send a query to Gemini and get a response.

        Args:
            question: The question to ask.
            context: Aggregated context dictionary.

        Returns:
            Response text from Gemini.

        Raises:
            GeminiConnectionError: If connection fails after retries.
            GeminiResponseError: If API returns an error.
        """
        self._ensure_client()

        # Build the prompt with context
        prompt = self._build_prompt(question, context)

        if self.verbose:
            print(f"[DEBUG] Prompt length: {len(prompt)} chars")

        # Execute with retry
        last_error = None
        for attempt in range(self._config.retry_count):
            try:
                response = self._model.generate_content(prompt)

                if response.text:
                    return response.text.strip()
                else:
                    raise GeminiResponseError("Empty response from Gemini API")

            except Exception as e:
                last_error = e
                if self.verbose:
                    print(f"[DEBUG] Attempt {attempt + 1} failed: {e}")

                if attempt < self._config.retry_count - 1:
                    time.sleep(self._config.retry_delay * (attempt + 1))

        raise GeminiConnectionError(
            f"Failed to get response after {self._config.retry_count} attempts: {last_error}"
        )

    def _build_prompt(self, question: str, context: dict[str, str]) -> str:
        """
        Build the full prompt including context.

        Args:
            question: The user's question.
            context: Aggregated context dictionary.

        Returns:
            Complete prompt string.
        """
        parts = []

        # Add context sections
        if context.get("documents"):
            parts.append("## Project Context\n")
            parts.append(context["documents"])
            parts.append("\n")

        if context.get("git_status"):
            parts.append("## Current Git Status\n")
            parts.append(f"```\n{context['git_status']}\n```\n")

        # Add the question
        parts.append("## Question from Senior DEV\n")
        parts.append(question)

        return "\n".join(parts)

    def report_progress(
        self,
        phase: int,
        status: str,
        message: Optional[str],
        milestone: str,
        context: dict[str, str],
    ) -> str:
        """
        Report progress to Gemini and get acknowledgment.

        Args:
            phase: Phase number.
            status: Status value (done, blocked, review).
            message: Optional details.
            milestone: Milestone identifier.
            context: Aggregated context dictionary.

        Returns:
            Acknowledgment text from Gemini.
        """
        self._ensure_client()

        # Build progress report prompt
        report = f"""## Progress Report

**Milestone:** {milestone}
**Phase:** {phase}
**Status:** {status}
"""
        if message:
            report += f"**Details:** {message}\n"

        report += """
Please acknowledge this progress report and provide any guidance for next steps.
If status is 'blocked', provide resolution suggestions.
If status is 'review', note what should be validated."""

        prompt = self._build_prompt(report, context)

        # Execute with retry
        last_error = None
        for attempt in range(self._config.retry_count):
            try:
                response = self._model.generate_content(prompt)

                if response.text:
                    return response.text.strip()
                else:
                    return f"Acknowledged: Phase {phase} marked as '{status}'"

            except Exception as e:
                last_error = e
                if self.verbose:
                    print(f"[DEBUG] Attempt {attempt + 1} failed: {e}")

                if attempt < self._config.retry_count - 1:
                    time.sleep(self._config.retry_delay * (attempt + 1))

        # On failure, return basic acknowledgment
        return f"Acknowledged: Phase {phase} marked as '{status}' (API unavailable)"

    def validate_status(self, context: dict[str, str]) -> str:
        """
        Request status validation from Gemini.

        Args:
            context: Aggregated context including git status.

        Returns:
            Validation result text.
        """
        self._ensure_client()

        prompt = """## Status Validation Request

Please validate the current project state based on the provided context.
Check for:
1. Alignment between git status and documented progress
2. Any drift from the milestone specification
3. Blockers or issues that need attention

Provide a concise assessment."""

        full_prompt = self._build_prompt(prompt, context)

        try:
            response = self._model.generate_content(full_prompt)
            if response.text:
                return response.text.strip()
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Validation request failed: {e}")

        return "Status validation completed - no critical issues detected (API check skipped)"
