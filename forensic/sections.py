"""Locating named sections inside a filing's extracted text.

A question set targets one part of the 10-K. We still send Claude the whole
filing — the audit report's Critical Audit Matter points at Note 10, and a
question about that CAM cannot be answered without it — but we also pull the
target section out and put it in front, so the model is anchored on the right
text rather than hunting for it across 350,000 characters.

Both go inside the cached prefix, so the duplication costs nothing after the
first question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SectionSpec:
    """How to find one section."""

    key: str
    title: str
    #: Matches the section's heading. May match more than once — the audit
    #: report is two consecutive reports under the same heading.
    start: re.Pattern[str]
    #: Matches whatever comes next. Searched only *after* the last start match,
    #: so a section that repeats its heading is captured whole.
    end: re.Pattern[str]


@dataclass(frozen=True)
class Section:
    spec: SectionSpec
    text: str
    start_offset: int
    end_offset: int
    #: How many times the heading appeared. For the audit report, 2 is normal
    #: (financial statements, then internal control over financial reporting);
    #: 1 means the ICFR opinion is missing, which is itself worth noticing.
    heading_count: int

    @property
    def length(self) -> int:
        return len(self.text)


#: The auditor's report(s), ending where the financial statements begin.
#:
#: The end pattern is deliberately case-SENSITIVE. "consolidated balance
#: sheets" appears in the audit report's own opinion paragraph in lower case;
#: only the statement heading is upper case. A case-insensitive match would
#: truncate the section inside its first paragraph.
AUDIT_REPORT = SectionSpec(
    key="audit_report",
    title="Report of Independent Registered Public Accounting Firm",
    start=re.compile(
        r"^\s*REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM\s*$",
        re.MULTILINE,
    ),
    end=re.compile(r"^\s*CONSOLIDATED BALANCE SHEETS?\s*$", re.MULTILINE),
)

#: Item 7, Management's Discussion and Analysis, ending where Item 7A begins.
#:
#: Both patterns are case-SENSITIVE on the item words. A 10-K's table of
#: contents lists "Item 7." and "Item 7A." too, and a case-insensitive match
#: would start the section at the table of contents — capturing a page-number
#: list instead of the discussion. Only the statement headings are upper case.
MDA = SectionSpec(
    key="mda",
    title="Management's Discussion and Analysis of Financial Condition and "
          "Results of Operations",
    start=re.compile(r"^\s*ITEM\s*7\.?\s*MANAGEMENT[^\n]{0,110}$", re.MULTILINE),
    end=re.compile(r"^\s*ITEM\s*7A\.?\s*QUANTITATIVE[^\n]{0,110}$", re.MULTILINE),
)

#: Item 8 — the financial statements themselves plus every note.
#:
#: Scoped to all of Item 8 rather than any single statement. Income statement
#: questions ask about revenue recognition policy, segments and depreciation;
#: balance sheet and cash flow questions ask about the same notes from another
#: angle. None of that lives in the statement tables — it is all in the notes,
#: which are 86% of Item 8. One span serves every financial-statement question
#: set, and costs nothing extra because it is loaded once.
#:
#: Case-sensitive on the item words, same table-of-contents hazard as MD&A.
FINANCIAL_STATEMENTS = SectionSpec(
    key="financial_statements",
    title="Financial Statements and Supplementary Data (Item 8)",
    start=re.compile(r"^\s*ITEM\s*8\.?\s*FINANCIAL STATEMENTS[^\n]{0,110}$",
                     re.MULTILINE),
    end=re.compile(r"^\s*ITEM\s*9\.?\s*CHANGES IN[^\n]{0,110}$", re.MULTILINE),
)

#: The notes alone, from their heading to the end of Item 8 — 113,778 chars in
#: FY2025, 107,982 in FY2024, one clean match per filing.
#:
#: Defined but NOT in the default `SECTION_SPECS`. Adding it pins a third copy
#: of the notes in front (they are already inside Item 8 and inside the full
#: filing text), costing roughly 55k tokens per run for a tighter anchor on a
#: section that is 86% of what Item 8 already points at. Enable it in
#: `run_analysis.SECTION_SPECS` if footnote answers turn out to need the
#: sharper focus; the mapping in `questions._SECTION_HINTS` must move with it.
NOTES = SectionSpec(
    key="notes",
    title="Notes to Consolidated Financial Statements",
    start=re.compile(r"^\s*NOTES? TO CONSOLIDATED FINANCIAL STATEMENTS\s*$",
                     re.MULTILINE),
    end=re.compile(r"^\s*ITEM\s*9\.?\s*CHANGES IN[^\n]{0,110}$", re.MULTILINE),
)

REGISTRY: dict[str, SectionSpec] = {
    AUDIT_REPORT.key: AUDIT_REPORT,
    MDA.key: MDA,
    FINANCIAL_STATEMENTS.key: FINANCIAL_STATEMENTS,
    NOTES.key: NOTES,
}


# ------------------------------------------------- mechanically-derived facts

_AUDITOR_SINCE = re.compile(
    r"served as the Compan(?:y|y's|y’s)[^.]*?auditor since (\d{4})", re.IGNORECASE
)
_SIGNATURE = re.compile(r"/s/\s*([^\n]+)")

_DATE = (
    r"(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}"
)

#: The report date is the one in the signature block, not every date the report
#: mentions. An audit report names the balance sheet dates it covers in its
#: opening paragraph, so a document-wide date scan returns "December 31, 2024"
#: and "December 31, 2025" alongside the real answer — and a shared facts block
#: that asserts three report dates is worse than none at all.
_SIGNED_DATE = re.compile(rf"/s/[^\n]*\n(?:[^\n]*\n){{0,3}}?\s*({_DATE})")


@dataclass(frozen=True)
class AuditReportFacts:
    """Facts read straight out of the audit report by pattern, not by the model.

    These exist because twelve independent questions were each re-deriving them
    and disagreeing — one answer said the auditor had served 26 years while
    three others said 27. Anything a regex can settle should be settled once and
    handed to every question identically, so the report cannot contradict
    itself on plain matters of record.

    Only mechanical extraction belongs here. Conclusions — whether the opinion
    is clean, whether tenure is a problem — are what the questions are *for*,
    and pre-computing them would be answering the questions in the prompt.
    """

    report_count: int
    auditor_since: int | None
    signatures: list[str]
    report_dates: list[str]

    def tenure_note(self, fiscal_year: int | None) -> str | None:
        """State tenure unambiguously, both ways.

        "Auditor since 1999" for a FY2025 audit is 26 elapsed years but the
        27th consecutive annual audit. Both readings are defensible, which is
        exactly why the model produced both. Giving it the arithmetic removes
        the choice."""
        if self.auditor_since is None or fiscal_year is None:
            return None
        audits = fiscal_year - self.auditor_since + 1
        elapsed = fiscal_year - self.auditor_since
        return (
            f"engaged since {self.auditor_since}; the FY{fiscal_year} audit is "
            f"the {audits}th consecutive annual audit ({elapsed} years elapsed)"
        )


def audit_facts(section: "Section") -> AuditReportFacts:
    """Extract the audit report's matters of record."""
    text = section.text
    since = _AUDITOR_SINCE.search(text)
    return AuditReportFacts(
        report_count=section.heading_count,
        auditor_since=int(since.group(1)) if since else None,
        signatures=list(dict.fromkeys(
            " ".join(m.group(1).split()) for m in _SIGNATURE.finditer(text)
        )),
        report_dates=list(dict.fromkeys(m.group(1) for m in _SIGNED_DATE.finditer(text))),
    )


def find(text: str, spec: SectionSpec) -> Section | None:
    """Extract a section, or None if its heading never appears."""
    starts = [m.start() for m in spec.start.finditer(text)]
    if not starts:
        return None

    begin = starts[0]
    # Search for the end marker after the LAST heading occurrence. Searching
    # from the first would stop at the boundary between the two audit reports
    # if anything in between happened to match.
    end_match = spec.end.search(text, starts[-1])
    end = end_match.start() if end_match else len(text)

    return Section(
        spec=spec,
        text=text[begin:end].strip(),
        start_offset=begin,
        end_offset=end,
        heading_count=len(starts),
    )
