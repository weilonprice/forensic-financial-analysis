# Forensic Financial Statement Analysis

Runs a set of forensic accounting questions against a company's SEC 10-K and
produces a report where **every factual claim is backed by a quotation the tool
has mechanically verified against the filing**.

That verification is the point. The model is asked to supply verbatim
quotations supporting each figure it cites; the application then checks each
quotation appears character-for-character in the source text and marks any that
does not. A paraphrase, a reformatted number, or text stitched together from
two places is reported as unverified rather than presented as a finding.

It also compares the current filing against the prior year, which is where the
more interesting findings tend to come from — a disclosure that quietly
disappeared is not visible in either year's filing read alone.

## What it does

- Parses inline XBRL filings straight from an EDGAR download — no API calls,
  no scraping. Company identity comes from DEI tags rather than filenames.
- Locates the audit report, MD&A, and financial statements, and pins them in
  front of the full text.
- Asks each question in its own request, against one shared cached copy of the
  filing.
- Rates each finding on four anchored levels — `none`, `minor`, `material`,
  `severe` — and flags `material` and above.
- Writes a JSON record, a Markdown report, and a PDF.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY='...'
```

The key is read from the environment and is never written to disk or read from
a file in this repository.

## Adding a filing

Download the complete XBRL folder for a filing from
[SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch) and drop it in
whole:

```
Latest 10k/0001652044-26-000018-xbrl/
Previous Year 10k/0001652044-25-000014-xbrl/
```

Filings are not committed to this repository — they are large, public, and
specific to whichever company you are looking at.

## Running

Check the question files parse before spending anything. This is free:

```bash
python scripts/check_questions.py
```

Then:

```bash
python scripts/run_analysis.py                  # every question set
python scripts/run_analysis.py --dry-run        # resolve everything, no API calls
python scripts/run_analysis.py --set mda        # one set
python scripts/run_analysis.py --only 1,6,13    # specific questions
```

Reports are written to `output/`.

## Questions

Question sets live in `Analysis Questions/` as plain `.txt` files, one folder
per set. They are ordinary numbered questions — edit them, or add your own set,
and the loader will pick it up. `check_questions.py` reports what the
application will actually see, which is worth running after any edit: several
of this project's early failures were formatting problems in the question
files rather than bugs in the code.

## Cost

Roughly **$12 per company** for 70 questions against a filing the size of
Alphabet's, on `claude-opus-5`. The dominant cost is not output — it is
re-reading the cached filing once per question, which is about half the bill.
A smaller filer costs proportionally less; context size drives most of it.

`--dry-run` resolves the filing, sections and questions without making a single
API call, which is the cheapest way to confirm a new company is set up
correctly.

## Reproducibility

Concern levels are produced by a language model and are **not perfectly
reproducible**. On a 1–10 scale, repeated runs of an identical filing disagreed
on 54% of questions; collapsing those same runs into the current four levels
cuts that to 31%, and the residual disagreement sits almost entirely on the
`none`/`minor` boundary, where neither level is flagged.

`scripts/measure_variance.py` measures this. `--baseline` analyses run records
already on disk and costs nothing:

```bash
python scripts/measure_variance.py --baseline
python scripts/measure_variance.py --set audit --runs 5
```

Treat the flagged findings and their verified quotations as the output. Treat
the levels as a triage aid, not a measurement.

## Layout

```
forensic/
  ixbrl.py       inline XBRL parsing, fact extraction, text rendering
  filing.py      filing discovery and identity from DEI tags
  sections.py    locating the audit report, MD&A, financial statements
  questions.py   parsing question files
  analysis.py    schemas, prompt, runner, evidence verification
  research.py    parsing the 100-step research workbook format
  report_pdf.py  PDF generation
  claude.py      the Anthropic API wrapper (caching, streaming, structured output)
scripts/
  run_analysis.py       the main entry point
  check_questions.py    validate question files (free)
  check_research.py     validate the research workbook (free)
  measure_variance.py   measure run-to-run reproducibility
  inspect_filings.py    inspect a parsed filing
```

[alphabet-analysis-20260813-223159.pdf](https://github.com/user-attachments/files/32162088/alphabet-analysis-20260813-223159.pdf)


## Disclaimer

This is a research tool. It is not investment advice, it is not an audit, and
its output is not a substitute for professional judgment. Language models make
mistakes; the evidence verification catches fabricated quotations but cannot
tell you whether a correctly-quoted passage actually supports the conclusion
drawn from it. Check anything you intend to rely on.

## License

MIT — see [LICENSE](LICENSE).
