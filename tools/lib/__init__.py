"""
HMAS Bridge Layer Library

Shared modules for Bridge Layer tools that enable communication
between Senior DEV (Claude Code) and Lead DEV (Gemini).
"""

from .config import Config
from .context import ContextAggregator
from .interface import LeadDevInterface
from .gemini_provider import (
    GeminiProvider,
    GeminiConfig,
    GeminiProviderError,
    GeminiAPIKeyError,
    GeminiConnectionError,
    GeminiResponseError,
)

__all__ = [
    "Config",
    "ContextAggregator",
    "LeadDevInterface",
    "GeminiProvider",
    "GeminiConfig",
    "GeminiProviderError",
    "GeminiAPIKeyError",
    "GeminiConnectionError",
    "GeminiResponseError",
]
