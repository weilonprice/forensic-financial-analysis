"""Reading inline XBRL (iXBRL) documents.

An SEC 10-K filed since 2019 is a single XHTML file that is simultaneously two
documents: the human-readable annual report, and a machine-readable XBRL
instance. Every tagged figure appears once, wrapped in an `<ix:nonFraction>`
element carrying its concept name, period context, unit, scale, and sign.

This module provides the primitives for reading that file:

  * `parse`        — load the document into an element tree
  * `entity_facts` — pull the DEI cover-page facts (who filed, what, when)
  * `to_text`      — render the human-readable report as plain text

It deliberately does NOT extract the financial facts. There are ~1,600 tagged
numbers in a typical 10-K, each meaningless without its context (which period?
which segment? which reporting scenario?), and resolving contexts correctly is
a larger job than reading the document. That is its own module, later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator

from lxml import etree

#: Namespaces. `ix:` wraps tagged facts; `dei:` is the Document & Entity
#: Information taxonomy that carries cover-page identity.
IX_NS = "http://www.xbrl.org/2013/inlineXBRL"
IX_HEADER = f"{{{IX_NS}}}header"
IX_NON_NUMERIC = f"{{{IX_NS}}}nonNumeric"
IX_NON_FRACTION = f"{{{IX_NS}}}nonFraction"

#: Tags whose content is markup or styling, never readable text.
_DROP_TAGS = {"script", "style", "head"}

#: Tags that end a line of readable text.
_BLOCK_TAGS = {
    "p", "div", "br", "li", "tr", "table", "section", "article",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "ul", "ol",
}

#: Cells holding only a currency or percent symbol. SEC tables put the "$" in
#: its own column, so a naive render produces "$ | 198,084" instead of
#: "$198,084" — which reads badly and invites the model to mis-associate a
#: figure with the wrong column.
_PREFIX_ONLY = {"$", "€", "£", "¥"}
_SUFFIX_ONLY = {"%"}


def _localname(tag: object) -> str:
    """Strip the namespace from an element tag. Returns '' for comments."""
    if not isinstance(tag, str):
        return ""
    return etree.QName(tag).localname.lower()


def _clean(text: str | None) -> str:
    """Normalize whitespace, including the non-breaking spaces filings are
    full of. Left un-normalized, `\\xa0` survives into the text we send to
    Claude and into every string comparison we make against it."""
    if not text:
        return ""
    return re.sub(r"[\s ]+", " ", text).strip()


# --------------------------------------------------------------------- parsing


def parse(path: str | Path) -> etree._Element:
    """Parse an iXBRL document and return its root element.

    Uses the XML parser rather than the HTML one: SEC inline XBRL is required
    to be well-formed XHTML, and the XML parser preserves namespaces, which is
    what makes `ix:` and `dei:` elements addressable. `recover=True` tolerates
    the occasional malformed entity; `huge_tree=True` lifts libxml2's default
    node limit, which a multi-megabyte filing exceeds.
    """
    parser = etree.XMLParser(recover=True, huge_tree=True)
    tree = etree.parse(str(path), parser)
    root = tree.getroot()
    if root is None:
        raise ValueError(f"could not parse {path} as XML/XHTML")
    return root


# ----------------------------------------------------------------- fact values


def parse_number(element: etree._Element) -> Decimal | None:
    """Read an `<ix:nonFraction>` element as an exact number.

    Three attributes change the value and are easy to miss. Getting any of them
    wrong is a silent, order-of-magnitude error in a financial statement:

      scale  — power of ten to multiply by. A cover page showing "1.9" with
               scale="12" means 1,900,000,000,000. The displayed text is not
               the value.
      sign   — "-" means negate. Filings show negatives as "(127)" for display
               while tagging the sign separately.
      format — a display transform (comma grouping, parentheses). We strip the
               formatting characters rather than implement every transform.

    Decimal, not float: these are exact monetary quantities, and binary
    floating point cannot represent them exactly.
    """
    raw = _clean("".join(element.itertext()))
    if not raw:
        return None

    # Strip display formatting: thousands separators, currency, and the
    # accounting convention of parentheses for negatives.
    negative_by_parens = raw.startswith("(") and raw.endswith(")")
    cleaned = raw.strip("()").replace(",", "").replace("$", "").strip()
    if not cleaned or cleaned in {"-", "—", "–"}:
        return None

    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None

    scale = element.get("scale")
    if scale:
        try:
            value *= Decimal(10) ** int(scale)
        except (ValueError, InvalidOperation):
            pass

    if element.get("sign") == "-" or negative_by_parens:
        value = -value

    return value


def _parse_date(raw: str) -> date | None:
    """Parse a DEI date.

    iXBRL declares the display format in a `format` attribute (e.g.
    `ixt:date-monthday-year-en`) and there are dozens of registered transforms.
    Rather than implement the registry, we try the handful of shapes the SEC
    actually emits. Returns None instead of guessing when none match.
    """
    text = _clean(raw)
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%B%d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------- entity facts


@dataclass(frozen=True)
class EntityFacts:
    """Cover-page identity, read from the filing's own DEI tags.

    Read from the tags rather than inferred from filenames: the filename
    prefix is a filer convention (`goog-`), while `EntityRegistrantName` is a
    reported fact the filer is accountable for. When the two disagree, the tag
    is right.
    """

    #: Every DEI value found, keyed by tag name without the `dei:` prefix.
    #: Some tags legitimately repeat — Alphabet reports
    #: `EntityCommonStockSharesOutstanding` three times, once per share class —
    #: so values are always lists and callers decide how to combine them.
    raw: dict[str, list[str]]

    #: Numeric DEI values, parsed with scale and sign applied. Kept separate
    #: from `raw` because those attributes live on the element and are lost the
    #: moment a fact is reduced to its display text.
    numbers: dict[str, list[Decimal]] = field(default_factory=dict)

    def first(self, name: str) -> str | None:
        values = self.raw.get(name)
        return values[0] if values else None

    def all(self, name: str) -> list[str]:
        return list(self.raw.get(name, []))

    # -- typed accessors for the fields we care about --------------------

    @property
    def company_name(self) -> str | None:
        return self.first("EntityRegistrantName")

    @property
    def cik(self) -> str | None:
        """Zero-padded to the canonical 10 digits."""
        value = self.first("EntityCentralIndexKey")
        return value.zfill(10) if value else None

    @property
    def tickers(self) -> list[str]:
        """Plural: dual-class issuers list one symbol per class (GOOGL, GOOG)."""
        return self.all("TradingSymbol")

    @property
    def exchanges(self) -> list[str]:
        return self.all("SecurityExchangeName")

    @property
    def document_type(self) -> str | None:
        return self.first("DocumentType")

    @property
    def fiscal_year(self) -> int | None:
        value = self.first("DocumentFiscalYearFocus")
        return int(value) if value and value.isdigit() else None

    @property
    def fiscal_period(self) -> str | None:
        return self.first("DocumentFiscalPeriodFocus")

    @property
    def period_end(self) -> date | None:
        value = self.first("DocumentPeriodEndDate")
        return _parse_date(value) if value else None

    @property
    def state_of_incorporation(self) -> str | None:
        return self.first("EntityIncorporationStateCountryCode")

    @property
    def filer_category(self) -> str | None:
        return self.first("EntityFilerCategory")

    @property
    def auditor(self) -> tuple[str | None, str | None, str | None]:
        """(name, PCAOB firm id, location). The auditor and any change of
        auditor is a standing forensic signal, so it is surfaced up front."""
        return (
            self.first("AuditorName"),
            self.first("AuditorFirmId"),
            self.first("AuditorLocation"),
        )

    @property
    def is_amendment(self) -> bool:
        return (self.first("AmendmentFlag") or "").strip().upper() == "TRUE"

    @property
    def shares_outstanding(self) -> list[Decimal]:
        """One entry per share class, in document order."""
        return [d for d in self._numeric("EntityCommonStockSharesOutstanding")]

    @property
    def public_float(self) -> Decimal | None:
        values = self._numeric("EntityPublicFloat")
        return values[0] if values else None

    def _numeric(self, name: str) -> list[Decimal]:
        return list(self.numbers.get(name, []))


def entity_facts(root: etree._Element) -> EntityFacts:
    """Extract every `dei:` fact from an iXBRL document.

    DEI facts appear in two places: the hidden `<ix:header>` block at the top,
    and inline in the visible cover page. We scan the whole document so both
    are captured.
    """
    text_values: dict[str, list[str]] = {}
    numbers: dict[str, list[Decimal]] = {}

    for element in root.iter():
        tag = element.tag
        if tag not in (IX_NON_NUMERIC, IX_NON_FRACTION):
            continue
        name = element.get("name", "")
        if not name.startswith("dei:"):
            continue

        key = name[len("dei:"):]
        text_values.setdefault(key, []).append(_clean("".join(element.itertext())))

        if tag == IX_NON_FRACTION:
            value = parse_number(element)
            if value is not None:
                numbers.setdefault(key, []).append(value)

    return EntityFacts(raw=text_values, numbers=numbers)


def count_facts(root: etree._Element) -> tuple[int, int]:
    """(numeric, non-numeric) tagged fact counts across the whole document.

    A rough measure of how thoroughly the filing is tagged, and a preview of
    how much the fact-extraction module will have to work with.
    """
    numeric = non_numeric = 0
    for element in root.iter():
        if element.tag == IX_NON_FRACTION:
            numeric += 1
        elif element.tag == IX_NON_NUMERIC:
            non_numeric += 1
    return numeric, non_numeric


# ------------------------------------------------------------ text extraction


def to_text(root: etree._Element) -> str:
    """Render the human-readable report as plain text.

    Two things make this more than `element.text_content()`:

    1. The `<ix:header>` block holds hundreds of hidden facts with no readable
       meaning. Left in, it prepends thousands of tokens of noise to every
       question we ask.

    2. Financial statements are HTML tables. Flattened naively they become an
       unreadable run of digits with no row or column structure — exactly the
       content a forensic analysis depends on reading correctly. Rows are
       emitted one per line with cells pipe-separated.

    The tree is mutated (the header is removed), so parse a fresh copy if you
    need the facts afterwards — or call `entity_facts` first.
    """
    for header in root.findall(f".//{IX_HEADER}"):
        parent = header.getparent()
        if parent is not None:
            parent.remove(header)

    chunks: list[str] = []
    _render(root, chunks)

    text = "".join(c if c == "\n" else c + " " for c in chunks if c)
    text = re.sub(r"[ \t]*\n[ \t\n]*", "\n", text)   # tidy line boundaries
    text = _strip_page_furniture(text)
    text = re.sub(r"\n{3,}", "\n\n", text)            # cap blank runs
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


#: Running page furniture: a bare page number on its own line, and the running
#: header. In this filing there are 97 of each — one pair per page.
_PAGE_FURNITURE = re.compile(r"^(?:\d{1,3}\.|Table of Contents\b.*)$")


def _strip_page_furniture(text: str) -> str:
    """Remove page numbers and running headers.

    These are not merely noise between paragraphs — they land *inside*
    sentences. A page break falling mid-sentence produces, in the extracted
    text:

        We recognized a charge of
        76.
        Table of Contents | Alphabet Inc.
        $ 3.5 billion in the third quarter of 2025

    Any quotation of that sentence then fails verification, because the source
    has a page header wedged into the middle of it — the model reads the
    sentence correctly and gets reported as citing text that "doesn't exist".
    Removing the furniture rejoins the sentence.

    A standalone "76." line is a page number; real numbered content in a filing
    ("16. Subsequent Event") carries text on the same line.
    """
    return "\n".join(
        line for line in text.split("\n")
        if not _PAGE_FURNITURE.match(line.strip())
    )


def _render(element: etree._Element, out: list[str]) -> None:
    tag = _localname(element.tag)

    if tag in _DROP_TAGS:
        return

    if tag == "table":
        _render_table(element, out)
        return

    if element.text:
        out.append(_clean(element.text))

    for child in element:
        _render(child, out)
        if child.tail:
            out.append(_clean(child.tail))

    if tag in _BLOCK_TAGS:
        out.append("\n")


def _render_table(table: etree._Element, out: list[str]) -> None:
    out.append("\n")
    for row in _rows(table):
        cells = _row_cells(row)
        if cells:
            out.append(" | ".join(cells))
            out.append("\n")
    out.append("\n")


def _rows(node: etree._Element) -> Iterator[etree._Element]:
    """Yield this table's own `<tr>` elements, not those of nested tables.

    SEC filings nest tables for layout. A plain `.iter('tr')` would emit a
    nested table's rows twice — once as part of the parent cell's text, and
    again as standalone rows — duplicating figures in the output.
    """
    for child in node:
        tag = _localname(child.tag)
        if tag == "table":
            continue  # captured as text inside its containing cell
        if tag == "tr":
            yield child
        else:
            yield from _rows(child)


def _row_cells(row: etree._Element) -> list[str]:
    """Cell text for one row, with lone currency symbols folded into the
    adjacent figure so a column reads `$402,836` rather than `$ | 402,836`."""
    raw = [
        _clean("".join(cell.itertext()))
        for cell in row
        if _localname(cell.tag) in {"td", "th"}
    ]

    merged: list[str] = []
    pending_prefix = ""
    for value in raw:
        if not value:
            continue
        if value in _PREFIX_ONLY:
            pending_prefix = value
            continue
        if value in _SUFFIX_ONLY and merged:
            merged[-1] += value
            continue
        merged.append(pending_prefix + value)
        pending_prefix = ""

    if pending_prefix:
        merged.append(pending_prefix)
    return merged
