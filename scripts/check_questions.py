#!/usr/bin/env python3
"""Show exactly what the app will see in your question files. No API calls.

    python scripts/check_questions.py
    python scripts/check_questions.py --verbose      # print every question

Run this after editing a question file and before paying for an analysis run.
Every formatting problem this project has hit — 29 questions parsed from a
15-question file, two questions merged into one by a stray paste, a set with no
section mapping, an edit that landed in a backup file — shows up here in a
second instead of after a multi-dollar run.

Exit code is 1 if anything looks wrong, so it can gate a run in a shell:

    python scripts/check_questions.py && python scripts/run_analysis.py
"""

from __future__ import annotations

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic import analysis, questions as questions_mod, sections
from forensic.questions import QuestionKind, QuestionSet

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTION_DIR = PROJECT_ROOT / "Analysis Questions"

#: Sections the runner actually loads. A set mapped to anything else gets no
#: scope marker at run time, so the mapping must be checked against this list
#: rather than against every spec that merely exists.
LOADED_SECTIONS = {spec.key for spec in
                   [sections.AUDIT_REPORT, sections.MDA,
                    sections.FINANCIAL_STATEMENTS]}

#: A question-number marker sitting *inside* a question body — the signature of
#: two questions pasted onto one line, which is what made Q14 ask about revenue
#: verticals and revenue recognition policy at the same time.
#:
#: Precise rather than heuristic. Length alone is too blunt: the real Q14 bug
#: ran 727 characters against a median of ~440, only 1.65x, so any threshold
#: loose enough to catch it also flags legitimately long questions. This matches
#: the actual shape — sentence end, then "N." then a capital — and finds 0 false
#: positives across the 47 questions in this project, including Q11's "Tell me 3
#: things. 1: ... 2: ..." which enumerates with colons rather than periods.
_MERGED = re.compile(r"(?<=[.!?])\s+(\d{1,2})\.\s+[A-Z]")

#: Two questions this similar are a duplicated block.
#:
#: Deliberately near-1.0. Most of each question's text is the same repeated
#: boilerplate ("Based on that response should I be worried? ... score out of
#: 10"), so genuinely different questions score very high on raw similarity —
#: "revenue disclosure" versus "expense disclosure" differs by one word in 430
#: characters and lands at 0.986. A threshold of 0.95 flagged both of those as
#: duplicates. The failure this is actually looking for is a pasted block, which
#: is identical.
_DUPLICATE_RATIO = 0.995

_BOILERPLATE = ("should I be worried", "score out of 10")


def check_set(question_set: QuestionSet, verbose: bool) -> list[str]:
    """Report one set; return a list of warnings."""
    warnings: list[str] = []
    questions = question_set.questions

    kinds: dict[str, int] = {}
    for question in questions:
        kinds[question.kind.value] = kinds.get(question.kind.value, 0) + 1

    mapped = question_set.section_key in LOADED_SECTIONS
    spec = sections.REGISTRY.get(question_set.section_key or "")
    section_note = (
        f"{question_set.section_key}  ({spec.title})" if mapped and spec
        else f"{question_set.section_key or 'UNMAPPED'}  <-- no scope marker"
    )

    print(f"\n{question_set.name}")
    print(f"  file      {question_set.path.relative_to(PROJECT_ROOT)}")
    print(f"  section   {section_note}")
    print(f"  questions {len(questions)}  " +
          "  ".join(f"{k}={v}" for k, v in sorted(kinds.items())))

    if not mapped:
        warnings.append(
            f"{question_set.name}: section_key is "
            f"{question_set.section_key or 'None'} — the runner loads "
            f"{sorted(LOADED_SECTIONS)}, so these questions will run with no "
            "scope marker and no section pinned in front."
        )

    # -- duplicate numbering ---------------------------------------------
    seen: dict[tuple[str, int], int] = {}
    for question in questions:
        key = (question.kind.value if question.kind is QuestionKind.TABLE
               else "q", question.number)
        seen[key] = seen.get(key, 0) + 1
    for (_, number), count in sorted(seen.items(), key=lambda kv: kv[0][1]):
        if count > 1:
            warnings.append(
                f"{question_set.name}: number {number} appears {count} times — "
                "the file probably contains a duplicated block."
            )

    # -- merged questions -------------------------------------------------
    prose = [q for q in questions if q.kind is not QuestionKind.TABLE]
    for question in prose:
        matches = list(_MERGED.finditer(question.text))
        if not matches:
            continue
        numbers = [int(m.group(1)) for m in matches]
        # An ascending run is a deliberate sub-list, not a paste. The footnote
        # set's first question is a preamble followed by items 1 through 5 under
        # one score; the real merge bug was a single stray "1." appended to
        # question 14.
        is_list = (len(numbers) >= 3
                   and all(b == a + 1 for a, b in zip(numbers, numbers[1:])))
        if is_list:
            continue
        where = question.text[max(0, matches[0].start() - 40):
                              matches[0].start() + 60]
        warnings.append(
            f"{question_set.name} Q{question.number}: a question number "
            f"appears mid-text — two questions pasted onto one line? "
            f"...{' '.join(where.split())}..."
        )

    # -- near-duplicate text ----------------------------------------------
    for i, first in enumerate(prose):
        for second in prose[i + 1:]:
            if abs(len(first.text) - len(second.text)) > 40:
                continue
            if SequenceMatcher(None, first.text, second.text).ratio() > _DUPLICATE_RATIO:
                warnings.append(
                    f"{question_set.name}: Q{first.number} and Q{second.number} "
                    "are near-identical — duplicated content?"
                )

    # -- tasks need a registered schema -----------------------------------
    for question in questions:
        if question.kind is not QuestionKind.TABLE:
            continue
        if question.task_slug not in analysis.TASK_SPECS:
            warnings.append(
                f"{question_set.name} Task {question.number} "
                f"({question.task_slug!r}): no schema registered — it will fall "
                "back to a prose answer instead of a filled table."
            )

    # -- per-question detail ----------------------------------------------
    for question in questions:
        bits = []
        if question.kind is QuestionKind.TABLE:
            bits.append(f"slug={question.task_slug}")
            bits.append("schema=" + ("yes" if question.task_slug
                                     in analysis.TASK_SPECS else "MISSING"))
        elif question.kind is QuestionKind.SUMMARY:
            bits.append(f"limit={question.max_chars or 'none'}")
        else:
            has = all(p in question.text for p in _BOILERPLATE)
            bits.append("scored" if has else "no concern/score in text")
        if question.auto_numbered:
            bits.append("AUTO-NUMBERED")
        detail = ", ".join(bits)
        if verbose:
            print(f"    {question.display_id:<8} {question.kind.value:<8} "
                  f"{detail}\n             {question.topic[:88]}")
        else:
            print(f"    {question.display_id:<8} {question.kind.value:<8} "
                  f"{detail:<34} {question.topic[:52]}")

    if not any(q.kind is QuestionKind.SUMMARY for q in questions):
        print("    (no summary question in this set)")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true",
                        help="print each question's topic on its own line")
    args = parser.parse_args()

    stray = [p for p in QUESTION_DIR.rglob("*")
             if p.is_file() and p.suffix.lower() not in {".txt", ""}
             and p.name != ".DS_Store"]

    # A .txt file that yields no questions is skipped silently by the loader.
    # That is how a whole question set went missing while this checker reported
    # "no problems found" — so check each file individually, not just the
    # aggregate.
    empty: list[Path] = []
    for path in sorted(QUESTION_DIR.rglob("*.txt")):
        if path.name.startswith((".", "._")):
            continue
        try:
            questions_mod.load(path)
        except ValueError:
            empty.append(path)

    question_sets = questions_mod.discover(QUESTION_DIR)
    if not question_sets:
        print(f"No question sets found in {QUESTION_DIR}")
        return 1

    print(f"{len(question_sets)} set(s) in {QUESTION_DIR.name}/")
    warnings: list[str] = []
    for question_set in question_sets:
        warnings.extend(check_set(question_set, args.verbose))

    total = sum(len(s) for s in question_sets)
    scored = sum(1 for s in question_sets for q in s.questions
                 if q.kind is QuestionKind.STANDARD)
    print(f"\n{'-' * 66}")
    print(f"{total} questions total across {len(question_sets)} set(s) "
          f"({scored} scored)")

    # Files the loader ignores are worth surfacing: an edit that lands in a
    # .bak or .docx looks saved but never reaches the app.
    for path in stray:
        warnings.append(
            f"{path.name}: not a .txt file, so the loader ignores it — "
            "an edit made here would never reach the app."
        )
    for path in empty:
        warnings.append(
            f"{path.name}: parsed to ZERO questions and is skipped silently by "
            "the runner. Expected numbered lines ('1.', '2.', ...) or questions "
            "ending in the scoring boilerplate."
        )

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  ! {warning}")
        return 1

    print("\nNo problems found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
