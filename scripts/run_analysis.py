#!/usr/bin/env python3
"""Run every question set against the uploaded filing.

    python scripts/run_analysis.py
    python scripts/run_analysis.py --set mda           # one set only
    python scripts/run_analysis.py --only 1,6,13       # a subset of questions
    python scripts/run_analysis.py --workers 1         # sequential
    python scripts/run_analysis.py --effort xhigh

Writes one JSON record and one Markdown report into `output/`, with a section
per question set.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic import analysis, questions as questions_mod, sections
from forensic.report_pdf import build_pdf
from forensic.llm import LLMClient, create_client, detect_provider, require_api_key
from forensic.filing import discover
from forensic.analysis import ConcernLevel
from forensic.questions import QuestionKind, QuestionSet

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Folder names the prior-year filing has been dropped into. Checked in order;
#: several exist in the project and only one holds a filing.
PRIOR_YEAR_FOLDERS = ["Previous Year 10k", "Past 10k", "Previous 10k"]

#: Sections pulled out of both filings and pinned in front of the full text.
SECTION_SPECS = [sections.AUDIT_REPORT, sections.MDA,
                 sections.FINANCIAL_STATEMENTS]

#: Per-company sector, keyed by CIK. Needed for benchmark comparisons like the
#: DSO task, and available nowhere else: a 10-K carries no SIC, NAICS or GICS
#: tag, so this cannot be read from the filing.
#:
#: Optional manual override, keyed by CIK. Nothing needs to be in it — the
#: sector is classified automatically — but an entry here wins over the
#: classification, for a company where you disagree with the call.
#:
#: Precedence: --sector, then sectors.json, then classification.
SECTOR_MAP_PATH = PROJECT_ROOT / "sectors.json"


def load_sector(cik: str | None, override: str | None) -> tuple[str | None, str]:
    """Resolve the sector for this filing. Returns (sector, where it came from).

    Returns None rather than falling back to a default: a wrong sector produces
    a confident benchmark against the wrong band, which is worse than no
    benchmark at all.
    """
    if override:
        return override, "--sector"
    if SECTOR_MAP_PATH.exists():
        try:
            entries = json.loads(SECTOR_MAP_PATH.read_text())
        except json.JSONDecodeError as exc:
            print(f"  WARNING: {SECTOR_MAP_PATH.name} is not valid JSON ({exc}）")
            entries = {}
        entry = entries.get(cik or "")
        if isinstance(entry, dict):
            entry = entry.get("sector")
        if entry:
            return str(entry), SECTOR_MAP_PATH.name
    return None, "unresolved"


def load_prior_filing():
    for name in PRIOR_YEAR_FOLDERS:
        found = discover(PROJECT_ROOT / name)
        if found:
            return found[0]
    return None


# ------------------------------------------------------------------ rendering


def _render_task(result: analysis.QuestionResult, add) -> None:
    """Render a table task as real Markdown tables."""
    data = result.data or {}
    slug = result.question.task_slug

    if slug == "dso_data_entry":
        header, rows = analysis.dso_table(data)
        add("| " + " | ".join(h or " " for h in header) + " |")
        add("|" + "---|" * len(header))
        for row in rows:
            add("| " + " | ".join(row) + " |")
        add("")
    elif slug == "dso_analysis":
        add("| | |")
        add("|---|---|")
        for label, value in analysis.dso_analysis_rows(data):
            add(f"| **{label}** | {value} |")
        add("")


def _render_question(result: analysis.QuestionResult, add) -> None:
    add(f"### {result.question.display_id}. {result.label}")
    add("")
    if not result.ok and not result.answer:
        add(f"> **Failed to run:** {result.error}")
        add("")
        return

    add(result.answer)
    add("")
    if result.question.kind is QuestionKind.TABLE:
        _render_task(result, add)
    if result.concern:
        add(f"**Concern:** {result.concern}")
        add("")
    if result.has_level:
        add(f"**Concern level:** {result.concern_level.label}")
        add("")

    if result.unverified:
        add(f"> ⚠️ **{len(result.unverified)} quotation(s) not found in the "
            "filing** — this answer cites text that could not be located:")
        for quote in result.unverified:
            add(f"> - `{' '.join(quote.split())[:200]}`")
        add("")
    if result.evidence:
        verified = len(result.evidence) - len(result.unverified)
        add(f"<details><summary>Evidence ({len(result.evidence)} quotation(s), "
            f"{verified} verified)</summary>")
        add("")
        for quote in result.evidence:
            mark = "  ❌ NOT FOUND" if quote in result.unverified else ""
            add(f"- \"{' '.join(quote.split())[:400]}\"{mark}")
        add("")
        add("</details>")
        add("")


def render_markdown(runs: list[analysis.AnalysisRun],
                    workspace: analysis.Workspace) -> str:
    filing = workspace.filing
    facts = filing.facts
    lines: list[str] = []
    add = lines.append

    add(f"# Forensic Analysis — {facts.company_name}")
    add("")
    add(f"**{facts.document_type} for fiscal year {facts.fiscal_year}**, "
        f"period ending {filing.period_end}")
    add("")
    add(f"- CIK {facts.cik}"
        + (f" · accession {filing.accession.raw}" if filing.accession else ""))
    if workspace.prior_filing is not None:
        prior = workspace.prior_filing
        add(f"- Compared against {prior.facts.document_type} FY{prior.fiscal_year}"
            + (f" (accession {prior.accession.raw})" if prior.accession else ""))
    for bundle in workspace.bundles:
        if bundle.current is None:
            continue
        prior_note = (f", prior {bundle.prior.length:,}" if bundle.prior else "")
        add(f"- Section located: {bundle.spec.title} "
            f"({bundle.current.length:,} chars{prior_note})")
    if runs:
        add(f"- Model: {runs[0].model} · run {runs[0].started_at}")
    add("")
    add("Concern levels throughout: **none · minor · material · severe**. "
        "Material and above are flagged.")
    add("")

    # -- overview across sets ---------------------------------------------
    add("## Overview")
    add("")
    add("| Section | Questions | Severe | Material | Minor | None | "
        "Worst | Unverified quotes |")
    add("|---|---|---|---|---|---|---|---|")
    for run in runs:
        counts = run.distribution
        worst = run.worst.label if run.worst is not None else "—"
        add(f"| {run.question_set.name} | {len(run.results)} "
            f"| {counts[ConcernLevel.SEVERE]} | {counts[ConcernLevel.MATERIAL]} "
            f"| {counts[ConcernLevel.MINOR]} | {counts[ConcernLevel.NONE]} "
            f"| {worst} | {run.unverified_count} |")
    add("")

    total_unverified = sum(r.unverified_count for r in runs)
    total_evidence = sum(r.evidence_count for r in runs)
    if total_unverified:
        add(f"⚠️ **{total_unverified} of {total_evidence} cited quotations could "
            "not be found in the filing.** Treat those answers as unsupported "
            "until checked by hand.")
    else:
        add(f"All {total_evidence} cited quotations verified against the filing text.")
    add("")

    # -- one block per set ------------------------------------------------
    for run in runs:
        add("---")
        add("")
        add(f"# {run.question_set.name}")
        add("")

        for result in run.summaries:
            add("## Summary")
            add("")
            add(result.answer)
            add("")
            limit = result.question.max_chars
            note = f"{len(result.answer)} characters"
            if limit:
                note += (f" (limit {limit}) — "
                         f"{'OVER LIMIT' if result.error else 'within limit'}")
            add(f"_{note}_")
            add("")

        flagged = run.flagged()
        add("## Flagged")
        add("")
        if flagged:
            for result in flagged:
                add(f"- **{result.concern_level.label} — "
                    f"{result.question.display_id}.** "
                    f"{result.label} {result.concern}")
        else:
            add("No question reached material concern.")
        add("")

        add("| # | Question | Concern |")
        add("|---|---|---|")
        for result in run.results:
            if result.question.kind is QuestionKind.SUMMARY:
                level = "summary"
            elif result.ok and result.has_level:
                level = result.concern_level.label
            elif result.ok:
                level = "table"
            else:
                level = "ERROR"
            topic = result.label.replace("|", "\\|")
            add(f"| {result.question.display_id} | {topic} | {level} |")
        add("")

        add("## Findings")
        add("")
        for result in run.results:
            if result.question.kind is QuestionKind.SUMMARY:
                continue  # rendered above
            _render_question(result, add)

    usage_in = sum(r.total_usage.total_input for r in runs)
    usage_out = sum(r.total_usage.output_tokens for r in runs)
    cached = sum(r.total_usage.cache_read_tokens for r in runs)
    elapsed = sum(r.elapsed_seconds for r in runs)
    add("---")
    add("")
    add(f"_{sum(len(r.results) for r in runs)} questions in {elapsed:.0f}s. "
        f"Tokens: {usage_in:,} in / {usage_out:,} out; {cached:,} from cache._")
    return "\n".join(lines)


def to_json(runs: list[analysis.AnalysisRun],
            workspace: analysis.Workspace,
            sector_for_json: str | None = None,
            sector_source_for_json: str = "") -> dict:
    filing = workspace.filing
    facts = filing.facts
    prior = workspace.prior_filing
    return {
        "filing": {
            "company": facts.company_name,
            "cik": facts.cik,
            "document_type": facts.document_type,
            "fiscal_year": facts.fiscal_year,
            "period_end": filing.period_end.isoformat() if filing.period_end else None,
            "accession": filing.accession.raw if filing.accession else None,
            "source_folder": filing.source_label,
            # Recorded so any past run can be audited for which benchmark band
            # it used, and where that sector came from.
            "sector": sector_for_json,
            "sector_source": sector_source_for_json,
        },
        "prior_filing": None if prior is None else {
            "fiscal_year": prior.fiscal_year,
            "period_end": prior.period_end.isoformat() if prior.period_end else None,
            "accession": prior.accession.raw if prior.accession else None,
            "source_folder": prior.source_label,
        },
        "sections": [
            {
                "key": b.spec.key,
                "title": b.spec.title,
                "current_chars": b.current.length if b.current else 0,
                "prior_chars": b.prior.length if b.prior else 0,
            }
            for b in workspace.bundles
        ],
        "sets": [
            {
                "name": run.question_set.name,
                "section": run.question_set.section_key,
                "question_file": str(run.question_set.path),
                "model": run.model,
                "started_at": run.started_at,
                "elapsed_seconds": round(run.elapsed_seconds, 1),
                "distribution": {level.value: count
                                 for level, count in run.distribution.items()},
                "worst": run.worst.value if run.worst is not None else None,
                "results": [
                    {
                        "number": r.question.number,
                        "display_id": r.question.display_id,
                        "task_slug": r.question.task_slug,
                        "kind": r.question.kind.value,
                        "auto_numbered": r.question.auto_numbered,
                        "max_chars": r.question.max_chars,
                        "title": r.title,
                        "label": r.label,
                        "topic": r.question.topic,
                        "question": r.question.text,
                        "answer": r.answer,
                        "concern": r.concern,
                        "concern_level": (r.concern_level.value
                                          if (r.ok and r.has_level) else None),
                        "data": r.data,
                        "evidence": r.evidence,
                        "unverified_evidence": r.unverified,
                        "attempts": r.attempts,
                        "error": r.error,
                        "usage": dataclasses.asdict(r.usage) if r.usage else None,
                    }
                    for r in run.results
                ],
            }
            for run in runs
        ],
    }


# ----------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # 3, not 4: each request carries ~120k input tokens, and four in flight was
    # enough to trip the input-token-per-minute limit.
    parser.add_argument("--workers", type=int, default=3,
                        help="parallel questions after the first (default 3)")
    parser.add_argument("--provider", default=None, choices=["claude", "gemini"],
                        help="LLM provider (claude or gemini; auto-detected if omitted)")
    parser.add_argument("--model", default=None,
                        help="model name (e.g. gemini-3.7-flash, claude-opus-5)")
    parser.add_argument("--only", type=str, default=None,
                        help="comma-separated question numbers to run")
    parser.add_argument("--set", dest="set_filter", type=str, default=None,
                        help="run only sets whose name or section key matches")
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "output")
    parser.add_argument("--sector", default=None,
                        help="S&P 500 sector for benchmarks; overrides sectors.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="load everything and report what was found, then "
                             "stop before the first API call")
    parser.add_argument("--no-pdf", action="store_true",
                        help="skip the PDF report")
    parser.add_argument("--pdf-evidence", action="store_true",
                        help="include every supporting quotation in the PDF")
    args = parser.parse_args()

    provider = args.provider or detect_provider(args.model)
    model_name = args.model or ("gemini-3.7-flash" if provider == "gemini" else "claude-opus-5")

    try:
        require_api_key(provider=provider, model=model_name)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}")
        return 1

    filings = discover(PROJECT_ROOT / "Latest 10k")
    if not filings:
        print("error: no filing found in 'Latest 10k/'")
        return 1
    filing = filings[0]
    prior = load_prior_filing()

    question_sets = questions_mod.discover(PROJECT_ROOT / "Analysis Questions")
    if not question_sets:
        print("error: no question sets found in 'Analysis Questions/'")
        return 1

    if args.set_filter:
        needle = args.set_filter.lower()
        question_sets = [
            s for s in question_sets
            if needle in s.name.lower() or needle == (s.section_key or "")
        ]
        if not question_sets:
            print(f"error: no question set matches {args.set_filter!r}")
            return 1

    if args.only:
        wanted = {int(n) for n in args.only.split(",") if n.strip()}
        question_sets = [
            QuestionSet(
                name=s.name, path=s.path, section_key=s.section_key,
                questions=[q for q in s.questions if q.number in wanted],
            )
            for s in question_sets
        ]
        question_sets = [s for s in question_sets if s.questions]

    print(f"Filing:    {filing.company_name} — {facts_type(filing)} "
          f"FY{filing.fiscal_year}")
    if prior is not None:
        print(f"Prior:     {facts_type(prior)} FY{prior.fiscal_year}  "
              f"({prior.source_label}/)")
        # A prior filing that isn't actually prior would silently invert every
        # comparison answer, so check rather than trust the folder name.
        if prior.cik != filing.cik:
            print(f"  WARNING: prior CIK {prior.cik} != current {filing.cik} "
                  "— these are different companies.")
        elif (prior.period_end and filing.period_end
              and prior.period_end >= filing.period_end):
            print(f"  WARNING: prior period ({prior.period_end}) is not earlier "
                  f"than current ({filing.period_end}) — folders may be swapped.")
    else:
        print("Prior:     none found — comparison questions have nothing to "
              "compare against.")

    sector, sector_source = load_sector(filing.cik, args.sector)
    sector_rationale = ""
    if sector is None and not args.dry_run:
        # One small call, name and tickers only — the filing states no sector,
        # so sending it would cost tokens for nothing. Runs before the context
        # is built because the result goes into the cached facts block.
        try:
            sector, sector_rationale = analysis.classify_sector(
                filing.company_name or "this company",
                filing.facts.tickers,
                llm=create_client(provider=provider, model=model_name, effort="low"),
            )
            sector_source = "classified"
        except Exception as exc:  # noqa: BLE001 - benchmark degrades, run goes on
            print(f"  WARNING: sector classification failed ({type(exc).__name__}: "
                  f"{exc}); benchmark questions will have no band.")
    workspace = analysis.prepare(filing, prior_filing=prior,
                                 specs=SECTION_SPECS, sector=sector)
    for bundle in workspace.bundles:
        if bundle.current is None:
            print(f"  WARNING: section {bundle.spec.key!r} not found in the "
                  "current filing.")
        else:
            prior_note = (f", prior {bundle.prior.length:,}"
                          if bundle.prior else ", prior NOT FOUND")
            print(f"  section {bundle.spec.key:<13} "
                  f"{bundle.current.length:>7,} chars{prior_note}")
    print(f"Context:   {len(workspace.context):,} chars "
          f"(~{len(workspace.context)//4:,} tokens)")
    if sector:
        print(f"Sector:    {sector}  (from {sector_source})")
        if sector_rationale:
            print(f"           {sector_rationale}")
    else:
        print(f"Sector:    NOT CONFIGURED for CIK {filing.cik} — benchmark "
              f"questions will have no sector band to compare against.")
        print(f"           Add it to {SECTOR_MAP_PATH.name} or pass --sector.")
    print(f"Provider:  {provider} ({model_name})  effort={args.effort}  "
          f"workers={args.workers}")
    for question_set in question_sets:
        print(f"  set {question_set.name!r} -> section "
              f"{question_set.section_key or 'UNMAPPED'} "
              f"({len(question_set)} questions)")
    print()

    if args.dry_run:
        # Everything above this point is free: filings parsed, sections located,
        # questions mapped, context assembled. Stopping here is how you check a
        # new company before committing to a paid run.
        missing = [b.spec.key for b in workspace.bundles if b.current is None]
        unmapped = [s.name for s in question_sets if s.section_key is None]
        print("Dry run — no API calls made.")
        if missing:
            print(f"  PROBLEM: sections not found in the current filing: {missing}")
        if unmapped:
            print(f"  PROBLEM: question sets with no section mapping: {unmapped}")
        if sector:
            print(f"  Sector: {sector} (from {sector_source}).")
        else:
            # Not a problem any more. Classification is an API call, so it is
            # deliberately skipped here; a real run resolves the sector before
            # building the context.
            print("  Sector: unresolved — a real run classifies it from the "
                  "company name. Use --sector to pin it.")
        if not (missing or unmapped):
            print("  Everything resolved. Re-run without --dry-run to analyse.")
        return 1 if (missing or unmapped) else 0

    llm_client = create_client(provider=provider, model=model_name, effort=args.effort)
    runs: list[analysis.AnalysisRun] = []

    # Only differentiate where a section is shared; naming the sub-part when a
    # set has its section to itself would just restate the section title.
    shared = {k for k in (s.section_key for s in question_sets)
              if k and sum(1 for s in question_sets if s.section_key == k) > 1}

    for question_set in question_sets:
        print(f"--- {question_set.name} ---")
        completed = 0
        total = len(question_set)

        def report(result: analysis.QuestionResult) -> None:
            nonlocal completed
            completed += 1
            cache = ("cached" if result.usage and result.usage.cache_hit
                     else "WROTE CACHE")
            if result.question.kind is QuestionKind.SUMMARY:
                status = f"summary {len(result.answer)} chars"
                if result.question.max_chars:
                    status += f"/{result.question.max_chars}"
                if result.attempts > 1:
                    status += f" after {result.attempts} attempts"
                note = f"  !! {result.error}" if result.error else "  within limit"
                print(f"  [{completed}/{total}] Q{result.question.number:<2} "
                      f"{status}  ({result.elapsed_seconds:.0f}s, {cache}){note}")
            elif result.question.kind is QuestionKind.TABLE:
                flag = (f"  !! {len(result.unverified)} UNVERIFIED QUOTE(S)"
                        if result.unverified
                        else f"  {len(result.evidence)} quotes ok")
                shown = (f"{result.concern_level.value:>8}"
                         if result.has_level else "   table")
                print(f"  [{completed}/{total}] {result.question.display_id:<7} "
                      f"{shown}  ({result.elapsed_seconds:.0f}s, {cache}){flag}")
            elif result.ok:
                flag = (f"  !! {len(result.unverified)} UNVERIFIED QUOTE(S)"
                        if result.unverified
                        else f"  {len(result.evidence)} quotes ok")
                print(f"  [{completed}/{total}] {result.question.display_id:<7} "
                      f"{result.concern_level.value:>8}  "
                      f"({result.elapsed_seconds:.0f}s, {cache}){flag}")
            else:
                print(f"  [{completed}/{total}] Q{result.question.number:<2} "
                      f"FAILED — {result.error}")

        runs.append(analysis.run(
            workspace, question_set, llm=llm_client, workers=args.workers,
            scope_hint=(question_set.section_label
                        if question_set.section_key in shared else None),
            on_result=report,
        ))
        print()

    # -- console summary ---------------------------------------------------
    for run in runs:
        counts = run.distribution
        spread = "  ".join(f"{level.value} {counts[level]}"
                           for level in counts)
        print(f"{run.question_set.name}: {spread}, "
              f"{len(run.flagged())} flagged")
        for result in run.flagged():
            print(f"   {result.concern_level.value:>8}  {result.question.display_id}. "
                  f"{result.label}")

    total_unverified = sum(r.unverified_count for r in runs)
    total_evidence = sum(r.evidence_count for r in runs)
    if total_unverified:
        print(f"\n!! {total_unverified} of {total_evidence} cited quotation(s) "
              "NOT found in the filing:")
        for run in runs:
            for result in run.with_unverified:
                print(f"   [{run.question_set.name}] Q{result.question.number}:")
                for quote in result.unverified:
                    print(f"      {' '.join(quote.split())[:110]}")
    else:
        print(f"\nEvidence: all {total_evidence} quotations verified.")

    usage_in = sum(r.total_usage.total_input for r in runs)
    usage_out = sum(r.total_usage.output_tokens for r in runs)
    cached = sum(r.total_usage.cache_read_tokens for r in runs)
    elapsed = sum(r.elapsed_seconds for r in runs)
    print(f"\nTokens: {usage_in:,} in / {usage_out:,} out ({cached:,} from "
          f"cache) in {elapsed:.0f}s")

    args.output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = (filing.company_name or "filing").split()[0].lower().strip(".,")
    base = args.output / f"{slug}-analysis-{stamp}"

    report = to_json(runs, workspace, sector, sector_source)
    base.with_suffix(".json").write_text(json.dumps(report, indent=2))
    base.with_suffix(".md").write_text(render_markdown(runs, workspace))
    print(f"\nWrote {base.with_suffix('.md')}")
    print(f"      {base.with_suffix('.json')}")
    if not args.no_pdf:
        # Built from the JSON record, so the same PDF can be regenerated later
        # from the saved run without re-querying the API.
        pdf = build_pdf(report, base.with_suffix(".pdf"),
                        include_evidence=args.pdf_evidence)
        print(f"      {pdf}")

    return 1 if any(r.failed for r in runs) else 0


def facts_type(filing) -> str:
    return filing.facts.document_type or "?"


if __name__ == "__main__":
    raise SystemExit(main())
