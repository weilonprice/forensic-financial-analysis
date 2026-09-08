"""Rendering an analysis run as a PDF.

Built from the JSON record rather than from live objects, so the same code
serves two purposes: writing the PDF at the end of a run, and regenerating one
from any saved run without re-querying the API. A report that can only be
produced at the moment of the run is a report you cannot re-issue after fixing
a typo in the layout.

Uses reportlab's platypus flowables and the built-in Helvetica family — no font
files to ship, no system libraries to install.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

INK = colors.HexColor("#1c2024")
MUTED = colors.HexColor("#6b7280")
RULE = colors.HexColor("#d5d8dc")
PANEL = colors.HexColor("#f5f6f8")
ACCENT = colors.HexColor("#1f3a5f")

#: Colour per concern level. Keyed by name rather than by a numeric threshold,
#: which removes the hazard the old inverted 1-10 scale carried: a band table
#: read the wrong way round would have painted the worst findings green, the one
#: visual error this document cannot afford. "severe" cannot be misread.
_LEVEL_COLOURS = {
    "none":     (colors.HexColor("#1a7f37"), colors.HexColor("#dafbe1")),
    "minor":    (colors.HexColor("#9a6700"), colors.HexColor("#fff8c5")),
    "material": (colors.HexColor("#bc4c00"), colors.HexColor("#ffe7d1")),
    "severe":   (colors.HexColor("#cf222e"), colors.HexColor("#ffe3e6")),
}

#: Worst first — the order findings are listed and counted in.
_LEVELS = ["severe", "material", "minor", "none"]

_LEVEL_LABELS = {"none": "No concern", "minor": "Minor",
                 "material": "Material", "severe": "Severe"}

#: Levels that put a question in the flagged list.
_FLAGGED = {"material", "severe"}

#: Characters that appear in filings but not in reportlab's WinAnsi encoding.
#: Left unmapped they render as black boxes, so translate the ones we see and
#: drop anything else outside the encoding.
_GLYPHS = {
    "☒": "[x]", "☐": "[ ]", "✓": "v", "≤": "<=", "≥": ">=",
    "⚠": "!", "→": "->", "•": "-", " ": " ",
}


#: Short labels for the cover's narrow left column.
_SECTION_LABELS = {
    "audit_report": "Audit report",
    "mda": "MD&A",
    "financial_statements": "Financial statements",
    "notes": "Notes",
}


def _hex(color: colors.Color) -> str:
    """reportlab's inline `<font color=...>` needs `#rrggbb`.

    `Color.hexval()` returns `0xrrggbb`, which the paragraph parser rejects —
    it tries to read it as a base-10 integer and raises.
    """
    return "#" + color.hexval()[2:]


def _band(level: str) -> tuple[colors.Color, colors.Color]:
    return _LEVEL_COLOURS.get(level, (MUTED, PANEL))


def _text(value: Any) -> str:
    """Make a string safe for a reportlab Paragraph.

    Two separate hazards: paragraphs are parsed as mini-XML so `&`, `<` and `>`
    must be escaped, and the built-in fonts cover only WinAnsi so exotic glyphs
    must be replaced or dropped.
    """
    text = "" if value is None else str(value)
    for bad, good in _GLYPHS.items():
        text = text.replace(bad, good)
    text = "".join(ch for ch in text if ch == "\n" or 32 <= ord(ch) < 0x2E80)
    return escape(" ".join(text.split()))


# ------------------------------------------------------------------- styles


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["BodyText"]
    make = lambda **kw: ParagraphStyle(**{"parent": base, **kw})  # noqa: E731
    return {
        "cover_kicker": make(
            name="ck", fontName="Helvetica", fontSize=10, textColor=MUTED,
            alignment=TA_CENTER, spaceAfter=6, leading=14,
        ),
        "cover_title": make(
            name="ct", fontName="Helvetica-Bold", fontSize=26, textColor=INK,
            alignment=TA_CENTER, leading=31, spaceAfter=4,
        ),
        "cover_sub": make(
            name="cs", fontName="Helvetica", fontSize=13, textColor=ACCENT,
            alignment=TA_CENTER, leading=18, spaceAfter=18,
        ),
        "h1": make(
            name="h1", fontName="Helvetica-Bold", fontSize=17, textColor=ACCENT,
            spaceBefore=4, spaceAfter=10, leading=21,
        ),
        "h2": make(
            name="h2", fontName="Helvetica-Bold", fontSize=12, textColor=INK,
            spaceBefore=14, spaceAfter=6, leading=15,
        ),
        "q": make(
            name="q", fontName="Helvetica-Bold", fontSize=10.5, textColor=ACCENT,
            spaceBefore=2, spaceAfter=4, leading=14,
        ),
        "body": make(
            name="b", fontName="Helvetica", fontSize=9.5, textColor=INK,
            leading=13.5, spaceAfter=5, alignment=TA_LEFT,
        ),
        "concern": make(
            name="cn", fontName="Helvetica-Oblique", fontSize=9.5,
            textColor=colors.HexColor("#3d4450"), leading=13.5,
            leftIndent=10, spaceAfter=5,
        ),
        "small": make(
            name="sm", fontName="Helvetica", fontSize=8, textColor=MUTED,
            leading=11, spaceAfter=3,
        ),
        "warn": make(
            name="w", fontName="Helvetica-Bold", fontSize=9, leading=12.5,
            textColor=colors.HexColor("#cf222e"), leftIndent=10, spaceAfter=4,
        ),
        "quote": make(
            name="qt", fontName="Helvetica", fontSize=7.6, textColor=MUTED,
            leading=10.2, leftIndent=12, spaceAfter=2,
        ),
    }


def _chrome(canvas, doc) -> None:
    """Running header and footer on every page but the cover."""
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)

    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN + 14, PAGE_WIDTH - MARGIN,
                PAGE_HEIGHT - MARGIN + 14)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 20,
                      getattr(doc, "running_title", ""))

    canvas.line(MARGIN, MARGIN - 12, PAGE_WIDTH - MARGIN, MARGIN - 12)
    canvas.drawString(MARGIN, MARGIN - 24, getattr(doc, "running_foot", ""))
    canvas.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 24,
                           f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# -------------------------------------------------------------------- blocks


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    table = Table(
        [[Paragraph(f"<b>{_text(k)}</b>", _styles()["small"]),
          Paragraph(_text(v), _styles()["small"])] for k, v in rows],
        colWidths=[1.55 * inch, CONTENT_WIDTH - 1.55 * inch],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _cover(report: dict, styles: dict) -> list:
    filing = report.get("filing", {})
    prior = report.get("prior_filing")
    sets = report.get("sets", [])
    flow: list = [Spacer(1, 1.5 * inch)]

    flow.append(Paragraph("FORENSIC FINANCIAL STATEMENT ANALYSIS",
                          styles["cover_kicker"]))
    flow.append(Paragraph(_text(filing.get("company") or "Unknown filer"),
                          styles["cover_title"]))
    flow.append(Paragraph(
        _text(f"{filing.get('document_type','?')} · Fiscal year "
              f"{filing.get('fiscal_year','?')} · Period ending "
              f"{filing.get('period_end','?')}"),
        styles["cover_sub"]))

    rows = [("CIK", filing.get("cik") or "—"),
            ("EDGAR accession", filing.get("accession") or "—")]
    if prior:
        rows.append(("Compared against",
                     f"FY{prior.get('fiscal_year','?')} "
                     f"(accession {prior.get('accession') or '—'})"))
    # Which sections a question set actually covered. A section can be loaded
    # into context without being analysed — running only the audit set still
    # puts the MD&A in front of the model for cross-reference — and a cover that
    # lists it unqualified reads as though it was analysed and then omitted.
    analysed = {block.get("section") for block in sets}
    for section in report.get("sections", []):
        # A short label in the narrow left column; the full title belongs in the
        # value, where there is room for it. Slicing the title instead cuts it
        # mid-word ("...Public Accounting F").
        label = _SECTION_LABELS.get(section.get("key", ""), "Section")
        detail = f"{_text(section.get('title',''))} — " \
                 f"{section.get('current_chars', 0):,} chars"
        if section.get("prior_chars"):
            detail += f", prior year {section['prior_chars']:,}"
        if section.get("key") not in analysed:
            detail += "  (loaded for cross-reference; not analysed in this report)"
        rows.append((label, detail))
    if filing.get("sector"):
        source = filing.get("sector_source") or ""
        rows.append(("Sector (benchmarks)",
                     f"{filing['sector']}"
                     + (f"  — {source}" if source else "")))
    if sets:
        rows.append(("Model", sets[0].get("model") or "—"))
        rows.append(("Analysis run", sets[0].get("started_at") or "—"))
    rows.append(("PDF generated", datetime.now().strftime("%Y-%m-%d %H:%M")))
    flow.append(_kv_table(rows))
    flow.append(Spacer(1, 22))

    # -- per-section scorecard -------------------------------------------
    head = ["Section", "Questions", "Severe", "Material", "Minor", "None",
            "Cited", "Unverified"]
    data = [[Paragraph(f"<b>{_text(h)}</b>", styles["small"]) for h in head]]
    total_cited = total_unverified = 0
    for block in sets:
        results = block.get("results", [])
        levels = [r["concern_level"] for r in results
                  if r.get("concern_level") is not None]
        cited = sum(len(r.get("evidence", [])) for r in results)
        unver = sum(len(r.get("unverified_evidence", [])) for r in results)
        total_cited += cited
        total_unverified += unver
        row = [
            Paragraph(_text(block.get("name", "")), styles["small"]),
            Paragraph(str(len(results)), styles["small"]),
        ]
        for level in _LEVELS:
            row.append(Paragraph(str(levels.count(level)), styles["small"]))
        row.append(Paragraph(str(cited), styles["small"]))
        row.append(Paragraph(str(unver), styles["small"]))
        data.append(row)

    # Eight columns now the mean/lowest pair became four level counts. Total
    # stays inside the 6.5" frame; the level columns are narrow because they
    # hold single digits.
    table = Table(data, colWidths=[1.85 * inch, 0.7 * inch, 0.55 * inch,
                                   0.62 * inch, 0.5 * inch, 0.5 * inch,
                                   0.5 * inch, 0.78 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 16))

    # -- evidence verification banner ------------------------------------
    if total_unverified:
        message = (f"{total_unverified} of {total_cited} cited quotations could "
                   "not be located in the filing. Answers carrying an unverified "
                   "citation are marked in the findings and should be checked by "
                   "hand before use.")
        ink, fill = colors.HexColor("#cf222e"), colors.HexColor("#ffe3e6")
    else:
        message = (f"All {total_cited} quotations cited across this analysis were "
                   "matched verbatim against the filing text.")
        ink, fill = colors.HexColor("#1a7f37"), colors.HexColor("#dafbe1")
    banner = Table([[Paragraph(
        f'<font color="{_hex(ink)}"><b>Evidence verification.</b> '
        f'{_text(message)}</font>', styles["small"])]],
        colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.5, ink),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    flow.append(banner)
    flow.append(Spacer(1, 14))

    legend = ("<b>Concern levels.</b> "
              "<b>None</b> present, complete, consistent with the prior year · "
              "<b>Minor</b> thinner or reworded, no evidence of a problem · "
              "<b>Material</b> an analyst would want it explained · "
              "<b>Severe</b> absent or contradicted. "
              "Material and above are flagged.")
    flow.append(Paragraph(legend, styles["small"]))
    return flow


def _score_chip(level: str, styles: dict) -> Table:
    ink, fill = _band(level)
    chip = Table([[Paragraph(
        f'<font color="{_hex(ink)}"><b>{_LEVEL_LABELS.get(level, level)}</b>'
        f'</font>', styles["small"])]], colWidths=[1.0 * inch])
    chip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.5, ink),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return chip


def _grid(header: list[str], rows: list[list[str]], styles: dict) -> Table:
    """A compact data table for a task result."""
    data = [[Paragraph(f"<b>{_text(h)}</b>", styles["small"]) for h in header]]
    data += [[Paragraph(_text(c), styles["small"]) for c in row] for row in rows]
    first = 2.05 * inch
    rest = (CONTENT_WIDTH - first) / max(1, len(header) - 1)
    table = Table(data, colWidths=[first] + [rest] * (len(header) - 1),
                  hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, RULE),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _task_flowables(result: dict, styles: dict) -> list:
    """Render a table task's structured payload."""
    from forensic import analysis
    data = result.get("data") or {}
    slug = result.get("task_slug")
    flow: list = []
    if slug == "dso_data_entry":
        header, rows = analysis.dso_table(data)
        flow.append(_grid(header, rows, styles))
    elif slug == "dso_analysis":
        pairs = analysis.dso_analysis_rows(data)
        flow.append(_grid(["", ""], [[k, v] for k, v in pairs], styles))
    if flow:
        flow.append(Spacer(1, 6))
    return flow


def _finding(result: dict, styles: dict, include_evidence: bool) -> list:
    flow: list = [Paragraph(
        f"{result.get('display_id') or result.get('number','?')}. "
        f"{_text(result.get('label') or result.get('topic',''))}",
        styles["q"])]

    if result.get("error") and not result.get("answer"):
        flow.append(Paragraph(f"Failed to run: {_text(result['error'])}",
                              styles["warn"]))
        return [KeepTogether(flow)]

    flow.append(Paragraph(_text(result.get("answer", "")), styles["body"]))
    if result.get("kind") == "table":
        flow.extend(_task_flowables(result, styles))
    if result.get("concern"):
        flow.append(Paragraph(f"<b>Concern.</b> {_text(result['concern'])}",
                              styles["concern"]))
    if result.get("concern_level") is not None:
        flow.append(_score_chip(result["concern_level"], styles))

    unverified = result.get("unverified_evidence") or []
    if unverified:
        flow.append(Spacer(1, 3))
        flow.append(Paragraph(
            f"{len(unverified)} cited quotation(s) could not be located in the "
            "filing:", styles["warn"]))
        for quote in unverified:
            flow.append(Paragraph(f"• {_text(quote)[:260]}", styles["quote"]))

    evidence = result.get("evidence") or []
    if include_evidence and evidence:
        flow.append(Spacer(1, 3))
        flow.append(Paragraph(f"Evidence ({len(evidence)} quotation(s)):",
                              styles["small"]))
        for quote in evidence:
            mark = "  [NOT FOUND]" if quote in unverified else ""
            flow.append(Paragraph(f"• {_text(quote)[:320]}{mark}",
                                  styles["quote"]))
    elif evidence:
        flow.append(Paragraph(
            f"{len(evidence)} supporting quotation(s), "
            f"{len(evidence) - len(unverified)} verified against the filing.",
            styles["small"]))

    flow.append(Spacer(1, 9))
    # Keep a finding whole where it fits on one page; a question split from its
    # concern level reads as though it has no conclusion.
    return [KeepTogether(flow)]


def _section(block: dict, styles: dict, include_evidence: bool) -> list:
    results = block.get("results", [])
    levels = [r["concern_level"] for r in results
              if r.get("concern_level") is not None]
    flow: list = [Paragraph(_text(block.get("name", "Questions")), styles["h1"])]

    meta = []
    if levels:
        spread = " · ".join(f"{levels.count(l)} {l}"
                            for l in _LEVELS if levels.count(l))
        meta.append(f"{len(levels)} rated questions — {spread}")
    if block.get("elapsed_seconds"):
        meta.append(f"completed in {block['elapsed_seconds']:.0f}s")
    if meta:
        flow.append(Paragraph(_text(" · ".join(meta)), styles["small"]))
        flow.append(Spacer(1, 8))

    # -- the section's own summary answer --------------------------------
    for result in results:
        if result.get("kind") != "summary":
            continue
        flow.append(Paragraph("Summary", styles["h2"]))
        panel = Table([[Paragraph(_text(result.get("answer", "")), styles["body"])]],
                      colWidths=[CONTENT_WIDTH], hAlign="LEFT")
        panel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 0.5, RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        flow.append(panel)
        limit = result.get("max_chars")
        note = f"{len(result.get('answer',''))} characters"
        if limit:
            note += (f" against a {limit}-character limit — "
                     f"{'OVER LIMIT' if result.get('error') else 'within limit'}")
        if result.get("attempts", 1) > 1:
            note += f" · {result['attempts']} attempts"
        flow.append(Spacer(1, 3))
        flow.append(Paragraph(_text(note), styles["small"]))

    # -- flagged ----------------------------------------------------------
    flagged = sorted(
        (r for r in results if r.get("concern_level") in _FLAGGED),
        key=lambda r: _LEVELS.index(r["concern_level"]),
    )
    flow.append(Paragraph("Flagged findings", styles["h2"]))
    if flagged:
        for result in flagged:
            flow.append(Paragraph(
                f"<b>{_LEVEL_LABELS[result['concern_level']]} — "
                f"{result.get('display_id') or result['number']}.</b> "
                f"{_text(result.get('label') or result.get('topic',''))} "
                f"{_text(result.get('concern',''))}",
                styles["body"]))
    else:
        flow.append(Paragraph(
            "No question in this section reached material concern.",
            styles["body"]))

    # -- concern table -----------------------------------------------------
    flow.append(Paragraph("All questions", styles["h2"]))
    data = [[Paragraph(f"<b>{h}</b>", styles["small"])
             for h in ("#", "Question", "Score")]]
    style_rows = [
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for index, result in enumerate(results, start=1):
        if result.get("kind") == "summary":
            label = "summary"
        elif result.get("concern_level") is not None:
            label = _LEVEL_LABELS[result["concern_level"]]
        elif result.get("kind") == "table":
            label = "table"
        else:
            label = "error"
        data.append([
            Paragraph(_text(result.get("display_id")
                                or result.get("number", "")), styles["small"]),
            Paragraph(_text(result.get("label")
                                or result.get("topic", ""))[:200], styles["small"]),
            Paragraph(label, styles["small"]),
        ])
        if result.get("concern_level") is not None:
            _, fill = _band(result["concern_level"])
            style_rows.append(("BACKGROUND", (2, index), (2, index), fill))
        style_rows.append(("LINEBELOW", (0, index), (-1, index), 0.25, RULE))

    # 0.75", not 0.4": identifiers now read "Task 1" as well as "7", and the
    # narrower column wrapped them to "Tas / k 1".
    table = Table(data, colWidths=[0.75 * inch, CONTENT_WIDTH - 1.7 * inch,
                                   0.95 * inch], hAlign="LEFT")
    table.setStyle(TableStyle(style_rows))
    flow.append(table)

    # -- findings ----------------------------------------------------------
    flow.append(Paragraph("Questions and answers", styles["h2"]))
    for result in results:
        if result.get("kind") == "summary":
            continue  # shown as the section summary above
        flow.extend(_finding(result, styles, include_evidence))

    return flow


# --------------------------------------------------------------------- entry


def build_pdf(report: dict, out_path: str | Path,
              *, include_evidence: bool = False) -> Path:
    """Render an analysis JSON record as a PDF."""
    out_path = Path(out_path)
    styles = _styles()
    filing = report.get("filing", {})

    doc = BaseDocTemplate(
        str(out_path), pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"Forensic Analysis — {filing.get('company','')}",
        author="Forensic Financial Statement Analysis",
    )
    doc.running_title = (
        f"{filing.get('company','')} · {filing.get('document_type','')} "
        f"FY{filing.get('fiscal_year','')} · Forensic Analysis"
    )
    doc.running_foot = (
        "Concern scale: 1 = very concerned, 10 = not concerned"
    )

    frame = Frame(MARGIN, MARGIN, CONTENT_WIDTH, PAGE_HEIGHT - 2 * MARGIN,
                  id="body")
    doc.addPageTemplates([
        # The cover carries no header or footer; every later page does.
        PageTemplate(id="cover", frames=[frame]),
        PageTemplate(id="body", frames=[frame], onPage=_chrome),
    ])

    flow: list = [NextPageTemplate("body")]
    flow.extend(_cover(report, styles))
    for block in report.get("sets", []):
        flow.append(PageBreak())
        flow.extend(_section(block, styles, include_evidence))

    doc.build(flow)
    return out_path
