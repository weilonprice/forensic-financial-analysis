#!/usr/bin/env python3
"""Measure how reproducible the analysis is across repeated runs.

    python scripts/measure_variance.py --baseline          # free, historical
    python scripts/measure_variance.py --set audit --runs 5

Two modes, deliberately reporting the same statistics so the numbers can be
compared directly.

`--baseline` reads the run records already in `output/` and needs no API key.
Several past runs covered the same question sets against the same filing, which
is a free before-measurement of the old 1-10 scale. It also answers the question
that decides whether the four-level scale was worth building: how much of that
variance was questions genuinely disagreeing, and how much was a ten-point
scale flipping between neighbouring values that meant the same thing? Collapsing
the old scores into the four bands separates the two.

The default mode runs a set N times against one prepared workspace — so the
filing is written to cache once and read N x questions times — and reports the
same statistics for the new levels.

The headline number is not the per-question flip rate. It is FLAGGED SET
STABILITY: whether the same questions end up in the report's findings list
every time. Individual levels can wobble without changing what an analyst
reads; the flagged set changing means two runs produced different reports.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic import analysis, questions as questions_mod, sections
from forensic.analysis import ConcernLevel
from forensic.llm import LLMClient, create_client, detect_provider, require_api_key
from forensic.filing import discover
from forensic.questions import QuestionSet

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIOR_YEAR_FOLDERS = ["Previous Year 10k", "Past 10k", "Previous 10k"]
SECTION_SPECS = [sections.AUDIT_REPORT, sections.MDA,
                 sections.FINANCIAL_STATEMENTS]

#: The bands the old 1-10 prompt described, mapped onto the levels that
#: replaced them. Used to ask what the four-level scale would have done to
#: historical runs — a flip from 8 to 7 was never a disagreement, it was two
#: names for the same finding.
_LEGACY_BANDS = [
    (10, ConcernLevel.NONE),
    (7, ConcernLevel.MINOR),
    (4, ConcernLevel.MATERIAL),
    (0, ConcernLevel.SEVERE),
]


def legacy_band(score: int) -> ConcernLevel:
    for threshold, level in _LEGACY_BANDS:
        if score >= threshold:
            return level
    return ConcernLevel.SEVERE


def _flagged(values: list) -> set:
    """Which questions would appear in the findings list, given one run."""
    return {
        key for key, value in values
        if (value.rank >= ConcernLevel.MATERIAL.rank
            if isinstance(value, ConcernLevel) else value <= 6)
    }


# --------------------------------------------------------------- reporting


def report(observations: dict[str, list], runs: int, title: str,
           verbose: bool = False) -> dict:
    """Print stability statistics for {question_key: [value per run]}.

    Values are either ints (old scale) or ConcernLevels (new). Questions not
    present in every run are dropped — a question added or renumbered between
    runs has nothing to compare against, and silently treating a missing value
    as agreement would flatter the result.
    """
    complete = {k: v for k, v in observations.items() if len(v) == runs}
    dropped = len(observations) - len(complete)

    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")
    print(f"{runs} runs · {len(complete)} questions compared"
          + (f" · {dropped} dropped (not in every run)" if dropped else ""))
    if not complete:
        print("  Nothing to compare.")
        return {}

    unstable = {k: v for k, v in complete.items() if len(set(v)) > 1}

    def render(value) -> str:
        return value.value if isinstance(value, ConcernLevel) else str(value)

    if verbose or unstable:
        print(f"\n{'question':<10} {'values across runs':<34} stable")
        print("-" * 74)
        for key in sorted(complete, key=lambda k: (k not in unstable, k)):
            values = complete[key]
            if not verbose and key not in unstable:
                continue
            shown = " ".join(f"{render(v):>8}" for v in values)
            print(f"{key:<10} {shown:<34} {'no' if key in unstable else 'yes'}")

    flip_rate = len(unstable) / len(complete)
    print(f"\n  per-question flip rate   {len(unstable)}/{len(complete)}"
          f"  ({flip_rate:.0%})")

    # The number that decides whether the report is reproducible.
    flagged_sets = [
        _flagged([(k, v[i]) for k, v in complete.items()]) for i in range(runs)
    ]
    identical = all(s == flagged_sets[0] for s in flagged_sets)
    union = set().union(*flagged_sets)
    always = set.intersection(*flagged_sets) if flagged_sets else set()
    print(f"  flagged set identical    {'YES' if identical else 'NO'}"
          f"   ({len(always)} flagged in every run, "
          f"{len(union)} in at least one)")
    if not identical:
        print(f"    unstable membership: "
              f"{sorted(union - always)}")

    return {
        "runs": runs, "questions": len(complete),
        "flip_rate": flip_rate, "unstable": sorted(unstable),
        "flagged_identical": identical,
        "flagged_always": sorted(always), "flagged_union": sorted(union),
    }


# ------------------------------------------------------------- baseline mode


def run_baseline(set_filter: str | None, verbose: bool) -> None:
    """Recover the old scale's variance from run records already on disk."""
    records = []
    for path in sorted(glob.glob(str(PROJECT_ROOT / "output" / "*.json"))):
        try:
            data = json.loads(Path(path).read_text())
        except json.JSONDecodeError:
            continue
        if any(r.get("score") is not None
               for s in data.get("sets", []) for r in s.get("results", [])):
            records.append((Path(path).name, data))

    if len(records) < 2:
        print(f"Need at least two scored run records; found {len(records)}.")
        return

    ciks = {d.get("filing", {}).get("cik") for _, d in records}
    if len(ciks) > 1:
        print(f"WARNING: records span several filings {ciks} — comparing runs "
              "of different companies measures nothing. Filtering to the most "
              "common.")
        common = Counter(d.get("filing", {}).get("cik")
                         for _, d in records).most_common(1)[0][0]
        records = [(n, d) for n, d in records
                   if d.get("filing", {}).get("cik") == common]

    # Group by set, keeping only sets that appear in at least two runs.
    by_set: dict[str, dict[str, list[int]]] = {}
    counts: Counter = Counter()
    for _, data in records:
        for block in data.get("sets", []):
            name = block.get("name", "?")
            if set_filter and set_filter.lower() not in name.lower():
                continue
            scored = {
                str(r.get("display_id") or r.get("number")): r["score"]
                for r in block.get("results", [])
                if r.get("score") is not None
            }
            if not scored:
                continue
            counts[name] += 1
            target = by_set.setdefault(name, {})
            for key, score in scored.items():
                target.setdefault(key, []).append(score)

    print(f"\n{len(records)} scored run record(s) for CIK "
          f"{records[0][1].get('filing', {}).get('cik')}")
    for name, n in counts.items():
        print(f"  {name:<40} appears in {n} run(s)")

    for name, observations in by_set.items():
        runs = counts[name]
        if runs < 2:
            continue
        stats = report(observations, runs,
                       f"BASELINE — {name} — old 1-10 scale", verbose)
        if not stats:
            continue

        # The decisive comparison: rerun the same numbers through the four
        # bands. Anything that stabilises here was scale noise, not
        # disagreement, and is exactly what the new levels absorb.
        banded = {k: [legacy_band(s) for s in v]
                  for k, v in observations.items()}
        after = report(banded, runs,
                       f"SAME RUNS — {name} — collapsed into four levels",
                       verbose)
        if after:
            print(f"\n  >> flip rate {stats['flip_rate']:.0%} -> "
                  f"{after['flip_rate']:.0%} purely from widening the buckets")
            print(f"  >> flagged set identical: "
                  f"{stats['flagged_identical']} -> "
                  f"{after['flagged_identical']}")


# ----------------------------------------------------------------- live mode


def run_live(args) -> None:
    provider = args.provider or detect_provider(args.model)
    model_name = args.model or ("gemini-3.7-flash" if provider == "gemini" else "claude-opus-5")

    try:
        require_api_key(provider=provider, model=model_name)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}")
        return

    filings = discover(PROJECT_ROOT / "Latest 10k")
    if not filings:
        print("No filing found in 'Latest 10k'.")
        return
    prior = None
    for name in PRIOR_YEAR_FOLDERS:
        found = discover(PROJECT_ROOT / name)
        if found:
            prior = found[0]
            break

    sets = questions_mod.discover(PROJECT_ROOT / "Analysis Questions")
    if args.set:
        sets = [s for s in sets if args.set.lower() in s.name.lower()]
    if not sets:
        print(f"No question set matching {args.set!r}.")
        return
    question_set = sets[0]

    if args.only:
        wanted = {int(n) for n in args.only.split(",") if n.strip()}
        question_set = QuestionSet(
            name=question_set.name, path=question_set.path,
            section_key=question_set.section_key,
            questions=[q for q in question_set.questions
                       if q.number in wanted],
        )
        if not question_set.questions:
            print(f"No question matching --only {args.only!r}.")
            return

    # Prepared once on purpose: every repeat shares the cached filing, so the
    # measurement costs one cache write plus N x questions reads rather than
    # N full-price passes.
    workspace = analysis.prepare(filings[0], prior_filing=prior,
                                 specs=SECTION_SPECS, sector=args.sector)
    llm_client = create_client(provider=provider, model=model_name, effort=args.effort)

    print(f"Measuring '{question_set.name}' — {len(question_set)} question(s) "
          f"x {args.runs} runs, provider={provider} ({model_name}), effort={args.effort}")

    observations: dict[str, list[ConcernLevel]] = {}
    raw = []
    for index in range(args.runs):
        run = analysis.run(workspace, question_set, llm=llm_client,
                           workers=args.workers)
        for result in run.results:
            if result.ok and result.has_level:
                observations.setdefault(
                    result.question.display_id, []).append(result.concern_level)
        counts = run.distribution
        print(f"  run {index + 1}/{args.runs}: "
              + "  ".join(f"{k.value} {v}" for k, v in counts.items()))
        raw.append({result.question.display_id: result.concern_level.value
                    for result in run.results
                    if result.ok and result.has_level})

    stats = report(observations, args.runs,
                   f"{question_set.name} — four-level scale", args.verbose)

    out = PROJECT_ROOT / "output" / "variance.json"
    out.write_text(json.dumps(
        {"set": question_set.name, "runs": args.runs, "effort": args.effort,
         "observations": raw, "stats": stats}, indent=2))
    print(f"\nRaw observations written to {out.relative_to(PROJECT_ROOT)} — "
          "re-analysable without spending again.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true",
                        help="analyse existing run records; no API calls")
    parser.add_argument("--set", help="question set to measure (substring)")
    parser.add_argument("--provider", default=None, choices=["claude", "gemini"],
                        help="LLM provider (claude or gemini)")
    parser.add_argument("--model", default=None,
                        help="model name (e.g. gemini-3.7-flash, claude-opus-5)")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--only", help="question numbers, e.g. 1,2,3")
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--sector", default=None)
    parser.add_argument("--verbose", action="store_true",
                        help="list every question, not only the unstable ones")
    args = parser.parse_args()

    if args.baseline:
        run_baseline(args.set, args.verbose)
    else:
        run_live(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
