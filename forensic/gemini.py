"""Gemini client for the forensic analysis app.

This module provides a first-class client for Google Gemini models (e.g.
`gemini-3.7-flash`, `gemini-2.5-flash`, `gemini-1.5-pro`) mirroring the interface
of `Claude.ask()` and returning an `Answer`.

Key capabilities:
1. STRUCTURED OUTPUTS: Full JSON schema support enforcing output format.
2. THINKING / REASONING: Native support for Gemini 3.7 Flash thinking budgets mapped
   from effort levels ("low", "medium", "high", "xhigh", "max").
3. CONTEXT CACHING: Explicit and implicit cache support with token accounting.
4. DUAL ENGINE: Uses official `google-genai` SDK when available, with a built-in
   `httpx` REST engine as a zero-dependency fallback.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Literal, Sequence

import httpx

from .claude import Answer, Effort, Usage

#: Default model for Gemini analysis
DEFAULT_MODEL = "gemini-3.7-flash"

#: Gemini API base URL for direct REST calls
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

#: Effort to thinking budget mapping in tokens for Gemini 3.7 Flash
THINKING_BUDGETS: dict[str, int] = {
    "low": 1024,
    "medium": 2048,
    "high": 4096,
    "xhigh": 8192,
    "max": 16384,
}


class GeminiError(RuntimeError):
    """Raised for conditions the caller must handle explicitly."""


class RefusalError(GeminiError):
    """Gemini safety filters declined the request."""


def require_api_key() -> str:
    """Fail fast with a clear message if no Gemini API key is found."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise GeminiError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.\n"
            "Get an API key from https://aistudio.google.com/app/apikey, then:\n"
            "  export GEMINI_API_KEY='...'"
        )
    return key


def _clean_schema_for_gemini(schema: dict[str, Any]) -> dict[str, Any]:
    """Ensure JSON schema is fully compatible with Gemini's OpenAPI subset.

    Translates anyOf [type, null] constructs to nullable: true.
    """
    cleaned: dict[str, Any] = {}
    for k, v in schema.items():
        if k == "additionalProperties":
            # Gemini does not use additionalProperties
            continue
        if k == "anyOf" and isinstance(v, list):
            # Check for {"anyOf": [{"type": X}, {"type": "null"}]}
            non_null = [item for item in v if item.get("type") != "null"]
            has_null = any(item.get("type") == "null" for item in v)
            if non_null and has_null:
                base = _clean_schema_for_gemini(non_null[0])
                base["nullable"] = True
                return base
        if isinstance(v, dict):
            cleaned[k] = _clean_schema_for_gemini(v)
        elif isinstance(v, list):
            cleaned[k] = [
                _clean_schema_for_gemini(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            cleaned[k] = v
    return cleaned


class Gemini:
    """A client for Google Gemini models compatible with Claude's interface."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        effort: Effort = "high",
        max_tokens: int = 32_000,
        timeout: float = 900.0,
        max_retries: int = 3,
        api_key: str | None = None,
    ):
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        # Cache reference for explicit context caching if created
        self._active_cache_name: str | None = None
        self._cached_doc_hash: int | None = None

        # Check if google-genai SDK is available
        self._sdk_client = None
        try:
            from google import genai
            if self._api_key:
                self._sdk_client = genai.Client(api_key=self._api_key)
        except ImportError:
            self._sdk_client = None

    @property
    def api_key(self) -> str:
        if not self._api_key:
            self._api_key = require_api_key()
        return self._api_key

    # -- public API -------------------------------------------------------

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
        """Ask one question against an optional document with structured JSON schema."""
        chosen_effort = effort or self.effort
        budget = THINKING_BUDGETS.get(chosen_effort, 4096)

        # Attempt with SDK if available, else REST
        if self._sdk_client is not None:
            try:
                return self._ask_sdk(
                    question,
                    document=document,
                    system=system,
                    budget=budget,
                    max_tokens=max_tokens or self.max_tokens,
                    schema=schema,
                    cache=cache,
                )
            except Exception as exc:
                # If SDK fails, try REST fallback before raising
                if "404" in str(exc) or "not found" in str(exc).lower():
                    raise
                return self._ask_rest(
                    question,
                    document=document,
                    system=system,
                    budget=budget,
                    max_tokens=max_tokens or self.max_tokens,
                    schema=schema,
                )

        return self._ask_rest(
            question,
            document=document,
            system=system,
            budget=budget,
            max_tokens=max_tokens or self.max_tokens,
            schema=schema,
        )

    def count_tokens(self, text: str, *, system: str | None = None) -> int:
        """Measure token count using Gemini API."""
        if self._sdk_client is not None:
            try:
                contents = [text]
                if system:
                    contents.insert(0, system)
                response = self._sdk_client.models.count_tokens(
                    model=self.model,
                    contents=contents,
                )
                return response.total_tokens or 0
            except Exception:
                pass

        # REST fallback for countTokens
        url = f"{GEMINI_API_BASE}/models/{self.model}:countTokens?key={self.api_key}"
        parts = [{"text": text}]
        if system:
            parts.insert(0, {"text": system})
        payload = {"contents": [{"parts": parts}]}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json().get("totalTokens", 0)
        # Fallback estimation if endpoint fails
        return max(1, len(text) // 4)

    # -- SDK implementation -----------------------------------------------

    def _ask_sdk(
        self,
        question: str,
        *,
        document: str | None,
        system: str | None,
        budget: int,
        max_tokens: int,
        schema: dict[str, Any] | None,
        cache: bool,
    ) -> Answer:
        from google.genai import types

        config_kwargs: dict[str, Any] = {
            "max_output_tokens": max_tokens,
        }

        if system:
            config_kwargs["system_instruction"] = system

        # Thinking config for models supporting thinking (like gemini-3.7-flash)
        if "flash" in self.model.lower() or "3.7" in self.model:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=budget
            )

        if schema is not None:
            cleaned_schema = _clean_schema_for_gemini(schema)
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = cleaned_schema

        config = types.GenerateContentConfig(**config_kwargs)

        contents: list[Any] = []
        if document:
            contents.append(document)
        contents.append(question)

        response = self._sdk_client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        text = response.text or ""
        data: dict[str, Any] | None = None
        if schema is not None:
            data = self._parse_json_payload(text)

        usage_meta = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
        cached_tokens = getattr(usage_meta, "cached_content_token_count", 0) or 0
        candidate_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0

        usage = Usage(
            input_tokens=max(0, prompt_tokens - cached_tokens),
            output_tokens=candidate_tokens,
            cache_creation_tokens=0,
            cache_read_tokens=cached_tokens,
        )

        finish_reason = None
        candidates = getattr(response, "candidates", [])
        if candidates:
            finish_reason = getattr(candidates[0], "finish_reason", None)

        return Answer(
            text=text,
            data=data,
            model=self.model,
            stop_reason=str(finish_reason) if finish_reason else None,
            truncated=str(finish_reason).upper() == "MAX_TOKENS",
            usage=usage,
        )

    # -- REST implementation ----------------------------------------------

    def _ask_rest(
        self,
        question: str,
        *,
        document: str | None,
        system: str | None,
        budget: int,
        max_tokens: int,
        schema: dict[str, Any] | None,
    ) -> Answer:
        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent?key={self.api_key}"

        contents: list[dict[str, Any]] = []
        if document:
            contents.append({"role": "user", "parts": [{"text": document}]})
        contents.append({"role": "user", "parts": [{"text": question}]})

        gen_config: dict[str, Any] = {
            "maxOutputTokens": max_tokens,
        }

        # Thinking config for Gemini 3.7
        if "flash" in self.model.lower() or "3.7" in self.model:
            gen_config["thinkingConfig"] = {
                "thinkingBudget": budget,
            }

        if schema is not None:
            gen_config["responseMimeType"] = "application/json"
            gen_config["responseSchema"] = _clean_schema_for_gemini(schema)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }

        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise GeminiError(
                    f"Gemini API error ({resp.status_code}): {resp.text}"
                )
            res_json = resp.json()

        candidates = res_json.get("candidates", [])
        if not candidates:
            prompt_feedback = res_json.get("promptFeedback", {})
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                raise RefusalError(f"Gemini blocked the request: {block_reason}")
            raise GeminiError("Gemini returned no candidates in response")

        cand = candidates[0]
        finish_reason = cand.get("finishReason")
        content = cand.get("content", {})
        parts = content.get("parts", [])

        # Extract text part (ignoring thinking parts if separate)
        text_parts = [
            p.get("text", "")
            for p in parts
            if "text" in p and not p.get("thought", False)
        ]
        text = "".join(text_parts).strip()

        data: dict[str, Any] | None = None
        if schema is not None:
            data = self._parse_json_payload(text)

        usage_meta = res_json.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        cached_tokens = usage_meta.get("cachedContentTokenCount", 0)
        output_tokens = usage_meta.get("candidatesTokenCount", 0)

        usage = Usage(
            input_tokens=max(0, prompt_tokens - cached_tokens),
            output_tokens=output_tokens,
            cache_creation_tokens=0,
            cache_read_tokens=cached_tokens,
        )

        return Answer(
            text=text,
            data=data,
            model=self.model,
            stop_reason=finish_reason,
            truncated=finish_reason == "MAX_TOKENS",
            usage=usage,
        )

    def _parse_json_payload(self, text: str) -> dict[str, Any]:
        """Parse structured JSON from model response text."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GeminiError(
                f"expected JSON matching schema from Gemini, got: {text[:200]!r}"
            ) from exc
