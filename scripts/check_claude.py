#!/usr/bin/env python3
"""Verify the Claude client works end to end.

Run this after setting ANTHROPIC_API_KEY. It proves three things:

  1. Credentials and model access work.
  2. Token counting works (how we'll size a filing before sending it).
  3. Prompt caching actually engages — the second question against the same
     document must report a cache READ, not another WRITE.

Check 3 is the one that matters. Caching failures are silent: answers stay
correct while cost quietly multiplies. This is the test that catches it.

    python scripts/check_claude.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic.claude import Claude, ClaudeError, RefusalError, require_api_key

# A stand-in for a filing. The cache has a minimum size — a prefix below the
# model's threshold silently will not cache, so a toy two-line document would
# make this test report a false failure. This is padded well past it.
FAKE_FILING = (
    "NOTE 3 — REVENUE RECOGNITION\n\n"
    "The Company recognizes revenue when control of promised goods or services "
    "transfers to the customer, in an amount reflecting the consideration the "
    "Company expects to be entitled to in exchange for those goods or services.\n\n"
    + "\n".join(
        f"Segment {i}: revenue of ${i * 1_250:,} thousand, cost of revenue of "
        f"${i * 780:,} thousand, and accounts receivable of ${i * 410:,} thousand "
        f"at period end, compared to ${i * 300:,} thousand in the prior period."
        for i in range(1, 120)
    )
)


def main() -> int:
    try:
        require_api_key()
    except ClaudeError as exc:
        print(f"FAIL  {exc}")
        return 1

    claude = Claude()
    print(f"Model: {claude.model}   effort={claude.effort}   cache_ttl={claude.cache_ttl}")

    # -- 1. token counting -------------------------------------------------
    try:
        doc_tokens = claude.count_tokens(FAKE_FILING)
    except Exception as exc:  # noqa: BLE001 - surface the real failure
        print(f"FAIL  token counting: {type(exc).__name__}: {exc}")
        return 1
    print(f"PASS  token counting — test document is {doc_tokens:,} tokens")

    # -- 2. a question against the document (writes the cache) -------------
    try:
        first = claude.ask(
            "In one sentence, what does Note 3 describe?",
            document=FAKE_FILING,
        )
    except RefusalError as exc:
        print(f"FAIL  request refused: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  first request: {type(exc).__name__}: {exc}")
        return 1

    print(f"PASS  first request  — {first.usage.summary()}")
    print(f"      answer: {first.text.strip()[:160]}")

    # -- 3. a DIFFERENT question, SAME document (must read the cache) ------
    # Same document bytes, different question. If the breakpoint is placed
    # correctly the document is served from cache and only the new question is
    # billed at full price.
    second = claude.ask(
        "In one sentence, what is the largest segment by revenue?",
        document=FAKE_FILING,
    )
    print(f"PASS  second request — {second.usage.summary()}")
    print(f"      answer: {second.text.strip()[:160]}")

    if not second.usage.cache_hit:
        print(
            "\nFAIL  caching did not engage on the second request.\n"
            "      Every question would re-bill the full filing. Check that the\n"
            "      document block carries cache_control and precedes the question."
        )
        return 1

    saved = second.usage.cache_read_tokens
    print(
        f"\nPASS  caching engaged — {saved:,} tokens served from cache on the "
        f"second question\n      (billed at roughly a tenth of full input price)."
    )
    print("\nBrick 1 is working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
