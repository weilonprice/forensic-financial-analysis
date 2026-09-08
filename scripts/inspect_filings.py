#!/usr/bin/env python3
"""Walk the uploaded 10-K folders and report what's in them.

For every filing package found in `Latest 10k/` and `Past 10k/` this prints:
who filed it, what period it covers, every file in the package and what that
file is for, and the size of the extracted text we'd send to Claude.

    python scripts/inspect_filings.py
    python scripts/inspect_filings.py --dump extracted/   # save the text
    python scripts/inspect_filings.py --no-tokens         # skip the API call

Token counting uses the Anthropic API (the endpoint is free) and is skipped
automatically when ANTHROPIC_API_KEY isn't set.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic import filing as filing_mod
from forensic.filing import FileRole, Filing

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FOLDERS = ["Latest 10k", "Past 10k"]

#: Print order for the manifest — most analytically important first, rather
#: than alphabetical.
ROLE_ORDER = [
    FileRole.PRIMARY_DOCUMENT,
    FileRole.INSTANCE,
    FileRole.SCHEMA,
    FileRole.CALCULATION_LINKBASE,
    FileRole.PRESENTATION_LINKBASE,
    FileRole.DEFINITION_LINKBASE,
    FileRole.LABEL_LINKBASE,
    FileRole.EXHIBIT,
    FileRole.IMAGE,
    FileRole.OTHER,
]

ROLE_NOTES = {
    FileRole.PRIMARY_DOCUMENT: "the 10-K itself (inline XBRL)",
    FileRole.INSTANCE: "extracted XBRL instance",
    FileRole.SCHEMA: "filer's extension taxonomy",
    FileRole.CALCULATION_LINKBASE: "filer's own arithmetic (which items sum to which)",
    FileRole.PRESENTATION_LINKBASE: "statement ordering as presented",
    FileRole.DEFINITION_LINKBASE: "dimensions: segments, scenarios, axes",
    FileRole.LABEL_LINKBASE: "filer's chosen labels for each concept",
    FileRole.EXHIBIT: "filed exhibit",
    FileRole.IMAGE: "embedded image",
    FileRole.OTHER: "unclassified",
}


def rule(char: str = "─", width: int = 78) -> str:
    return char * width


def describe_identity(f: Filing) -> None:
    facts = f.facts
    name, firm_id, location = facts.auditor

    print(f"  Company           {f.company_name or '(not tagged)'}")
    print(f"  CIK               {f.cik or '(not tagged)'}")
    if facts.tickers:
        listing = ", ".join(facts.tickers)
        exchanges = ", ".join(dict.fromkeys(facts.exchanges))
        print(f"  Ticker(s)         {listing}" + (f"  on {exchanges}" if exchanges else ""))
    print(f"  Document          {facts.document_type or '?'}"
          f"   FY{facts.fiscal_year or '?'} {facts.fiscal_period or ''}".rstrip())
    print(f"  Period ending     {f.period_end.isoformat() if f.period_end else '(unparsed)'}")

    if facts.state_of_incorporation or facts.filer_category:
        print(f"  Incorporation     {facts.state_of_incorporation or '?'}"
              f"   ({facts.filer_category or 'filer category not tagged'})")
    if name:
        firm = f"{name}"
        if location:
            firm += f", {location}"
        if firm_id:
            firm += f"  [PCAOB {firm_id}]"
        print(f"  Auditor           {firm}")

    shares = facts.shares_outstanding
    if shares:
        total = f.shares_outstanding_total
        if len(shares) > 1:
            classes = " + ".join(f"{s:,.0f}" for s in shares)
            print(f"  Shares o/s        {total:,.0f}   ({len(shares)} classes: {classes})")
        else:
            print(f"  Shares o/s        {total:,.0f}")
    if facts.public_float is not None:
        print(f"  Public float      ${facts.public_float:,.0f}")

    if f.accession:
        acc = f.accession
        print(f"  Accession         {acc.raw}   filed {acc.filed_year}"
              f"   (filer CIK {acc.filer_cik})")


def describe_files(f: Filing) -> None:
    print(f"\n  Files ({len(f.files)}, {f.total_bytes / 1_048_576:.1f} MB total)")
    for role in ROLE_ORDER:
        for item in f.by_role(role):
            note = ROLE_NOTES.get(role, "")
            print(f"    {item.name:<38} {item.size_human:>10}   {note}")


def describe_content(f: Filing, *, count_tokens: bool, dump_dir: Path | None) -> None:
    numeric, non_numeric = f.fact_counts()
    print(f"\n  Tagged XBRL facts   {numeric:,} numeric, {non_numeric:,} non-numeric")

    text = f.document_text()
    print(f"  Extracted text      {len(text):,} characters")

    if count_tokens:
        try:
            from forensic.llm import create_client

            client = create_client()
            tokens = client.count_tokens(text)
            print(f"  Token count ({client.model}) {tokens:,}  "
                  f"({tokens / 1_000_000:.1%} of the 1M context window)")
        except Exception as exc:  # noqa: BLE001 - informational only
            print(f"  Token count         unavailable ({type(exc).__name__}: {exc})")

    # Prove the exhibits are readable too, not just the main document.
    for exhibit in f.exhibits:
        exhibit_text = f.exhibit_text(exhibit)
        first_line = next(
            (line for line in exhibit_text.splitlines() if len(line.strip()) > 25),
            "",
        )
        print(f"    {exhibit.name:<38} {len(exhibit_text):>7,} chars  "
              f"| {first_line[:44]}")

    if dump_dir is not None:
        dump_dir.mkdir(parents=True, exist_ok=True)
        stem = f.accession.raw if f.accession else f.root.name
        out = dump_dir / f"{stem}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"\n  Wrote text to       {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump", type=Path, default=None,
        help="directory to write extracted plain text into",
    )
    parser.add_argument(
        "--no-tokens", action="store_true",
        help="skip the Anthropic token-count call",
    )
    args = parser.parse_args()

    count_tokens = not args.no_tokens and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not args.no_tokens and not count_tokens:
        print("note: ANTHROPIC_API_KEY not set — skipping token counts\n")

    found_any = False
    exit_code = 0

    for folder_name in INPUT_FOLDERS:
        folder = PROJECT_ROOT / folder_name
        filings = filing_mod.discover(folder)

        print(rule("═"))
        print(f"{folder_name}/   —   {len(filings)} filing package(s)")
        print(rule("═"))

        if not filings:
            print("  (empty)\n")
            continue

        for f in filings:
            found_any = True
            print(f"\n  {f.root.name}")
            print(f"  {rule('─', 74)}")
            try:
                describe_identity(f)
                describe_files(f)
                describe_content(
                    f, count_tokens=count_tokens, dump_dir=args.dump
                )
            except Exception as exc:  # noqa: BLE001 - report and keep going
                print(f"  ERROR reading this package: {type(exc).__name__}: {exc}")
                exit_code = 1
                continue

            warnings = f.consistency_warnings()
            if warnings:
                print("\n  Warnings")
                for warning in warnings:
                    print(f"    ! {warning}")
            else:
                print("\n  No consistency warnings.")
            print()

    if not found_any:
        print("No filing packages found. Drop an extracted EDGAR XBRL folder "
              "into 'Latest 10k/'.")
        return 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
