"""Running a question set against a filing.

One Claude call per question, all reading the same cached filing. Costs
marginally more than batching all twelve into one call and buys three things:
each question gets undivided attention, output format holds across the whole
set, and a failure on question 7 does not take down the other eleven.
"""

from __future__ import annotations

import concurrent.futures
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Sequence

from .claude import Answer, Claude, ClaudeError, Usage
from .llm import LLMClient, create_client
from .filing import Filing
from .questions import Question, QuestionKind, QuestionSet
from .sections import (
    Section,
    SectionSpec,
    audit_facts as section_facts,
    find as find_section,
)


class ConcernLevel(str, Enum):
    """How much concern a finding warrants, on four anchored levels.

    Replaces a 1-10 score. The scale was the main source of run-to-run
    variance: nobody — model or human — reliably discriminates ten levels of
    concern, and an unanchored "7" has no shared meaning to reproduce, so
    repeat runs of an identical filing drifted by a point in either direction.
    Four levels, each defined by what is observably true of the disclosure,
    absorb that uncertainty instead of flipping on it.

    The bands are exactly the ones the 1-10 prompt already described (10 /
    7-9 / 4-6 / 1-3), so this discards precision that was never real while
    leaving earlier runs broadly comparable.

    Ordering runs least to most concerning, which also drops the inverted
    scale — "severe" needs no explanation of which direction is bad.
    """

    NONE = "none"
    MINOR = "minor"
    MATERIAL = "material"
    SEVERE = "severe"

    @property
    def rank(self) -> int:
        """0 = nothing to see, 3 = serious. Sort and threshold on this."""
        return _CONCERN_ORDER.index(self)

    @property
    def label(self) -> str:
        return {
            ConcernLevel.NONE: "No concern",
            ConcernLevel.MINOR: "Minor",
            ConcernLevel.MATERIAL: "Material",
            ConcernLevel.SEVERE: "Severe",
        }[self]

    @property
    def flagged(self) -> bool:
        """Whether this belongs in the report's flagged list."""
        return self.rank >= ConcernLevel.MATERIAL.rank


_CONCERN_ORDER: tuple[ConcernLevel, ...] = (
    ConcernLevel.NONE,
    ConcernLevel.MINOR,
    ConcernLevel.MATERIAL,
    ConcernLevel.SEVERE,
)

#: The anchor text. Lives here because it is needed in two places that must not
#: drift apart: the schema description, which the model sees while its output is
#: being constrained, and the system prompt, which it reads while reasoning.
CONCERN_ANCHORS = (
    "none — the disclosure is present, complete, and consistent with the prior "
    "year; exactly what a well-controlled filer should report. "
    "minor — present but thinner than the prior year, reworded without "
    "explanation, or a structural consideration worth noting with no evidence "
    "of a problem. "
    "material — an omission, change, or inconsistency a reasonable analyst "
    "would want explained before relying on these statements. "
    "severe — absent, contradictory, or contradicted elsewhere in the filing; "
    "a red flag that materially undermines confidence."
)

#: The response contract. Enforced by the API, not requested in the prompt —
#: the model cannot omit a field, wrap the object in prose, or return the
#: concern level as a sentence instead of one of the four values.
RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": (
                "A label of at most 60 characters naming WHAT THE QUESTION "
                "ASKS. Not what the answer found — this heads a row in a list "
                "of questions, so a conclusion reads wrongly beside a level. "
                "E.g. 'Auditor identity and reputation', 'Inventory growth vs "
                "revenue', 'GAAP to non-GAAP, earnings quality, accruals'."
            ),
        },
        "answer": {
            "type": "string",
            "description": "The substantive answer, two sentences or fewer.",
        },
        "concern": {
            "type": "string",
            "description": (
                "Exactly one sentence, third person, explaining whether this "
                "finding warrants concern and why. Never uses 'you' or 'I'."
            ),
        },
        "concern_level": {
            "type": "string",
            "enum": [level.value for level in _CONCERN_ORDER],
            "description": (
                "How much concern this finding warrants. " + CONCERN_ANCHORS
            ),
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Verbatim quotations copied character-for-character from the "
                "filing text, supporting every figure and factual claim made "
                "in `answer`. One entry per supporting passage."
            ),
        },
    },
    "required": ["title", "answer", "concern", "concern_level", "evidence"],
    "additionalProperties": False,
}


#: Summary questions digest the answers already produced. They carry no concern
#: sentence and no level, so they need their own contract — reusing the standard
#: one would force the model to invent a judgment for a question that never
#: asked for one.
SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": (
                "The summary, respecting any stated sentence and character "
                "limits, in a single paragraph."
            ),
        },
    },
    "required": ["summary"],
    "additionalProperties": False,
}


#: The eleven GICS sectors — exactly the rows in the DSO benchmark table.
#:
#: The classification is constrained to this list by enum rather than left free.
#: An unconstrained answer of "Technology" or "Internet Services" would match no
#: row in the benchmark table, and the comparison would silently have nothing to
#: measure against. Every value here is guaranteed to resolve to a DSO band.
GICS_SECTORS: list[str] = [
    "Information Technology", "Consumer Discretionary", "Consumer Staples",
    "Health Care", "Financials", "Industrials", "Materials", "Energy",
    "Utilities", "Communication Services", "Real Estate",
]

SECTOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sector": {
            "type": "string", "enum": GICS_SECTORS,
            "description": "The company's GICS sector.",
        },
        "rationale": {
            "type": "string",
            "description": "One sentence on why this sector rather than the "
                           "nearest alternative.",
        },
    },
    "required": ["sector", "rationale"],
    "additionalProperties": False,
}

SECTOR_SYSTEM_PROMPT = """\
You classify public companies into their GICS sector, the eleven-sector scheme \
used for the S&P 500.

Give the sector the company is actually classified under, not the one its \
products superficially suggest. Several large companies sit somewhere a casual \
reader would not expect — Alphabet and Meta are Communication Services rather \
than Information Technology, Amazon and Tesla are Consumer Discretionary, \
Visa and Mastercard are Financials. Where a company could plausibly sit in two \
sectors, say which one you rejected and why in the rationale."""


def classify_sector(
    company: str,
    tickers: Sequence[str] = (),
    *,
    claude: LLMClient | None = None,
    llm: LLMClient | None = None,
) -> tuple[str, str]:
    """Classify a company into a GICS sector. Returns (sector, rationale).

    Deliberately does NOT see the filing. Sector membership is not stated in a
    10-K — there is no SIC, NAICS or GICS tag anywhere in the XBRL — so the
    document adds nothing but cost. Sending only the name keeps this to a
    fraction of a cent, and keeps it independent of the cached context, which
    cannot be built until the sector is known.
    """
    client = llm or claude or create_client(effort="low")
    listing = f" (ticker{'s' if len(tickers) > 1 else ''}: {', '.join(tickers)})" \
        if tickers else ""
    answer = client.ask(
        f"Which GICS sector is {company}{listing} classified under?",
        system=SECTOR_SYSTEM_PROMPT,
        schema=SECTOR_SCHEMA,
        effort="low",
    )
    payload = answer.data or {}
    return str(payload.get("sector", "")), str(payload.get("rationale", ""))


#: A cell that may legitimately have no value — the earliest year has no prior
#: year to compute a change against. Expressed as anyOf rather than a type list
#: because structured outputs support the former.
_NUM_OR_NULL: dict[str, Any] = {"anyOf": [{"type": "number"}, {"type": "null"}]}

#: Task 1 — the DSO data-entry grid.
DSO_TABLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "fiscal_years": {
            "type": "array", "items": {"type": "string"},
            "description": "Four fiscal-year labels, oldest first: the -3, -2, "
                           "-1 and most recent columns (e.g. FY2022..FY2025).",
        },
        "revenue": {
            "type": "array", "items": _NUM_OR_NULL,
            "description": "Annual revenue for each of the four years, in the "
                           "units given by `units`.",
        },
        "revenue_yoy_pct": {
            "type": "array", "items": _NUM_OR_NULL,
            "description": "Year-over-year revenue change in percent. Null for "
                           "any year with no prior-year figure to compare to.",
        },
        "accounts_receivable": {
            "type": "array", "items": _NUM_OR_NULL,
            "description": "Accounts receivable, net, per year. Null where the "
                           "figure is not available in either filing.",
        },
        "ar_yoy_pct": {"type": "array", "items": _NUM_OR_NULL},
        "dso_days": {
            "type": "array", "items": _NUM_OR_NULL,
            "description": "Days sales outstanding = (accounts receivable / "
                           "revenue) x 365. Null where receivables are absent.",
        },
        "units": {
            "type": "string",
            "description": "Units of the revenue and receivables figures, e.g. "
                           "'USD millions'.",
        },
        "summary": {
            "type": "string",
            "description": "One or two sentences on what the table shows, "
                           "naming the DSO trend.",
        },
        "evidence": {
            "type": "array", "items": {"type": "string"},
            "description": "Verbatim quotations from the filings for every "
                           "revenue and receivables figure entered.",
        },
    },
    "required": ["fiscal_years", "revenue", "revenue_yoy_pct",
                 "accounts_receivable", "ar_yoy_pct", "dso_days", "units",
                 "summary", "evidence"],
    "additionalProperties": False,
}

#: Task 2 — DSO measured against its sector band.
DSO_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sector": {"type": "string",
                   "description": "The S&P 500 sector used for the comparison."},
        "dso_low": {"type": "number"},
        "dso_high": {"type": "number"},
        "current_dso_days": {"type": "number"},
        "within_range": {"type": "boolean"},
        "summary": {"type": "string",
                    "description": "One or two sentences stating the sector, "
                                   "the band, and where the DSO falls."},
        "assessment": {"type": "string",
                       "description": "Exactly one sentence, third person, on "
                                      "whether this warrants concern and why."},
        "concern_level": {
            "type": "string",
            "enum": [level.value for level in _CONCERN_ORDER],
            "description": ("How much concern the DSO comparison warrants. "
                            + CONCERN_ANCHORS),
        },
        "evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sector", "dso_low", "dso_high", "current_dso_days",
                 "within_range", "summary", "assessment", "concern_level",
                 "evidence"],
    "additionalProperties": False,
}


def _cell(value: Any, fmt: str) -> str:
    """Format one table cell, showing an em dash where there is no value.

    A null here is meaningful — the earliest year has no prior year to measure
    against — so it is rendered as an explicit blank rather than a zero.
    """
    if value is None:
        return "—"
    try:
        return fmt.format(float(value))
    except (TypeError, ValueError):
        return str(value)


def dso_table(payload: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    """Turn a DSO task payload into a header row and body rows.

    Shared by the Markdown and PDF renderers so the two cannot drift — a table
    that reads differently in the PDF than in the Markdown is a reporting bug
    waiting to happen.
    """
    years = [str(y) for y in (payload.get("fiscal_years") or [])]
    units = payload.get("units") or ""
    header = [""] + years

    def row(label: str, key: str, fmt: str) -> list[str]:
        values = payload.get(key) or []
        cells = [_cell(values[i] if i < len(values) else None, fmt)
                 for i in range(len(years))]
        return [label] + cells

    body = [
        row(f"Revenue ({units})" if units else "Revenue", "revenue", "{:,.0f}"),
        row("  YoY change", "revenue_yoy_pct", "{:+.1f}%"),
        row(f"Accounts receivable ({units})" if units else "Accounts receivable",
            "accounts_receivable", "{:,.0f}"),
        row("  YoY change", "ar_yoy_pct", "{:+.1f}%"),
        row("DSO (days)", "dso_days", "{:.1f}"),
    ]
    return header, body


def dso_analysis_rows(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Key/value rows for the sector-benchmark task."""
    low, high = payload.get("dso_low"), payload.get("dso_high")
    dso = payload.get("current_dso_days")
    inside = payload.get("within_range")
    return [
        ("Sector", str(payload.get("sector") or "—")),
        ("Healthy DSO range", f"{_cell(low, '{:.0f}')} – {_cell(high, '{:.0f}')} days"),
        ("Company DSO", f"{_cell(dso, '{:.1f}')} days"),
        ("Within range", "yes" if inside else "no"),
    ]


@dataclass(frozen=True)
class TaskSpec:
    """How to run one table task and read its result back."""

    slug: str
    schema: dict[str, Any]
    #: Field carrying a 0-10 rating, when the task asks for one. Tasks without
    #: a rating carry no level and stay out of the distribution.
    rating_field: str | None = None
    #: Field holding the one-sentence judgement, shown where a concern would be.
    assessment_field: str | None = None


#: Registered tasks, keyed by a slug from the task's title. An unregistered
#: task falls back to the ordinary answer/concern/level path rather than
#: failing, so adding "Task 3: ..." to the file still produces something.
TASK_SPECS: dict[str, TaskSpec] = {
    "dso_data_entry": TaskSpec("dso_data_entry", DSO_TABLE_SCHEMA,
                               assessment_field=None),
    "dso_analysis": TaskSpec("dso_analysis", DSO_ANALYSIS_SCHEMA,
                             rating_field="concern_level",
                             assessment_field="assessment"),
}


SYSTEM_PROMPT = """\
You are a forensic financial analyst at a hedge fund, examining an SEC filing \
on behalf of institutional investors. Your reader is a professional who will \
act on what you write.

GROUNDING
- Answer from the filing text provided. Do not infer facts the document does \
not support, and do not assume a company follows a practice merely because it \
is common.
- If the filing does not address a question, say so plainly. "The report does \
not mention X" is a complete and useful answer; inventing a plausible one is \
not.
- Use knowledge from outside the filing ONLY where a question explicitly asks \
about something the document cannot answer — a firm's reputation, standing, or \
track record. Everywhere else, stay strictly inside the document.
- Distinguish the two auditor's reports. A 10-K normally contains an opinion on \
the financial statements and a separate opinion on internal control over \
financial reporting. They have different scopes and different conclusions.

ANSWERING
- `title`: a short caption for the question, at most 60 characters. It names the
subject the question is about, never the conclusion you reached — the report
lists it beside the level, where "Receivables quality deteriorating" would be
asserting a finding in what is meant to be a question list.
- `answer`: at most two sentences by default — but a question's own stated \
limit always wins. A question asking for "less than 5 sentences" may use five; \
a stated character count is a hard cap. Never let the default override an \
instruction the question makes explicitly. Lead with the finding, not with \
preamble. Name specifics — firm names, dates, dollar amounts, defined terms — \
rather than characterising them.
- `concern`: exactly one sentence, always present, written in the third person. \
Never use "you", "your", "I", "we", or the reader's name. Write it even when \
there is nothing to be concerned about, stating plainly why the finding is \
unremarkable.
- `concern_level`: one of four values, defined below.

CONCERN LEVEL
Choose the level by what is observably true of the disclosure, not by an \
overall impression:
  none      the disclosure is present, complete, and consistent with the prior \
year — exactly what a well-controlled filer should report
  minor     present but thinner than the prior year, reworded without \
explanation, or a structural consideration worth noting with no evidence of a \
problem
  material  an omission, change, or inconsistency a reasonable analyst would \
want explained before relying on these statements
  severe    absent, contradictory, or contradicted elsewhere in the filing — a \
red flag that materially undermines confidence

Decide by asking which description the filing actually matches, then name that \
level. Do not reason about degree first and translate afterwards. If a finding \
sits between two levels, choose the less severe one and let `concern` carry \
the nuance — that sentence is where a borderline judgment belongs, not the \
level.

Do not inflate the level to appear rigorous or deflate it to be agreeable. \
Most questions about a clean filing are genuinely `none`; say so.

EVIDENCE
Every figure and factual claim in `answer` must be supported by a verbatim \
quotation in `evidence`, copied character-for-character from the filing text \
above. The application checks each quotation against the document \
mechanically and flags any that does not appear, so a paraphrase, a reformatted \
number, or text stitched together from two places will be reported as \
unverified.

Beware near-duplicate passages. The audit report section holds TWO separate \
reports whose sentences differ by only a few words — "We also have audited, in \
accordance with the standards of the PCAOB, the Company's internal control..." \
in one, "We have audited Alphabet Inc.'s internal control..." in the other — and \
the current and prior year contain their own near-identical versions again. \
Quote one passage in full, from a single place. Merging the opening of one into \
the continuation of another produces a sentence that appears nowhere in the \
filing, and it will be reported as unverified even though the underlying fact \
is right.

When citing a figure from a table, quote enough of the row to show which \
column and which period the number comes from. A bare number proves nothing, \
and reading a figure from the prior-year column is the single most common way \
this analysis goes wrong — a comparative table shows two years side by side and \
the wrong column is a plausible-looking, entirely incorrect answer. Check the \
column before you quote it.

FINDINGS ABOUT WHAT IS ABSENT
Some of the most valuable observations concern what a filing does NOT say: an \
estimate the auditor did not designate a critical audit matter, a risk \
management describes but never quantifies, a reconciliation that is not \
provided. Do not suppress such an observation merely because no single sentence \
states it — an absence is still evidenced, indirectly, by quoting both halves \
of the contrast:
  (a) the complete enumeration showing the item is missing — the full list of \
critical audit matters, the whole set of disclosures given; and
  (b) the passages establishing that the missing item is material enough for \
its absence to be worth noting.
Put both in `evidence`, and state the inference in `answer` as your own \
reasoning rather than as something the filing asserts. Raise such a point only \
when the omitted item is genuinely material; do not manufacture one to appear \
thorough.

COMPARING YEARS
The context may include the prior year's filing alongside the current one. \
Unless a question explicitly asks about differences between years, "the audit \
report", "the opinion", "the MD&A", and "the company" refer to the CURRENT \
year. Use the prior year only to answer comparison questions or to give a \
current-year finding its context, and always say which year a figure comes from.

SCOPE
The context carries more than one section of the filing. Each question is \
prefixed with the section it concerns; answer from that section, and reach into \
the rest of the filing only to verify or contextualise what that section says. \
A question about the MD&A is not answered from the audit report, and vice \
versa.

TABLE TASKS
A task supplies an ASCII table to populate rather than a question to answer. \
Read the template for which figures belong in which column, then return the \
values as structured data — the application renders the table itself, so do \
not reproduce the ASCII layout.

Fill every cell you can from the filings, including cells the template shows \
as "N/A": those mark values to be calculated, not values to omit. Leave a cell \
null only when the underlying figure genuinely does not exist — the earliest \
year has no prior year to measure a change against, and receivables are not \
available for every year the revenue is.

Figures for the earliest years come from the PRIOR year's filing. Where a year \
appears in both filings, the two must agree; if they do not, say so in the \
summary rather than silently picking one. Quote every figure you enter in \
`evidence`, so each input can be checked even though the arithmetic cannot be.

SUMMARY QUESTIONS
Some questions ask you to summarise the answers already given rather than to \
examine the filing. For those the prior answers are supplied inside the \
question itself: work from them, obey any stated sentence and character limit \
exactly, and supply no evidence quotations — the task is condensing analysis, \
not citing the document.

VERIFIED FACTS
The context begins with a block of facts extracted mechanically from the \
filing. Treat those values as authoritative and use them verbatim rather than \
re-deriving them, so that separate answers cannot disagree about plain matters \
of record.

FORMAT
Each question repeats its own formatting instructions. Map them onto the \
response fields: the substantive reply is `answer` and the "should I be \
worried" sentence is `concern`.

Where a question asks for "a score out of 10", answer it with \
`concern_level` instead. That wording is left over from an earlier version of \
this report and the ten-point scale no longer exists — a question asking for a \
number is asking how concerned to be, which the four levels now answer. Never \
put a number in `answer` or `concern` in response to it."""


#: Characters that differ between the filing's typography and what a model
#: reproduces: curly quotes, dashes, non-breaking spaces — and the currency
#: symbol. A model quoting a table row reconstructs it as "$47,964 | $52,340"
#: where the filing renders "47,964 | 52,340": same figures, added currency
#: marks. Dropping "$" on both sides removes that false alarm without weakening
#: the check, since the digits still have to match exactly.
_TYPOGRAPHY = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ", "$": "",
})


def normalize_for_match(text: str) -> str:
    """Fold typography and whitespace so quotation matching is about content."""
    return " ".join(text.translate(_TYPOGRAPHY).split()).casefold()


def verify_evidence(quotes: list[str], normalized_source: str) -> list[str]:
    """Return the quotations that do not appear in the source.

    This is the check that catches the failure the model cannot catch itself:
    a figure recalled from the wrong column, or a number that was never in the
    document at all. It is a substring test, not a judgement — it proves the
    text exists, not that it supports the claim.
    """
    missing: list[str] = []
    for quote in quotes:
        cleaned = normalize_for_match(quote)
        # Very short fragments match by accident and prove nothing.
        if len(cleaned) < 8 or cleaned not in normalized_source:
            missing.append(quote)
    return missing


def _parse_level(value: Any) -> ConcernLevel:
    """Read a concern level out of a model response.

    The schema constrains this to the four values, so an unrecognised one means
    something upstream changed rather than the model misbehaving. Falling back
    to the *most* concerning level makes that loud: a silent `none` would read
    as a clean finding and hide the fault, whereas an unexplained `severe`
    surfaces in the flagged list where someone will look at it.
    """
    if isinstance(value, ConcernLevel):
        return value
    # Check for None before stringifying: str(None).lower() is "none", which is
    # a *valid* level, so a missing field would quietly become "no concern" —
    # the precise failure this function exists to prevent.
    if not isinstance(value, str):
        return ConcernLevel.SEVERE
    try:
        return ConcernLevel(value.strip().lower())
    except ValueError:
        return ConcernLevel.SEVERE


@dataclass(frozen=True)
class QuestionResult:
    question: Question
    answer: str
    concern: str
    concern_level: ConcernLevel = ConcernLevel.NONE
    usage: Usage | None = None
    elapsed_seconds: float = 0.0
    #: Verbatim quotations the model offered in support of its answer.
    evidence: list[str] = field(default_factory=list)
    #: Quotations that could not be found in the filing. A non-empty list means
    #: at least one cited fact is unsupported — treat the answer as suspect.
    unverified: list[str] = field(default_factory=list)
    #: Short caption returned by the model, used as the question's label in the
    #: report. Empty for tasks and summaries, which carry their own headings.
    title: str = ""
    #: Structured payload for table tasks; None for ordinary questions.
    data: dict[str, Any] | None = None
    #: Whether this result carries a concern level that belongs in the
    #: section distribution.
    #: False for summaries, and for tasks that ask for no rating.
    has_level: bool = True
    #: How many model calls this question took. >1 means a length retry fired.
    #: Recorded because a summary that passed on the first try and one that
    #: passed on the third are indistinguishable afterwards — usage reports only
    #: the final attempt.
    attempts: int = 1
    #: Set when the question failed. `concern_level` is then meaningless and
    #: the report
    #: shows the failure rather than a fabricated finding.
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def evidence_ok(self) -> bool:
        return not self.unverified

    @property
    def label(self) -> str:
        """What the report calls this question.

        The model's caption when there is one, falling back to the text-derived
        topic — which is what a failed question, a task, or a PDF regenerated
        from a JSON predating this field will have.
        """
        return self.title or self.question.topic


@dataclass
class AnalysisRun:
    filing: Filing
    question_set: QuestionSet
    section: Section | None
    prior_filing: Filing | None = None
    results: list[QuestionResult] = field(default_factory=list)
    model: str = ""
    started_at: str = ""
    elapsed_seconds: float = 0.0

    # -- aggregates -------------------------------------------------------

    @property
    def successful(self) -> list[QuestionResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> list[QuestionResult]:
        return [r for r in self.results if not r.ok]

    @property
    def scored(self) -> list[QuestionResult]:
        """Only questions that actually carry a concern level.

        A summary question rates nothing, and counting it would distort the
        section's distribution with a question that never made a judgment."""
        return [r for r in self.successful if r.has_level]

    @property
    def summaries(self) -> list[QuestionResult]:
        return [
            r for r in self.successful
            if r.question.kind is QuestionKind.SUMMARY
        ]

    @property
    def distribution(self) -> dict[ConcernLevel, int]:
        """How many questions landed at each level, worst level first.

        Replaces the old mean score deliberately. Concern levels are ordinal,
        not numeric — the distance from `none` to `minor` is not the same
        quantity as `material` to `severe`, so averaging them produced a number
        that looked precise and meant nothing. It also invited comparison
        across sections that were never calibrated against each other. A count
        per level says what the mean was reaching for without implying
        arithmetic the scale does not support.
        """
        counts = {level: 0 for level in reversed(_CONCERN_ORDER)}
        for result in self.scored:
            counts[result.concern_level] += 1
        return counts

    @property
    def worst(self) -> ConcernLevel | None:
        """The most concerning level reached anywhere in this section."""
        levels = [r.concern_level for r in self.scored]
        return max(levels, key=lambda level: level.rank) if levels else None

    @property
    def with_unverified(self) -> list[QuestionResult]:
        """Answers citing at least one quotation not found in the filing."""
        return [r for r in self.successful if not r.evidence_ok]

    @property
    def unverified_count(self) -> int:
        return sum(len(r.unverified) for r in self.successful)

    @property
    def evidence_count(self) -> int:
        return sum(len(r.evidence) for r in self.successful)

    def flagged(self,
                threshold: ConcernLevel = ConcernLevel.MATERIAL,
                ) -> list[QuestionResult]:
        """Questions at `material` or worse, most concerning first.

        These are the report's findings. Everything else is confirmation that
        the filing is unremarkable in that respect — worth recording, not worth
        an analyst's attention.
        """
        return sorted(
            (r for r in self.scored if r.concern_level.rank >= threshold.rank),
            key=lambda r: r.concern_level.rank,
            reverse=True,
        )

    @property
    def total_usage(self) -> Usage:
        return Usage(
            input_tokens=sum(r.usage.input_tokens for r in self.results if r.usage),
            output_tokens=sum(r.usage.output_tokens for r in self.results if r.usage),
            cache_creation_tokens=sum(
                r.usage.cache_creation_tokens for r in self.results if r.usage
            ),
            cache_read_tokens=sum(
                r.usage.cache_read_tokens for r in self.results if r.usage
            ),
        )


# ------------------------------------------------------------------- context


def _elide_extracted(full_text: str, bundles: Sequence[SectionBundle]) -> str:
    """Drop from the full filing the spans already pinned above it.

    The context pins each located section in full, then appends the whole filing
    for cross-reference — so every pinned section appeared *twice*, once in its
    own block and again inside the full text. On Alphabet that duplicate ran
    193k characters, about 65k tokens: 47% of the full-filing block and, once
    multiplied by one cache write and seventy cache reads, roughly a quarter of
    the run's cost for a second copy of text the model already had.

    The full text is still worth carrying — Item 1 (Business), Item 1A (Risk
    Factors), Item 3 (Legal Proceedings) and Item 9A (Controls) appear nowhere
    else — so this removes only the exact duplicated spans and leaves a pointer
    in their place, preserving the surrounding reading order.

    Matching is exact and per-section: a section whose text is not found
    verbatim is left alone rather than approximately matched, because a fuzzy
    match here would silently delete filing content the analysis depends on.

    Sections are elided longest-first because they nest — Item 8 contains the
    audit reports, so the financial-statements span contains the audit-report
    span. Shortest-first removes the inner one, which leaves the outer span no
    longer matching the filing verbatim, and the exact-match guard then skips
    the largest section entirely. That silently salvaged only a third of the
    duplication. Once the outer span goes, the inner one is already gone and
    its own pass correctly finds nothing to do.
    """
    ordered = sorted(
        (b for b in bundles if b.current is not None),
        key=lambda b: len(b.current.text),
        reverse=True,
    )
    for bundle in ordered:
        section_text = bundle.current.text
        # Guard against removing something trivially short, which could match
        # in the wrong place and take real content with it.
        if len(section_text) < 500 or full_text.count(section_text) != 1:
            continue
        full_text = full_text.replace(
            section_text,
            f"\n[{bundle.spec.title} appears in full above, under "
            f"'CURRENT YEAR SECTION: {bundle.spec.title}'. Omitted here to "
            f"avoid duplication.]\n",
        )
    return full_text


def _filing_header(filing: Filing, label: str) -> str:
    facts = filing.facts
    lines = [
        f"=== {label} ===",
        f"Company: {facts.company_name or 'unknown'}",
        f"Document type: {facts.document_type or 'unknown'}",
        f"Fiscal year: {facts.fiscal_year or 'unknown'}",
        f"Period ending: {filing.period_end.isoformat() if filing.period_end else 'unknown'}",
    ]
    if filing.accession:
        lines.append(f"EDGAR accession: {filing.accession.raw}")
    return "\n".join(lines)


@dataclass
class SectionBundle:
    """One filing section, in both years."""

    spec: SectionSpec
    current: Section | None
    prior: Section | None = None


@dataclass
class Workspace:
    """The cached prefix, shared by every question set in a run.

    Built once. Both question sets read the same context so the filing is
    written to cache a single time — two contexts would mean two cache writes
    of ~120k tokens each for no analytical benefit.
    """

    filing: Filing
    prior_filing: Filing | None
    bundles: list[SectionBundle]
    context: str
    normalized_context: str
    #: Set once the first question has written the cache. Until then, questions
    #: must run one at a time.
    cache_warm: bool = False

    def bundle(self, key: str | None) -> SectionBundle | None:
        return next((b for b in self.bundles if b.spec.key == key), None)


def prepare(
    filing: Filing,
    *,
    prior_filing: Filing | None = None,
    specs: Sequence[SectionSpec] = (),
    sector: str | None = None,
) -> Workspace:
    """Locate every section in both filings and assemble the cached prefix."""
    document_text = filing.document_text()
    prior_text = prior_filing.document_text() if prior_filing else None

    bundles = [
        SectionBundle(
            spec=spec,
            current=find_section(document_text, spec),
            prior=find_section(prior_text, spec) if prior_text else None,
        )
        for spec in specs
    ]

    context = build_context(filing, bundles, prior_filing=prior_filing,
                            sector=sector)
    return Workspace(
        filing=filing,
        prior_filing=prior_filing,
        bundles=bundles,
        context=context,
        # Normalised once, not per question: this is a ~480,000-character
        # string and every answer's quotations are checked against it.
        normalized_context=normalize_for_match(context),
    )


def build_context(
    filing: Filing,
    bundles: Sequence[SectionBundle],
    *,
    prior_filing: Filing | None = None,
    sector: str | None = None,
) -> str:
    """Assemble the cached prefix shared by every question.

    Layout: identity, mechanically-verified facts, each target section for the
    current year, the full current filing for cross-reference, then the prior
    year's identity and the same sections again for comparison questions.

    This string must be byte-identical across all questions in a run, or the
    cache misses and every question re-bills the whole filing. Nothing
    per-question, and nothing time-varying, may appear here.

    The prior year contributes only its *sections*, not its full 10-K. The
    comparison questions ask how the audit reports and MD&As differ; carrying a
    second complete filing would add ~90,000 tokens to answer questions about
    ~68,000 characters of it.
    """
    facts = filing.facts
    auditor_name, _, auditor_location = facts.auditor

    header = [
        _filing_header(filing, "FILING UNDER EXAMINATION — CURRENT YEAR"),
        f"CIK: {facts.cik or 'unknown'}",
    ]
    if auditor_name:
        location = f", {auditor_location}" if auditor_location else ""
        header.append(f"Auditor per cover page tags: {auditor_name}{location}")

    parts = ["\n".join(header)]

    # Facts every question needs and none should have to re-derive. Extracted
    # by pattern from the audit report, so they are matters of record rather
    # than model output.
    audit_bundle = next((b for b in bundles if b.spec.key == "audit_report"), None)
    if audit_bundle is not None and audit_bundle.current is not None:
        audit = section_facts(audit_bundle.current)
        verified = [
            "=== VERIFIED FACTS (extracted mechanically — use verbatim) ===",
            f"Auditor's reports present: {audit.report_count} "
            "(normally two: one on the financial statements, one on internal "
            "control over financial reporting)",
        ]
        if audit.signatures:
            verified.append(f"Signed by: {'; '.join(audit.signatures)}")
        if audit.report_dates:
            verified.append(f"Report date(s): {', '.join(audit.report_dates)}")
        tenure = audit.tenure_note(facts.fiscal_year)
        if tenure:
            verified.append(f"Auditor tenure: {tenure}")
        # The cover-page flag is tagged as a checkbox glyph rather than a
        # boolean. Passing "☒" through would be ambiguous, so translate it.
        icfr_flag = facts.first("IcfrAuditorAttestationFlag")
        if icfr_flag:
            checked = icfr_flag.strip() in {"☒", "x", "X", "true", "TRUE", "Yes"}
            verified.append(
                "ICFR auditor attestation (cover page checkbox): "
                + ("yes — attestation provided" if checked else f"no ({icfr_flag})")
            )
        if sector:
            # Analyst-supplied, not read from the filing. A 10-K states no GICS
            # sector, and the choice moves the DSO benchmark band enough to flip
            # the finding — so it is pinned here and labelled as an input rather
            # than left to be inferred differently on each run.
            verified.append(
                f"Sector for benchmark comparison (analyst-supplied, not from "
                f"the filing): {sector}"
            )
        parts.append("\n".join(verified))

    for bundle in bundles:
        if bundle.current is None:
            continue
        parts.append(
            f"=== CURRENT YEAR SECTION: {bundle.spec.title} ===\n"
            f"(The heading appears {bundle.current.heading_count} time(s).)\n\n"
            f"{bundle.current.text}"
        )

    parts.append(
        "=== FULL FILING TEXT — CURRENT YEAR (for cross-reference) ===\n"
        + _elide_extracted(filing.document_text(), bundles)
    )

    if prior_filing is not None:
        prior_header = [
            _filing_header(prior_filing, "PRIOR YEAR FILING (for comparison only)")
        ]
        prior_audit_bundle = next(
            (b for b in bundles if b.spec.key == "audit_report"), None
        )
        if prior_audit_bundle is not None and prior_audit_bundle.prior is not None:
            prior_audit = section_facts(prior_audit_bundle.prior)
            prior_header.append(
                f"Auditor's reports present: {prior_audit.report_count}"
            )
            if prior_audit.signatures:
                prior_header.append(f"Signed by: {'; '.join(prior_audit.signatures)}")
            if prior_audit.report_dates:
                prior_header.append(
                    f"Report date(s): {', '.join(prior_audit.report_dates)}"
                )
            prior_tenure = prior_audit.tenure_note(prior_filing.fiscal_year)
            if prior_tenure:
                prior_header.append(f"Auditor tenure: {prior_tenure}")
        parts.append("\n".join(prior_header))

        for bundle in bundles:
            if bundle.prior is None:
                continue
            parts.append(
                f"=== PRIOR YEAR SECTION: {bundle.spec.title} "
                f"(FY{prior_filing.fiscal_year}) ===\n"
                f"(The heading appears {bundle.prior.heading_count} time(s).)\n\n"
                f"{bundle.prior.text}"
            )

    return "\n\n".join(parts)


# -------------------------------------------------------------------- runner


def render_digest(results: list[QuestionResult]) -> str:
    """The prior answers, formatted for a summary question to work from."""
    lines = ["=== PREVIOUS ANSWERS ON THE AUDIT REPORT ==="]
    for result in results:
        if not result.ok or result.question.kind is QuestionKind.SUMMARY:
            continue
        lines.append(f"\n{result.question.display_id}. {result.question.topic}")
        lines.append(f"Answer: {result.answer}")
        if result.concern:
            lines.append(f"Concern: {result.concern}")
        if result.has_level:
            lines.append(f"Level of concern: {result.concern_level.value}")
    return "\n".join(lines)


def run(
    workspace: Workspace,
    question_set: QuestionSet,
    *,
    claude: LLMClient | None = None,
    llm: LLMClient | None = None,
    workers: int = 4,
    scope_hint: str | None = None,
    on_result: Callable[[QuestionResult], None] | None = None,
) -> AnalysisRun:
    """Run every question in one set against the shared workspace.

    `workers` controls parallelism. The very first question of the whole run
    goes alone: a cache entry only becomes readable once the first response
    starts streaming, so firing everything at once would have every request
    miss the cache and pay full price for the filing. Warm it, then fan out —
    and because the workspace is shared, the second question set inherits the
    warm cache and never pays that cost again.
    """
    client: LLMClient = llm or claude or create_client()
    started = time.monotonic()

    filing = workspace.filing
    context = workspace.context
    normalized_context = workspace.normalized_context

    bundle = workspace.bundle(question_set.section_key)
    section = bundle.current if bundle else None
    scope_title = bundle.spec.title if bundle else None

    run_result = AnalysisRun(
        filing=filing,
        question_set=question_set,
        section=section,
        prior_filing=workspace.prior_filing,
        model=client.model,
        started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    def scoped(text: str) -> str:
        """Prefix a question with the section it concerns.

        Lives in the varying block, not the cached prefix — it differs per
        question set, and putting it in the prefix would split the cache in two.
        """
        if not scope_title:
            return text
        if scope_hint:
            # Several question sets can share one section — income statement,
            # balance sheet and footnote questions all read Item 8. Naming the
            # part each set is about stops three sets receiving identical
            # guidance about a 133,000-character span.
            return (
                f"[Scope: {scope_hint}. Answer from the {scope_title} section "
                f"of the CURRENT year filing, concentrating on the "
                f"{scope_hint} within it.]\n\n{text}"
            )
        return (
            f"[Scope: this question concerns the {scope_title} section of the "
            f"CURRENT year filing.]\n\n{text}"
        )

    def ask_one(question: Question) -> QuestionResult:
        started_at = time.monotonic()
        try:
            answer: Answer = client.ask(
                scoped(question.text),
                document=context,
                system=SYSTEM_PROMPT,
                schema=RESULT_SCHEMA,
            )
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            return QuestionResult(
                question=question,
                answer="",
                concern="",
                elapsed_seconds=time.monotonic() - started_at,
                error=f"{type(exc).__name__}: {exc}",
            )

        data = answer.data or {}
        evidence = [str(q) for q in data.get("evidence", []) if str(q).strip()]
        return QuestionResult(
            question=question,
            title=str(data.get("title", "")).strip()[:80],
            answer=str(data.get("answer", "")).strip(),
            concern=str(data.get("concern", "")).strip(),
            concern_level=_parse_level(data.get("concern_level")),
            evidence=evidence,
            unverified=verify_evidence(evidence, normalized_context),
            usage=answer.usage,
            has_level=True,
            elapsed_seconds=time.monotonic() - started_at,
        )

    def ask_summary(question: Question, prior: list[QuestionResult]) -> QuestionResult:
        """Run a summary question against the answers already produced.

        The digest goes in the varying block rather than the cached prefix —
        it changes every run, and putting it in the prefix would invalidate the
        cache for every other question.

        Character limits are enforced here because the API cannot express one:
        structured outputs support no `maxLength` constraint, so the only way to
        hold a hard budget is to measure the result and ask again.
        """
        started_at = time.monotonic()
        prompt = scoped(f"{question.text}\n\n{render_digest(prior)}")
        # Three attempts, not two. The model aims just under a stated budget and
        # sometimes overshoots by a few percent — one retry left a 350-character
        # summary at 370. Each retry also asks for a stricter target than the
        # hard limit, so "just under" lands inside it rather than on it.
        attempts = 3 if question.max_chars else 1
        answer = None
        summary = ""
        #: The shortest attempt seen. If every attempt overshoots, report the
        #: closest one rather than whichever happened to come last.
        best = ""

        for attempt in range(attempts):
            try:
                answer = client.ask(
                    prompt,
                    document=context,
                    system=SYSTEM_PROMPT,
                    schema=SUMMARY_SCHEMA,
                )
            except Exception as exc:  # noqa: BLE001 - recorded, not raised
                return QuestionResult(
                    question=question,
                    answer="",
                    concern="",
                        elapsed_seconds=time.monotonic() - started_at,
                    error=f"{type(exc).__name__}: {exc}",
                )
            summary = str((answer.data or {}).get("summary", "")).strip()
            if not best or len(summary) < len(best):
                best = summary
            if not question.max_chars or len(summary) <= question.max_chars:
                break
            # 85%, not 90%: the model aims at whatever number it is given and
            # lands just under it. A 90% target produced 349 characters against
            # a 350 limit — a pass with one character of margin.
            target = int(question.max_chars * 0.85)
            prompt = scoped(
                f"{question.text}\n\n{render_digest(prior)}\n\n"
                f"A previous attempt ran to {len(summary)} characters, over the "
                f"{question.max_chars}-character hard limit. Rewrite it to at "
                f"most {target} characters — aim comfortably below the limit "
                "rather than right at it — while keeping the material findings. "
                "Drop the least material detail first."
            )

        summary = best if question.max_chars and len(best) < len(summary) else summary
        over = bool(question.max_chars and len(summary) > question.max_chars)
        return QuestionResult(
            question=question,
            answer=summary,
            concern="",
            usage=answer.usage if answer else None,
            has_level=False,
            attempts=attempt + 1,
            elapsed_seconds=time.monotonic() - started_at,
            error=(
                f"summary is {len(summary)} characters, over the "
                f"{question.max_chars}-character limit"
                if over else None
            ),
        )

    def ask_task(question: Question) -> QuestionResult:
        """Run a table task, returning structured data instead of prose."""
        spec = TASK_SPECS.get(question.task_slug or "")
        if spec is None:
            # An unregistered task still runs, as an ordinary question. Better a
            # prose answer than a silently skipped block.
            return ask_one(question)

        started_at = time.monotonic()
        try:
            answer = client.ask(
                scoped(question.text),
                document=context,
                system=SYSTEM_PROMPT,
                schema=spec.schema,
                # Each task has its own schema and appears once per run, so its
                # prefix is never reused. Caching it wrote a full ~247k-token
                # entry per task that nothing ever read — at the 1h TTL's 2x
                # write rate that cost double a plain uncached request. The
                # ordinary questions and summaries still cache: they share one
                # schema across dozens of calls.
                cache=False,
            )
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            return QuestionResult(
                question=question, answer="", concern="",
                has_level=False,
                elapsed_seconds=time.monotonic() - started_at,
                error=f"{type(exc).__name__}: {exc}",
            )

        payload = answer.data or {}
        evidence = [str(q) for q in payload.get("evidence", []) if str(q).strip()]
        rating = payload.get(spec.rating_field) if spec.rating_field else None
        assessment = (str(payload.get(spec.assessment_field, "")).strip()
                      if spec.assessment_field else "")

        return QuestionResult(
            question=question,
            answer=str(payload.get("summary", "")).strip(),
            concern=assessment,
            concern_level=_parse_level(rating),
            has_level=rating is not None,
            data=payload,
            evidence=evidence,
            unverified=verify_evidence(evidence, normalized_context),
            usage=answer.usage,
            elapsed_seconds=time.monotonic() - started_at,
        )

    def dispatch(question: Question) -> QuestionResult:
        return (ask_task(question) if question.kind is QuestionKind.TABLE
                else ask_one(question))

    # Summary questions run last: they digest the answers to everything else.
    questions = [q for q in question_set.questions
                 if q.kind is not QuestionKind.SUMMARY]
    summary_questions = [
        q for q in question_set.questions if q.kind is QuestionKind.SUMMARY
    ]
    results: dict[int, QuestionResult] = {}
    start_index = 0

    # The first question of the whole run goes alone, to write the cache. Later
    # question sets share the workspace and so inherit a warm cache.
    if questions and not workspace.cache_warm:
        first = dispatch(questions[0])
        results[0] = first
        workspace.cache_warm = True
        start_index = 1
        if on_result:
            on_result(first)

    remaining = list(enumerate(questions[start_index:], start=start_index))
    if remaining:
        if workers <= 1:
            for index, question in remaining:
                result = dispatch(question)
                results[index] = result
                if on_result:
                    on_result(result)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(dispatch, question): index
                    for index, question in remaining
                }
                for future in concurrent.futures.as_completed(futures):
                    index = futures[future]
                    result = future.result()
                    results[index] = result
                    if on_result:
                        on_result(result)

    # Restore the user's question order — parallel completion is out of order,
    # and a report whose questions jump around is unreadable.
    ordered = [results[i] for i in sorted(results)]

    for question in summary_questions:
        result = ask_summary(question, ordered)
        ordered.append(result)
        if on_result:
            on_result(result)

    run_result.results = ordered
    run_result.elapsed_seconds = time.monotonic() - started
    return run_result
