#!/usr/bin/env python3
"""Verify the Gemini client works end to end.

Run this after setting GEMINI_API_KEY (or GOOGLE_API_KEY). It proves:

  1. Credentials and model access work (defaulting to gemini-3.7-flash).
  2. Token counting works.
  3. Structured JSON output schema validation works.
  4. Thinking/reasoning configuration succeeds.

    python scripts/check_gemini.py
    python scripts/check_gemini.py --model gemini-3.7-flash
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic.gemini import Gemini, GeminiError, RefusalError, require_api_key

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

SAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "One sentence summary."},
        "largest_segment_number": {"type": "integer", "description": "The segment number with the highest revenue."},
    },
    "required": ["summary", "largest_segment_number"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3.7-flash",
                        help="Gemini model name (default: gemini-3.7-flash)")
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"],
                        help="Thinking effort level")
    args = parser.parse_args()

    try:
        require_api_key()
    except GeminiError as exc:
        print(f"FAIL  {exc}")
        return 1

    gemini = Gemini(model=args.model, effort=args.effort)
    print(f"Model: {gemini.model}   effort={gemini.effort}")

    # -- 1. token counting -------------------------------------------------
    try:
        doc_tokens = gemini.count_tokens(FAKE_FILING)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  token counting: {type(exc).__name__}: {exc}")
        return 1
    print(f"PASS  token counting — test document is {doc_tokens:,} tokens")

    # -- 2. standard question ----------------------------------------------
    try:
        first = gemini.ask(
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

    # -- 3. structured JSON schema output with thinking -------------------
    try:
        second = gemini.ask(
            "Summarize the filing note and identify the largest segment number by revenue.",
            document=FAKE_FILING,
            schema=SAMPLE_SCHEMA,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  structured output request: {type(exc).__name__}: {exc}")
        return 1

    print(f"PASS  structured JSON schema request — {second.usage.summary()}")
    print(f"      parsed data: {json.dumps(second.data)}")

    if not second.data or "largest_segment_number" not in second.data:
        print("FAIL  structured output did not contain expected fields")
        return 1

    print("\nALL CHECKS PASSED for Gemini client.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
