"""Claude client for the forensic analysis app.

This is the only module that talks to the Anthropic API. Everything else in the
app calls `Claude.ask()` and gets back an `Answer` — no other module imports
`anthropic` or knows about content blocks, streaming, or token accounting.

Three decisions are baked in here, and they are the whole reason this file
exists rather than callers using the SDK directly.

1. PROMPT CACHING. The app's shape is "one enormous document, many questions."
   A 10-K runs 100k-300k tokens; the question is a few hundred. Sent naively,
   every question re-bills the entire filing at full input price. So the
   document goes in its own content block with a cache breakpoint, and the
   question goes in a block *after* it. The cached prefix is then reused by
   every subsequent question, at roughly a tenth of the input cost.

   Caching is a *prefix match* on exact bytes: the cached span is everything
   from the start of the request up to the breakpoint. Anything that varies
   between questions must therefore come after it. That is the single
   invariant this module protects — see `_build_messages`.

2. STREAMING. Large inputs and long answers push a non-streaming request past
   the SDK's HTTP timeout. We always stream and reassemble with
   `get_final_message()`, so we get timeout safety without the caller having to
   handle stream events.

3. REFUSALS. Claude Opus 5 runs safety classifiers that can decline a request.
   That arrives as a *successful* HTTP 200 with `stop_reason == "refusal"` and
   an empty or partial `content` — so code that reads `content[0].text`
   unconditionally raises an IndexError on a response that never errored. We
   check `stop_reason` first, always.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

import anthropic

#: Opus 5 is the default: forensic reading of a filing is exactly the kind of
#: careful, high-stakes analysis where the strongest model earns its cost.
DEFAULT_MODEL = "claude-opus-5"

#: Effort controls how much the model thinks and works before answering.
#: "high" is the API default; "xhigh" and "max" go deeper for harder analysis.
Effort = Literal["low", "medium", "high", "xhigh", "max"]

#: Cache lifetime. "5m" costs 1.25x to write, "1h" costs 2x. A 10-K analysis
#: run issues many questions over many minutes, and re-writing a 200k-token
#: cache is far more expensive than the higher write premium, so "1h" is the
#: default. Drop to "5m" for tight back-to-back question loops.
CacheTTL = Literal["5m", "1h"]


class ClaudeError(RuntimeError):
    """Raised for conditions the caller must handle explicitly."""


class RefusalError(ClaudeError):
    """Claude's safety classifiers declined the request.

    Carries the policy category so the caller can distinguish "this filing
    tripped a classifier" from an ordinary failure.
    """

    def __init__(self, category: str | None, explanation: str | None):
        self.category = category
        self.explanation = explanation
        super().__init__(
            f"Claude declined the request (category={category!r}): "
            f"{explanation or 'no explanation provided'}"
        )


# --------------------------------------------------------------------------- usage


@dataclass(frozen=True)
class Usage:
    """Token accounting for one call.

    Worth surfacing rather than hiding: on this app's workload the difference
    between a cache hit and a cache miss is roughly 10x the input cost, and the
    only way to know which happened is to read these numbers.
    """

    input_tokens: int          # billed at full price (the question, mostly)
    output_tokens: int         # the answer, plus thinking tokens
    cache_creation_tokens: int # written to cache this call (~1.25x or 2x price)
    cache_read_tokens: int     # served from cache this call (~0.1x price)

    @property
    def cache_hit(self) -> bool:
        return self.cache_read_tokens > 0

    @property
    def total_input(self) -> int:
        """Full prompt size. `input_tokens` alone is only the *uncached*
        remainder — reading it as the prompt size understates a cached
        request by orders of magnitude."""
        return self.input_tokens + self.cache_creation_tokens + self.cache_read_tokens

    def summary(self) -> str:
        state = (
            f"cache HIT {self.cache_read_tokens:,}"
            if self.cache_hit
            else f"cache WRITE {self.cache_creation_tokens:,}"
            if self.cache_creation_tokens
            else "uncached"
        )
        return (
            f"{self.total_input:,} in / {self.output_tokens:,} out ({state})"
        )


@dataclass(frozen=True)
class Answer:
    """One question, answered."""

    text: str
    usage: Usage
    model: str
    stop_reason: str | None
    #: True when the answer was cut off by `max_tokens` rather than finishing.
    #: Silently treating a truncated answer as complete is how a forensic
    #: finding loses its conclusion, so callers should check this.
    truncated: bool
    #: Parsed JSON, when the call supplied a schema. `None` otherwise.
    data: dict[str, Any] | None = None


# -------------------------------------------------------------------------- client


class Claude:
    """A thin, opinionated wrapper over the Messages API."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        effort: Effort = "high",
        max_tokens: int = 32_000,
        cache_ttl: CacheTTL = "1h",
        thinking_display: Literal["omitted", "summarized"] = "omitted",
        timeout: float = 900.0,
        max_retries: int = 3,
        client: anthropic.Anthropic | None = None,
    ):
        """
        `max_tokens` is a hard ceiling on thinking *plus* answer text. Thinking
        is on by default on Opus 5, so a limit sized only for the prose will
        truncate the answer. 32k leaves room for both.

        `timeout` is generous because a high-effort question against a full
        10-K legitimately takes minutes. The SDK retries connection errors,
        429s, and 5xx automatically (`max_retries`).

        `client` is injectable so tests can pass a fake and never hit the
        network.
        """
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.cache_ttl = cache_ttl
        self.thinking_display = thinking_display
        # No api_key argument: the SDK resolves ANTHROPIC_API_KEY (or an
        # `ant auth login` profile) from the environment. Keeping the key out
        # of this code means it can never be committed by accident.
        self._client = client or anthropic.Anthropic(
            timeout=timeout, max_retries=max_retries
        )

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
        """Ask one question, optionally against a cached document.

        Pass the *same* `document` and `system` strings across calls to reuse
        the cache. Any change to either — even a whitespace edit — invalidates
        the cached prefix and re-bills the whole filing.

        `schema` invalidates it too, which is easy to miss: the render order is
        tools -> system -> messages, so a different schema changes the prefix
        *ahead* of the document and the document caches separately under it.
        Set `cache=False` when a schema is used only once or twice in a run.
        At the 1h TTL a write costs 2x base and a read 0.1x, so a prefix that
        is written and never read costs double what not caching it would; the
        break-even is three uses.

        When `schema` is a JSON Schema, the API *constrains* the response to
        match it and `Answer.data` holds the parsed object. This is stronger
        than asking for JSON in the prompt: the model cannot emit prose around
        it, cannot omit a required field, and cannot return a score as "8/10"
        instead of 8. For structured findings that later get sorted and
        aggregated, that guarantee is the difference between a data pipeline
        and a regex that works until it doesn't.
        """
        output_config: dict[str, Any] = {"effort": effort or self.effort}
        if schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": schema}

        response = self._client.messages.stream(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=self._build_system(system),
            messages=self._build_messages(question, document, cache=cache),
            output_config=output_config,
            thinking={"type": "adaptive", "display": self.thinking_display},
        )
        with response as stream:
            message = stream.get_final_message()

        return self._to_answer(message, expect_json=schema is not None)

    def count_tokens(self, text: str, *, system: str | None = None) -> int:
        """Measure a document before sending it.

        Used to decide whether a filing fits the context window and to estimate
        cost up front. Never estimate Claude tokens with `tiktoken` or a
        characters/4 rule — both are wrong for this tokenizer, and wrong by
        enough to matter on a 300k-token filing.
        """
        result = self._client.messages.count_tokens(
            model=self.model,
            system=self._build_system(system),
            messages=[{"role": "user", "content": text}],
        )
        return result.input_tokens

    # -- request construction --------------------------------------------

    def _build_system(self, system: str | None) -> Any:
        """System prompt as a plain string, or omitted.

        Deliberately *not* cached here. Render order is tools -> system ->
        messages, so the breakpoint on the document block (which comes later)
        already covers the system prompt. One breakpoint, everything before it
        cached — no need to spend a second of the four available.
        """
        return system if system is not None else anthropic.NOT_GIVEN

    def _build_messages(self, question: str, document: str | None,
                        *, cache: bool = True) -> list[dict]:
        """Assemble the user turn with the cache breakpoint in the right place.

        Block order is load-bearing:

            [0] document  <- cache_control breakpoint (stable across questions)
            [1] question  <- varies every call, must come AFTER the breakpoint

        Reversing these would put varying bytes inside the cached prefix, and
        every request would write a brand-new cache entry that nothing ever
        reads — paying the write premium for zero benefit. The failure is
        silent: correct answers, quietly multiplied cost. `Usage.cache_hit` is
        how you catch it.

        `cache=False` omits the breakpoint entirely, for requests whose prefix
        no later request will share. That is not the same as the block order
        being wrong — the document still needs to precede the question — it is
        the case where caching this prefix at all is the mistake.
        """
        blocks: list[dict] = []

        if document is not None:
            block: dict[str, Any] = {"type": "text", "text": document}
            if cache:
                block["cache_control"] = {
                    "type": "ephemeral", "ttl": self.cache_ttl,
                }
            blocks.append(block)

        blocks.append({"type": "text", "text": question})
        return [{"role": "user", "content": blocks}]

    # -- response handling ------------------------------------------------

    def _to_answer(self, message: Any, *, expect_json: bool = False) -> Answer:
        # Check stop_reason BEFORE touching content. On a refusal the content
        # list can be empty, and indexing it would raise IndexError on an
        # HTTP 200 — an error that looks like a bug in our parsing rather than
        # a policy decision by the API.
        if message.stop_reason == "refusal":
            details = getattr(message, "stop_details", None)
            raise RefusalError(
                category=getattr(details, "category", None),
                explanation=getattr(details, "explanation", None),
            )

        text = "".join(
            block.text for block in message.content if block.type == "text"
        )

        data: dict[str, Any] | None = None
        if expect_json:
            # A truncated response is invalid JSON, and the resulting decode
            # error is far more confusing than the real cause. Say the real
            # cause.
            if message.stop_reason == "max_tokens":
                raise ClaudeError(
                    "response hit max_tokens before the JSON was complete — "
                    "raise max_tokens or lower effort"
                )
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ClaudeError(
                    f"expected JSON matching the schema, got: {text[:200]!r}"
                ) from exc

        usage = message.usage
        return Answer(
            text=text,
            data=data,
            model=message.model,
            stop_reason=message.stop_reason,
            truncated=message.stop_reason == "max_tokens",
            usage=Usage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            ),
        )


def require_api_key() -> None:
    """Fail fast with a useful message instead of a 401 from deep in a run."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ClaudeError(
            "ANTHROPIC_API_KEY is not set.\n"
            "Get a key from https://console.anthropic.com/settings/keys, then:\n"
            "  export ANTHROPIC_API_KEY='...'"
        )
