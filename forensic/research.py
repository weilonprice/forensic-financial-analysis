"""Parse the 100-step research workbook export into prompts.

The file in ``100 Steps Questions/`` is a text dump of a spreadsheet workbook,
not a question list written for this app. Three things follow from that, and
this module exists to deal with all three:

1.  **No anchors.** The sets in ``Analysis Questions/`` are found either by
    leading "1." numbering or by the trailing scoring boilerplate. This file has
    neither — zero numbered lines, zero "score out of 10". Its only structure is
    a ``[NN SECTION NAME]`` header per step, so that is what we split on.

2.  **Repeats.** Roughly half the lines are the same question asked N times for
    N entities: ten competitors, ten suppliers, twenty countries. Step 72 asks
    the same nine stock questions eleven times over. Asking each separately is
    both wasteful and worse — a model asked for "the 9th largest supplier" in
    isolation will invent one. Each run collapses to a single "list up to N"
    prompt. See :func:`_collapse`.

3.  **Spreadsheet furniture.** Many lines describe a cell rather than ask a
    question ("in the box on the right", "calculated for you"), and the
    template's example company survived the export, so questions refer to "the
    Computer market" and "the 2nd largest competitor (Microsoft)". Left in, the
    model answers about Apple while reading someone else's filing. See
    :data:`_FURNITURE` and :data:`_PLACEHOLDERS`.

Nothing here calls an API. Load a file and inspect it for free:

    python scripts/check_research.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

#: ``[72 STOCK DETAILS]``. The number is the workbook's step number and is worth
#: keeping: it is how the questions cross-reference each other ("from Step 88").
_STEP_HEADER = re.compile(r"^\[(\d{1,3})\s+(.+?)\s*\]$")

#: The ``----`` rule under each header.
_RULE = re.compile(r"^-{3,}$")


class LineKind(str, Enum):
    """What a line in the workbook actually is."""

    #: A research question to put to the model.
    QUESTION = "question"
    #: Step 4. Not a question — an input (company, industries, competitors) that
    #: later steps substitute into their own text. Resolved once per run.
    SETTING = "setting"
    #: A spreadsheet formula cell, e.g. "The market capitalization is calculated
    #: for you". Nothing to ask; the value is derived from other answers.
    COMPUTED = "computed"
    #: Asks the analyst to do something outside the app entirely — the two lines
    #: that say to phone a lawyer at LegalZoom and RocketLawyer.
    UNAVAILABLE = "unavailable"


#: Step 4 holds settings rather than questions.
SETTINGS_STEP = 4

#: Lines whose value is computed from other answers rather than researched.
#: Matched on the cleaned text. "calculated for you" is the workbook's own
#: marker and covers most of them; the rest state the formula instead.
_COMPUTED = re.compile(
    r"calculated for you"
    r"|^the dividend yield is the dividend divided by the stock price"
    r"|^the value of the average daily trading volume times the stock price is",
    re.IGNORECASE,
)

#: Two lines ask the analyst to book a call with a lawyer. Kept in the parse
#: (so the step's question count still reconciles against the source file) but
#: marked so the runner skips them rather than inventing a phone call.
_UNAVAILABLE = re.compile(r"LegalZoom|RocketLawyer", re.IGNORECASE)

#: Pure spreadsheet mechanics — text about *where to type*, carrying no part of
#: the question. Stripped before the prompt is built. Deliberately conservative:
#: each pattern names the workbook's own phrasing rather than trying to
#: generalise, because over-stripping silently removes meaning ("enter the
#: percent of revenue from this customer" is the question, not furniture).
_FURNITURE: tuple[re.Pattern[str], ...] = (
    re.compile(r"\s*Click me if you want to[^.]*\.", re.IGNORECASE),
    re.compile(r"\s*Only enter a number please in the cell on the right\.",
               re.IGNORECASE),
    re.compile(r"\s*\(you can change the years as well if you want to as they "
               r"are in white shaded boxes in row \d+\)", re.IGNORECASE),
    re.compile(r"\s*\(enter the (?:percent|%) in the box on the right[^)]*\)",
               re.IGNORECASE),
    # Both of these are trailing boilerplate, so they run to end of line. Do NOT
    # bound them with [^.]* — the workbook writes "the tab called 88 I.S.
    # FORECAST", and stopping at the first period cuts mid-abbreviation and
    # leaves ".S. FORECAST ..." glued to the question.
    re.compile(r"\s*You can track the aforementioned details on the tab "
               r"called .*$", re.IGNORECASE),
    re.compile(r"\s*For more details, please click the hyperlink link above on "
               r"row \d+ for a video explanation\..*$", re.IGNORECASE),
    re.compile(r"\s*\[see Tab \d+ for all links\]", re.IGNORECASE),
    re.compile(r"\s*,?\s*(?:and )?then in the box on the right of where you "
               r"entered the comment,?", re.IGNORECASE),
    # "on the right" and "on right" both occur.
    re.compile(r"\s*in the box on (?:the )?right"
               r"(?: of where you (?:entered|selected)[^.,)]*)?", re.IGNORECASE),
    re.compile(r"\s*in the cell on the right", re.IGNORECASE),
    re.compile(r"\s*Then on the right of the (?:input name|country box|"
               r"product/service name box|where you selected the \w+ name),?"
               r"\s*(?:please\s+)?", re.IGNORECASE),
    re.compile(r"\s*After you enter in a company name, the GDP per capita "
               r"statistic will appear on the right\.", re.IGNORECASE),
    re.compile(r"\s*Hard code over the GDP statistic if it is wrong\.",
               re.IGNORECASE),
    re.compile(r"^On the right,\s*please\s*", re.IGNORECASE),
    re.compile(r"^On the right,\s*", re.IGNORECASE),
    re.compile(r"\s*please enter your comments in the white box on the right",
               re.IGNORECASE),
    # Whatever survived the more specific patterns above. Always positional —
    # the workbook never uses "on the right" to mean anything but a cell.
    re.compile(r",?\s+on the right\b", re.IGNORECASE),
)

#: The example company's data, left behind by the export. These are not this
#: company's competitors or markets — they are Apple's, plus a run of joke names
#: from the template. Any of them reaching the model is a correctness bug, so
#: they are removed by name and the removal is asserted in check_research.py.
_PLACEHOLDER_NAMES = (
    "Samsung", "Microsoft", "Research in Motion", "Bluth Company",
    "Bubba Gump", "J.T. Marlin", "Wonka Industries", "Virtucon",
    "Los Pollos Hermanos", "Cyberdyne Systems",
)
_PLACEHOLDER_MARKETS = ("Computer", "Phone", "Tablet", "Watch", "Media")

_PLACEHOLDERS: tuple[re.Pattern[str], ...] = (
    # ", which you entered as the Computer market"
    re.compile(r",?\s*which you entered as the (?:"
               + "|".join(_PLACEHOLDER_MARKETS) + r") market", re.IGNORECASE),
    # "the 2nd largest competitor (Microsoft) has"
    re.compile(r"\s*\((?:" + "|".join(re.escape(n) for n in _PLACEHOLDER_NAMES)
               + r")\)"),
)

#: Ordinals, stripped when building the key two lines are grouped by, so that
#: "the 7th largest supplier" lands on the same key as "the largest supplier".
#: Covers 2nd through 20th — the widest run in the file is step 45's twenty
#: countries.
_ORDINAL = re.compile(r"\b(?:2nd|3rd|[4-9]th|1\d(?:st|nd|rd|th)|20th)\s+",
                      re.IGNORECASE)

#: "board member #1" through "#9".
_HASH_INDEX = re.compile(r"#\s*\d+")

_WHITESPACE = re.compile(r"\s+")


def _clean(text: str) -> str:
    """Strip spreadsheet furniture and template placeholders from one line."""
    for pattern in _PLACEHOLDERS:
        text = pattern.sub("", text)
    for pattern in _FURNITURE:
        # A space, not "": these patterns absorb the whitespace on either side
        # of the clause they remove, and substituting nothing welds the
        # surrounding words together ("...to the BOM.enter the cost...").
        # Runs of spaces are collapsed below.
        text = pattern.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    # Stripping a clause out of the middle of a sentence leaves debris: a space
    # before punctuation, a comma orphaned against a full stop, or a following
    # sentence that now begins lowercase.
    # Order matters. Drop a comma left stranded after a full stop BEFORE
    # pulling punctuation back onto the preceding word — the stranded comma is
    # always separated by the space the removed clause left behind, whereas
    # "i.e., solar" has none, and collapsing first would make the two
    # indistinguishable and eat a legitimate comma.
    text = re.sub(r"\.\s+,", ".", text)
    text = re.sub(r"\s+([.,;:])", r"\1", text)
    text = re.sub(r"[,;:]\s*\.", ".", text)
    # The workbook uses "...." as an ellipsis mid-sentence; collapsing it to a
    # bare "." would run two sentences together as "company.they must file".
    text = re.sub(r"\.{2,}", ". ", text)
    text = _WHITESPACE.sub(" ", text).strip(" ,;:")
    # Recapitalise every sentence, not just the first — "services. please enter"
    # is the giveaway that a mid-sentence clause was removed.
    #
    # The lookbehind spares dotted abbreviations by testing for a preceding
    # "<dot><letter>": the last period of "D.A.U." and of "i.e." is preceded by
    # one, so neither starts a new sentence, while "...to the BOM. enter" is not
    # and correctly becomes "BOM. Enter". Requiring whitespace after the period
    # is what keeps "Yelp.com" and "Vault.com" lowercase.
    text = re.sub(r"(^|(?<!\.[A-Za-z])[.?!]\s+)([a-z])",
                  lambda m: m.group(1) + m.group(2).upper(), text)
    # Terminate the sentence, but look past a closing quote: several settings
    # end with a quoted example (... instead of "The Computer Market.") and
    # already carry their full stop inside the quotes.
    if text and text.rstrip("\"'”’")[-1:] not in ("", ".", "?", "!", ":"):
        text += "."
    return text


def _key(text: str) -> str:
    """The identity two lines are considered 'the same question' under."""
    text = _ORDINAL.sub("", text)
    text = _HASH_INDEX.sub("#N", text)
    return _WHITESPACE.sub(" ", text).strip().lower()


def _collapse(keys: list[str]) -> list[tuple[int, int, int]]:
    """Find repeated blocks. Returns ``(start, period, repeats)`` spans.

    Handles both shapes the workbook uses, because both reduce to the same
    problem once ordinals are normalised out by :func:`_key`:

    * one question repeated per entity — ten suppliers, twenty countries;
      period 1.
    * a *group* of questions repeated per entity — step 72's nine stock
      questions asked once for the company and once per competitor; period 9.
      Consecutive-duplicate matching cannot see this one, since the sequence is
      A B C A B C rather than A A A.

    Greedy, taking the widest reach at each position, smallest period on a tie.
    """
    spans: list[tuple[int, int, int]] = []
    i = 0
    while i < len(keys):
        best_period, best_repeats = 1, 1
        for period in range(1, (len(keys) - i) // 2 + 1):
            repeats = 1
            while keys[i + repeats * period: i + (repeats + 1) * period] == \
                    keys[i: i + period]:
                repeats += 1
            if repeats >= 2 and repeats * period > best_period * best_repeats:
                best_period, best_repeats = period, repeats
        spans.append((i, best_period, best_repeats))
        i += best_period * best_repeats
    return spans


@dataclass(frozen=True)
class ResearchQuestion:
    """One prompt, which may stand for up to :attr:`repeat` source lines."""

    step: int
    step_name: str
    #: Position within the step, 1-based. Stable across runs; used as an id.
    index: int
    #: Cleaned text, furniture and placeholders removed.
    text: str
    kind: LineKind
    #: Source lines this stands for, verbatim. Length equals :attr:`repeat`.
    sources: tuple[str, ...] = ()

    @property
    def repeat(self) -> int:
        """How many entities to ask for. 1 for an ordinary question."""
        return len(self.sources)

    @property
    def question_id(self) -> str:
        return f"{self.step}.{self.index}"

    @property
    def prompt(self) -> str:
        """The text to send, with the repeat turned into an explicit request."""
        if self.repeat <= 1:
            return self.text
        return (f"{self.text}\n\nList up to {self.repeat}, in order, most "
                f"significant first. Give only those the sources actually "
                f"support — fewer than {self.repeat} is expected and correct if "
                f"that is all there is. Do not pad the list.")


@dataclass(frozen=True)
class ResearchStep:
    """One numbered step of the workbook."""

    number: int
    name: str
    questions: tuple[ResearchQuestion, ...] = field(default_factory=tuple)
    #: Lines read from the file for this step, before collapsing.
    source_lines: int = 0

    @property
    def askable(self) -> tuple[ResearchQuestion, ...]:
        return tuple(q for q in self.questions if q.kind is LineKind.QUESTION)

    def __len__(self) -> int:
        return len(self.questions)


def parse(text: str) -> tuple[ResearchStep, ...]:
    """Parse the workbook export. See module docstring for the format."""
    raw_steps: list[tuple[int, str, list[str]]] = []
    for line in text.splitlines():
        stripped = line.strip()
        header = _STEP_HEADER.match(stripped)
        if header:
            raw_steps.append((int(header.group(1)), header.group(2), []))
            continue
        if not raw_steps or not stripped or _RULE.match(stripped):
            continue
        raw_steps[-1][2].append(stripped)

    steps: list[ResearchStep] = []
    for number, name, lines in raw_steps:
        cleaned = [_clean(line) for line in lines]
        spans = _collapse([_key(c) for c in cleaned])

        questions: list[ResearchQuestion] = []
        index = 0
        for start, period, repeats in spans:
            for offset in range(period):
                index += 1
                text_ = cleaned[start + offset]
                sources = tuple(lines[start + offset + step * period]
                                for step in range(repeats))
                if number == SETTINGS_STEP:
                    kind = LineKind.SETTING
                elif _UNAVAILABLE.search(text_):
                    kind = LineKind.UNAVAILABLE
                elif _COMPUTED.search(text_):
                    kind = LineKind.COMPUTED
                else:
                    kind = LineKind.QUESTION
                questions.append(ResearchQuestion(
                    step=number, step_name=name, index=index, text=text_,
                    kind=kind, sources=sources,
                ))
        steps.append(ResearchStep(number=number, name=name,
                                  questions=tuple(questions),
                                  source_lines=len(lines)))
    return tuple(steps)


def load(path: Path | str) -> tuple[ResearchStep, ...]:
    """Parse a workbook export from disk."""
    path = Path(path)
    steps = parse(path.read_text(encoding="utf-8"))
    if not steps:
        raise ValueError(
            f"no steps found in {path} — expected headers like '[12 SECTION NAME]'"
        )
    return steps


def discover(folder: Path | str) -> tuple[ResearchStep, ...]:
    """Load the workbook export from a folder, ignoring macOS cruft."""
    folder = Path(folder)
    candidates = sorted(p for p in folder.glob("*.txt")
                        if not p.name.startswith((".", "._")))
    if not candidates:
        raise ValueError(f"no .txt workbook export found in {folder}")
    if len(candidates) > 1:
        raise ValueError(
            f"expected one workbook export in {folder}, found "
            f"{[p.name for p in candidates]}"
        )
    return load(candidates[0])
