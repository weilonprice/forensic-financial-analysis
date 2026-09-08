"""Unified LLM provider interface and client factory.

Supports both Claude (Anthropic) and Gemini (Google), allowing seamless switching
between models like `claude-opus-5` and `gemini-3.7-flash`.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable

from .claude import Answer, Claude, ClaudeError, Effort, Usage
from .gemini import Gemini, GeminiError

__all__ = [
    "Answer",
    "Claude",
    "ClaudeError",
    "Effort",
    "Gemini",
    "GeminiError",
    "LLMClient",
    "Usage",
    "create_client",
    "detect_provider",
    "require_api_key",
]


@runtime_checkable
class LLMClient(Protocol):
    """Protocol satisfied by both Claude and Gemini clients."""

    model: str

    def ask(
        self,
        question: str,
        *,
        document: str | None = None,
        system: str | None = None,
        effort: Effort | None = None,
        max_tokens: int | None = None,
        schema: dict[str, Any] | None = None,
        cache: bool = True,
    ) -> Answer:
        ...

    def count_tokens(self, text: str, *, system: str | None = None) -> int:
        ...


def detect_provider(model_or_provider: str | None = None) -> str:
    """Determine the provider ('gemini' or 'claude') from a name or env."""
    if model_or_provider:
        low = model_or_provider.lower()
        if "gemini" in low or "google" in low:
            return "gemini"
        if "claude" in low or "anthropic" in low or "opus" in low or "sonnet" in low or "haiku" in low:
            return "claude"

    env_provider = os.environ.get("LLM_PROVIDER")
    if env_provider:
        return "gemini" if "gemini" in env_provider.lower() else "claude"

    # Default to Gemini if GEMINI_API_KEY/GOOGLE_API_KEY is available and no ANTHROPIC_API_KEY
    if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) and not os.environ.get("ANTHROPIC_API_KEY"):
        return "gemini"

    # Default to claude otherwise
    return "claude"


def create_client(
    provider: str | None = None,
    model: str | None = None,
    *,
    effort: Effort = "high",
    **kwargs: Any,
) -> LLMClient:
    """Factory creating a configured Claude or Gemini client.

    Examples:
        create_client("gemini")                     # Gemini 3.7 Flash
        create_client(model="gemini-3.7-flash")     # Gemini 3.7 Flash
        create_client("claude")                     # Claude Opus 5
        create_client(model="claude-opus-5")        # Claude Opus 5
    """
    resolved_provider = provider or detect_provider(model)

    if resolved_provider == "gemini":
        model_name = model or "gemini-3.7-flash"
        return Gemini(model=model_name, effort=effort, **kwargs)

    model_name = model or "claude-opus-5"
    return Claude(model=model_name, effort=effort, **kwargs)


def require_api_key(provider: str | None = None, model: str | None = None) -> None:
    """Ensure the API key for the chosen provider is available."""
    resolved_provider = provider or detect_provider(model)
    if resolved_provider == "gemini":
        from .gemini import require_api_key as gemini_require_key
        gemini_require_key()
    else:
        from .claude import require_api_key as claude_require_key
        claude_require_key()
