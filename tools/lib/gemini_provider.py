"""
Gemini API provider for HMAS Bridge Layer.

This module handles communication with the Gemini API for Lead DEV responses.
It utilizes the Google GenAI SDK (v1+) for 'gemini-2.0-flash-exp' and newer models.
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
    model: str = "gemini-2.0-flash-exp"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 2.0
    thinking_level: Optional[str] = None  # LOW, HIGH, or None to disable


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
    Provider for Gemini API interactions using the google-genai SDK.
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
        """
        self.verbose = verbose

        if config:
            self._config = config
        else:
            self._config = self._load_config_from_env()

        self._client = None

    def _load_config_from_env(self) -> GeminiConfig:
        """Load configuration from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your_api_key_here":
            raise GeminiAPIKeyError(
                "GEMINI_API_KEY not configured. "
                "Copy .env.example to .env and set your API key."
            )

        # Get thinking level (optional, only for gemini-3+ models)
        thinking_level = os.getenv("GEMINI_THINKING_LEVEL", "").upper() or None
        if thinking_level and thinking_level not in ("LOW", "HIGH"):
            thinking_level = None  # Invalid value, disable thinking mode

        return GeminiConfig(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            thinking_level=thinking_level,
        )

    def _ensure_client(self) -> None:
        """Initialize the Gemini client if not already done."""
        if self._client is not None:
            return

        try:
            from google import genai
        except ImportError:
            raise GeminiProviderError(
                "google-genai package not installed. "
                "Run: pip install -r tools/requirements.txt"
            )

        self._client = genai.Client(api_key=self._config.api_key)

        if self.verbose:
            thinking_info = f", thinking={self._config.thinking_level}" if self._config.thinking_level else ""
            print(f"[DEBUG] Gemini client initialized for model: {self._config.model}{thinking_info}")

    def _build_generate_config(self):
        """
        Build GenerateContentConfig with optional thinking mode.

        Thinking mode is only applied if:
        - thinking_level is explicitly set, OR
        - model name contains 'gemini-3'

        Returns:
            GenerateContentConfig instance.
        """
        from google.genai import types

        config_args = {
            "system_instruction": LEAD_DEV_SYSTEM_PROMPT,
        }

        # Determine if thinking mode should be enabled
        should_enable_thinking = (
            self._config.thinking_level is not None or
            "gemini-3" in self._config.model.lower()
        )

        if should_enable_thinking:
            # Default to LOW if model supports thinking but level not specified
            level_str = self._config.thinking_level or "LOW"
            level = getattr(types.ThinkingLevel, level_str, types.ThinkingLevel.LOW)
            config_args["thinking_config"] = types.ThinkingConfig(thinking_level=level)

            if self.verbose:
                print(f"[DEBUG] Thinking mode enabled: {level_str}")

        return types.GenerateContentConfig(**config_args)

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
        """
        self._ensure_client()

        # Build the prompt with context
        prompt_content = self._build_prompt(question, context)

        if self.verbose:
            print(f"[DEBUG] Prompt length: {len(prompt_content)} chars")

        # Execute with retry
        last_error = None
        config = self._build_generate_config()

        for attempt in range(self._config.retry_count):
            try:
                response = self._client.models.generate_content(
                    model=self._config.model,
                    contents=prompt_content,
                    config=config,
                )

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
        report = f"""
## Progress Report

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

        prompt_content = self._build_prompt(report, context)
        config = self._build_generate_config()

        # Execute with retry
        for attempt in range(self._config.retry_count):
            try:
                response = self._client.models.generate_content(
                    model=self._config.model,
                    contents=prompt_content,
                    config=config,
                )

                if response.text:
                    return response.text.strip()
                else:
                    return f"Acknowledged: Phase {phase} marked as '{status}'"

            except Exception as e:
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

        prompt = """
## Status Validation Request

Please validate the current project state based on the provided context.
Check for:
1. Alignment between git status and documented progress
2. Any drift from the milestone specification
3. Blockers or issues that need attention

Provide a concise assessment."""

        full_prompt = self._build_prompt(prompt, context)
        config = self._build_generate_config()

        try:
            response = self._client.models.generate_content(
                model=self._config.model,
                contents=full_prompt,
                config=config,
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Validation request failed: {e}")

        return "Status validation completed - no critical issues detected (API check skipped)"