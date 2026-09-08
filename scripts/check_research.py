#!/usr/bin/env python3
"""Show exactly what the app will see in the 100-step workbook. No API calls.

    python scripts/check_research.py
    python scripts/check_research.py --verbose        # print every prompt
    python scripts/check_research.py --step 72        # one step, with sources

Run this after editing the workbook export and before paying for a run.

The checks that matter here are different from check_questions.py. That file
guards against a *human* mis-editing a question list. This one guards against
the *parser* mangling a machine-generated export: furniture that survived
stripping, a template placeholder reaching the model, or a repeat run collapsed
onto the wrong period. Exit code is 1 if anything looks wrong.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic import research
from forensic.research import LineKind

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKBOOK_DIR = PROJECT_ROOT / "100 Steps Questions"

#: Phrases that mean cleaning missed something. If any of these reach a prompt,
#: the model is being told about a spreadsheet it cannot see.
_LEAKED_FURNITURE = (
    "box on the right", "cell on the right", "click me", "calculated for you",
    "white shaded", "row 22", "on the right, please",
)

#: The example company's competitors, left behind by the export. Any of these in
#: a prompt is a correctness bug: the model would answer about Apple's rivals
#: while reading another company's filing.
_LEAKED_PLACEHOLDERS = (
    "Samsung", "Microsoft", "Research in Motion", "Bluth", "Bubba Gump",
    "J.T. Marlin", "Wonka", "Virtucon", "Los Pollos", "Cyberdyne",
)

#: The market placeholders cannot be caught by name. "Computer market" appears
#: both as a leak ("which you entered as the Computer market") and as a
#: legitimate instruction telling the analyst how to phrase an answer (type
#: "Computer" rather than "The Computer Market") — that second one is worth
#: keeping, so match the leak's phrasing instead of the bare words.
_LEAKED_SUBSTITUTION = re.compile(r"which you entered as the", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true",
                        help="print every prompt, not just a per-step summary")
    parser.add_argument("--step", type=int,
                        help="show one step in full, with its source lines")
    args = parser.parse_args()

    steps = research.discover(WORKBOOK_DIR)
    warnings: list[str] = []

    if args.step is not None:
        matches = [s for s in steps if s.number == args.step]
        if not matches:
            print(f"No step {args.step}. Present: "
                  f"{', '.join(str(s.number) for s in steps)}")
            return 1
        step = matches[0]
        print(f"[{step.number} {step.name}]  "
              f"{step.source_lines} source lines -> {len(step)} prompts\n")
        for question in step.questions:
            print(f"  {question.question_id:<8} {question.kind.value:<12} "
                  f"repeat={question.repeat}")
            print(f"      {question.text}")
            if question.repeat > 1:
                print(f"      stands for {question.repeat} source lines:")
                for source in question.sources:
                    print(f"        - {source[:96]}")
            print()
        return 0

    total_lines = total_prompts = 0
    counts: dict[str, int] = {}

    print(f"{len(steps)} steps in {WORKBOOK_DIR.name}/\n")
    header = f"  {'step':<5} {'name':<32} {'lines':>6} {'prompts':>8}  breakdown"
    print(header)
    print(f"  {'-' * (len(header) - 2)}")

    for step in steps:
        total_lines += step.source_lines
        total_prompts += len(step)
        kinds: dict[str, int] = {}
        for question in step.questions:
            kinds[question.kind.value] = kinds.get(question.kind.value, 0) + 1
            counts[question.kind.value] = counts.get(question.kind.value, 0) + 1

        # A step whose questions do not account for every source line means the
        # collapse dropped something.
        covered = sum(q.repeat for q in step.questions)
        if covered != step.source_lines:
            warnings.append(
                f"step {step.number}: {covered} lines accounted for but "
                f"{step.source_lines} read — the collapse lost content."
            )

        note = "  ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
        collapsed = " *" if len(step) != step.source_lines else "  "
        print(f"  {step.number:<5} {step.name[:32]:<32} {step.source_lines:>6} "
              f"{len(step):>8}{collapsed} {note}")

        if args.verbose:
            for question in step.questions:
                tag = (f"x{question.repeat}" if question.repeat > 1 else "  ")
                print(f"        {question.question_id:<8} {tag:<4} "
                      f"{question.text[:96]}")

    # -- leak checks -------------------------------------------------------
    for step in steps:
        for question in step.questions:
            # Only prompts that actually get sent can leak. A computed line
            # keeps its "calculated for you" wording — that phrase is how it was
            # identified as computed in the first place.
            if question.kind not in (LineKind.QUESTION, LineKind.SETTING):
                continue
            lowered = question.text.lower()
            for phrase in _LEAKED_FURNITURE:
                if phrase in lowered:
                    warnings.append(
                        f"{question.question_id}: spreadsheet furniture survived "
                        f"cleaning ({phrase!r}) — {question.text[:70]}"
                    )
            for name in _LEAKED_PLACEHOLDERS:
                if re.search(rf"\b{re.escape(name)}\b", question.text, re.I):
                    warnings.append(
                        f"{question.question_id}: template placeholder {name!r} "
                        f"reached a prompt — the model would answer about the "
                        f"wrong company. {question.text[:70]}"
                    )
            if _LEAKED_SUBSTITUTION.search(question.text):
                warnings.append(
                    f"{question.question_id}: an unresolved workbook "
                    f"substitution reached a prompt — {question.text[:70]}"
                )

    print(f"\n{'-' * 78}")
    print(f"{total_lines} source lines -> {total_prompts} prompts "
          f"({total_lines - total_prompts} folded into repeats)")
    print("  " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    askable = counts.get(LineKind.QUESTION.value, 0)
    print(f"\n{askable} prompts would be sent to the model.")

    settings = [q for s in steps for q in s.questions
                if q.kind is LineKind.SETTING]
    if settings:
        print(f"\n{len(settings)} setting(s) resolved once per run, then "
              f"substituted into later steps:")
        for question in settings:
            tag = f" (x{question.repeat})" if question.repeat > 1 else ""
            print(f"    {question.question_id}{tag}  {question.text[:82]}")

    skipped = [q for s in steps for q in s.questions
               if q.kind in (LineKind.COMPUTED, LineKind.UNAVAILABLE)]
    if skipped:
        print(f"\n{len(skipped)} line(s) are not questions and will be skipped:")
        for question in skipped:
            print(f"    {question.question_id:<8} {question.kind.value:<12} "
                  f"{question.text[:70]}")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  ! {warning}")
        return 1

    print("\nNo problems found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
