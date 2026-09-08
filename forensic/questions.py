"""Loading question sets from the `Analysis Questions/` folder.

A question file holds one or more *sets*, each targeting a different part of the
10-K. Sets are separated by a bare header line ("MD&A Questions:") and each set
numbers its questions from 1, so numbers are unique only within a set — the file
currently contains two questions numbered 1, and treating them as one flat list
collides them.

Two parsing rules matter, both learned from this file breaking them:

* Questions split on the leading `N.` at the start of a line, NOT on blank
  lines. Audit questions 5 and 6 sit on consecutive lines with no blank between
  them; a blank-line split silently merges them and produces an 11-question set
  from a 12-question file.
* A numbered block may still contain more than one question. Questions appended
  later are sometimes left unnumbered, separated only by a blank line. Without
  splitting those out they are absorbed into the question above, which then asks
  three things at once and answers whichever it prefers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

#: A question begins with `N.` at the start of a line. Anchored to line start so
#: that "1 is very concerned. 10 is not concerned" inside a question body cannot
#: be mistaken for a new question.
_QUESTION_START = re.compile(r"^[ \t]*(\d{1,3})\.[ \t]+", re.MULTILINE)

#: A set divider: a short, unnumbered line ending in a colon, alone on its line.
#: The length bound is what stops it matching a real question that happens to
#: contain a colon.
_SET_HEADER = re.compile(r"^[ \t]*([A-Za-z][^\n:]{0,70}:)[ \t]*$", re.MULTILINE)

#: A blank line separates questions within a numbered block.
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")

_TOPIC = re.compile(r"^(.{0,160}?\?)", re.DOTALL)

#: A question asking for a digest of the answers already produced rather than
#: for anything in the filing. Detected by wording because the file carries no
#: type markers. The `.{0,60}` between the verb and "answers" is what lets this
#: match "summarize all of the MD&A answers" as well as "...the previous
#: answers".
#: "answers" and "questions" both appear in practice — one set asks to
#: "summarize all previous income statement answers", another to "summarize all
#: the Balance sheet and Cash flow questions". Same intent, and requiring
#: "answers" alone left the second parsed as an ordinary scored question.
_SUMMARY = re.compile(
    r"answers?\s+summary"
    r"|summar(?:y|ize|ise)\b[^.]{0,60}\b(?:answers|questions)\b",
    re.IGNORECASE,
)

#: An explicit character budget, e.g. "character count is less than 350".
_CHAR_LIMIT = re.compile(
    r"character count[^.]{0,30}?(?:less than|under|below|fewer than)\s*(\d{2,5})",
    re.IGNORECASE,
)

#: Which filing section a set of questions is about, inferred from the words the
#: questions use. Inference rather than configuration because the file names its
#: sets freely — and the first set carries no header at all. Whatever is inferred
#: is printed at run time so a wrong guess is visible rather than silent.
#:
#: Hints must be distinctive to one set. Bare words like "revenue" or
#: "non-GAAP" appear in more than one question file and would pull a set toward
#: whichever section happens to use them more often, so each entry below uses
#: phrases that only its own section's questions would contain.
_SECTION_HINTS: list[tuple[str, str, tuple[str, ...]]] = [
    ("mda", "MD&A", ("md&a", "management's discussion", "management discussion",
                     "liquidity", "capital resources", "forward-looking")),
    ("audit_report", "Audit Report",
     ("auditor", "audit report", "critical audit matter", "cams", "icfr",
      "unqualified", "material weakness")),
    ("financial_statements", "Income Statement",
     ("income statement", "revenue recognition", "expense recognition",
      "profit margin", "gross profit", "operating profit", "organic revenue",
      "accruals ratio", "earnings quality", "depreciation polic",
      "sales allowances", "restated earnings", "non-recurring")),
    # Balance sheet and cash flow questions read the same Item 8 span as the
    # income statement ones — the statements sit side by side and share the
    # notes — so they map to the same section, with their own display label.
    ("financial_statements", "Balance Sheet and Cash Flow",
     ("balance sheet", "cash flow", "working capital", "current ratio",
      "quick ratio", "cash conversion", "free cash flow", "days payable",
      "days inventory", "book value", "tangible asset", "net debt",
      "deferred tax", "share buyback", "treasury stock")),
    # Footnotes likewise: the notes are 86% of Item 8. Retarget this entry to
    # "notes" only if the dedicated NOTES spec is enabled in SECTION_SPECS.
    ("financial_statements", "Footnotes",
     ("footnote", "notes to the financial statements",
      "notes to consolidated", "off-balance sheet", "related party",
      "subsequent event", "commitments and contingencies",
      "fair value hierarchy", "level 3", "contingent liabilit",
      "disclosure note")),
]


#: A task block: "Task 1: DSO Data Entry", followed by an ASCII table rather
#: than a sentence. Matched separately from numbered questions because it has
#: no leading `N.` and because its body must survive whole.
_TASK_START = re.compile(r"^[ \t]*Task\s+(\d+)\s*:[ \t]*([^\n]*)$", re.MULTILINE)


class QuestionKind(str, Enum):
    #: Examine the filing and return answer + concern + score.
    STANDARD = "standard"
    #: Digest the answers already given. No concern, no score, and it must run
    #: after everything it summarises.
    SUMMARY = "summary"
    #: Populate a table of figures. Returns structured data rather than prose,
    #: so it needs its own schema and its own rendering.
    TABLE = "table"


@dataclass(frozen=True)
class Question:
    number: int
    #: The question exactly as written, including its formatting instructions.
    #: Sent to the model verbatim: the user's wording is the specification, and
    #: paraphrasing it would quietly change what gets asked.
    text: str
    kind: QuestionKind = QuestionKind.STANDARD
    #: True when the question carried no number in the source file and one was
    #: assigned. Surfaced in the report so a numbering gap is visible.
    auto_numbered: bool = False
    #: A hard character budget, when the question states one. Enforced by the
    #: runner: the API's structured outputs cannot express a maxLength.
    max_chars: int | None = None
    #: For TABLE questions, a slug from the task title ("dso_data_entry") used
    #: to look up the right response schema and renderer.
    task_slug: str | None = None
    #: The task's own title, for display.
    title: str | None = None

    @property
    def topic(self) -> str:
        """A short label for display — the first question mark's worth."""
        if self.title:
            return self.title
        match = _TOPIC.match(self.text)
        label = match.group(1) if match else self.text[:90]
        return " ".join(label.split())

    @property
    def display_id(self) -> str:
        """Identifier for the report.

        Tasks number from 1 independently of the questions, so a bare number
        would show two "1"s in the same section. Internally they never collide
        — results are keyed by position — but the reader needs them told apart.
        """
        return f"Task {self.number}" if self.kind is QuestionKind.TABLE \
            else str(self.number)


@dataclass(frozen=True)
class QuestionSet:
    name: str
    path: Path
    questions: list[Question] = field(default_factory=list)
    #: Key of the `SectionSpec` these questions are about, or None if unclear.
    section_key: str | None = None
    #: The inferred content label ("Balance Sheet and Cash Flow", "Footnotes").
    #: Distinct from `name`, which comes from the file. Used to tell apart sets
    #: that share one section: three sets now point at Item 8, and without this
    #: they would all receive an identical scope marker.
    section_label: str | None = None

    def __len__(self) -> int:
        return len(self.questions)

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")


def classify(text: str) -> tuple[QuestionKind, int | None]:
    """Infer a question's kind and any character budget from its wording."""
    kind = QuestionKind.SUMMARY if _SUMMARY.search(text) else QuestionKind.STANDARD
    limit = _CHAR_LIMIT.search(text)
    return kind, int(limit.group(1)) if limit else None


def infer_section(questions: list[Question]) -> tuple[str | None, str | None]:
    """Guess which filing section a set of questions is about.

    Returns (section_key, human label), or (None, None) when nothing scores.
    """
    corpus = " ".join(q.text for q in questions).lower()
    best: tuple[int, str, str] | None = None
    for key, label, hints in _SECTION_HINTS:
        score = sum(corpus.count(hint) for hint in hints)
        if score and (best is None or score > best[0]):
            best = (score, key, label)
    return (best[1], best[2]) if best else (None, None)


#: The tail every scored question ends with. Used as a question terminator when
#: a file carries no usable numbering.
_SCORE_TAIL = re.compile(
    r"just give me a number and nothing else\.?", re.IGNORECASE
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _split_on_terminator(text: str) -> list[str]:
    """Split a set into questions on the scoring boilerplate.

    For files written without numbering, the boilerplate is a more reliable
    delimiter than blank lines — spacing in these files is inconsistent (two
    blank lines in places, one in others, none between some questions), and a
    blank-line split silently fuses neighbours.

    It also gets a composite question right where numbering cannot. The footnote
    set opens with a preamble, five numbered sub-items, and a single "should I
    be worried" tail covering all of it. Splitting on numbers would promote the
    five sub-items to five questions; splitting on the tail keeps the block
    whole, which is what it is.
    """
    blocks: list[str] = []
    cursor = 0
    for match in _SCORE_TAIL.finditer(text):
        blocks.append(text[cursor:match.end()])
        cursor = match.end()
    remainder = text[cursor:]
    if remainder.strip():
        blocks.append(remainder)

    cleaned: list[str] = []
    for block in blocks:
        # Keep line breaks: a composite question's sub-items are a list, and
        # flattening them to one line makes it far harder to read. Only the
        # padding and blank runs go.
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if lines:
            cleaned.append("\n".join(lines))
    return cleaned


def _parse_questions(text: str) -> list[Question]:
    """Split one set's text into questions and tasks.

    Both anchor at the start of a line — `N.` for a question, `Task N:` for a
    task — and each block runs to the next anchor. They are collected together
    and sorted by position so a file can interleave them in any order.
    """
    anchors: list[tuple[int, str, re.Match[str]]] = []
    for match in _QUESTION_START.finditer(text):
        anchors.append((match.start(), "question", match))
    for match in _TASK_START.finditer(text):
        anchors.append((match.start(), "task", match))

    # Numbering is authoritative when it accounts for the file. Where the
    # scoring boilerplate appears MORE often than there are numbered anchors,
    # the numbers are not question numbers — they are sub-items inside one
    # question, or absent entirely — and the boilerplate is the real delimiter.
    #
    # Observed across this project's five sets (terminators vs anchors):
    #   audit 13/14, MD&A 14/16, income 14/17  -> numbering
    #   footnotes 10/5, balance sheet 11/0     -> terminator
    terminators = len(_SCORE_TAIL.findall(text))
    if terminators and terminators > len(anchors):
        questions: list[Question] = []
        for number, body in enumerate(_split_on_terminator(text), start=1):
            kind, max_chars = classify(body)
            questions.append(
                Question(number=number, text=body, kind=kind,
                         max_chars=max_chars)
            )
        return questions

    if not anchors:
        return []
    anchors.sort(key=lambda a: a[0])

    questions: list[Question] = []
    last_number = 0

    for index, (_, anchor_kind, match) in enumerate(anchors):
        block_end = anchors[index + 1][0] if index + 1 < len(anchors) else len(text)

        if anchor_kind == "task":
            # Keep the block verbatim from its header line. Collapsing
            # whitespace here would flatten the ASCII table the task IS —
            # column alignment is what makes it readable as a grid.
            body = "\n".join(
                line.rstrip() for line in text[match.start():block_end].split("\n")
            ).strip("\n")
            title = " ".join(match.group(2).split()) or f"Task {match.group(1)}"
            questions.append(
                Question(
                    number=int(match.group(1)),
                    text=body,
                    kind=QuestionKind.TABLE,
                    task_slug=_slug(title),
                    title=title,
                )
            )
            continue

        # A numbered block may still hold more than one question — appended
        # questions are sometimes left unnumbered, separated by a blank line.
        for offset, paragraph in enumerate(
            p for p in _PARAGRAPH_BREAK.split(text[match.end():block_end]) if p.strip()
        ):
            # These are prose; the file pads them with trailing spaces, so
            # collapse whitespace to keep dead characters out of the prompt.
            cleaned = " ".join(paragraph.split())
            if not cleaned:
                continue
            number = int(match.group(1)) if offset == 0 else last_number + 1
            kind, max_chars = classify(cleaned)
            questions.append(
                Question(
                    number=number,
                    text=cleaned,
                    kind=kind,
                    auto_numbered=offset > 0,
                    max_chars=max_chars,
                )
            )
            last_number = number

    return questions


def parse(raw: str, path: Path) -> list[QuestionSet]:
    """Split a question file into its sets."""
    # Strip a UTF-8 BOM (Windows editors add one) and normalise CRLF. Left
    # alone, the BOM becomes part of question 1's text and CRLF breaks the
    # line-anchored splits.
    text = raw.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")

    headers = list(_SET_HEADER.finditer(text))
    # Segment boundaries: start of file, then each header.
    segments: list[tuple[str | None, str]] = []
    cursor = 0
    label: str | None = None
    for header in headers:
        chunk = text[cursor:header.start()]
        if chunk.strip():
            segments.append((label, chunk))
        label = header.group(1).rstrip(":").strip()
        cursor = header.end()
    if text[cursor:].strip():
        segments.append((label, text[cursor:]))

    sets: list[QuestionSet] = []
    for header_label, body in segments:
        questions = _parse_questions(body)
        if not questions:
            continue
        key, inferred = infer_section(questions)
        # Name from the header if there is one, otherwise the filename. NOT from
        # the inferred section label: the footnote questions mention revenue
        # recognition and depreciation often enough to infer "Income Statement",
        # which would put two identically-named sections in the report. The
        # filename is a deliberate human label; the inference is a guess, and it
        # is only trusted for the section mapping.
        name = header_label or path.stem
        sets.append(
            QuestionSet(name=name, path=path, questions=questions,
                        section_key=key, section_label=inferred)
        )
    return sets


def load(path: Path) -> list[QuestionSet]:
    path = Path(path)
    sets = parse(path.read_text(encoding="utf-8-sig", errors="replace"), path)
    if not sets:
        raise ValueError(
            f"no numbered questions found in {path} — expected lines beginning "
            "'1.', '2.', ..."
        )
    return sets


def discover(directory: Path) -> list[QuestionSet]:
    """Find every question set under `Analysis Questions/`."""
    directory = Path(directory)
    if not directory.is_dir():
        return []

    sets: list[QuestionSet] = []
    for path in sorted(directory.rglob("*.txt")):
        if path.name.startswith((".", "._")):
            continue
        try:
            sets.extend(load(path))
        except ValueError:
            continue  # a text file that isn't a question set
    return sets
