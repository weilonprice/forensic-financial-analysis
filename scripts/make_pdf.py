#!/usr/bin/env python3
"""Regenerate a PDF from a saved analysis JSON — no API calls.

    python scripts/make_pdf.py                       # newest run in output/
    python scripts/make_pdf.py output/foo.json       # a specific run
    python scripts/make_pdf.py --evidence            # include every quotation

Exists because layout changes shouldn't cost a re-run: the JSON holds
everything the report needs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forensic.report_pdf import build_pdf

OUTPUT = Path(__file__).resolve().parent.parent / "output"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", nargs="?", type=Path, default=None)
    parser.add_argument("--evidence", action="store_true",
                        help="include every supporting quotation")
    parser.add_argument("-o", "--out", type=Path, default=None)
    args = parser.parse_args()

    path = args.json_path
    if path is None:
        candidates = sorted(OUTPUT.glob("*analysis*.json"),
                            key=lambda p: p.stat().st_mtime)
        if not candidates:
            print(f"error: no analysis JSON found in {OUTPUT}")
            return 1
        path = candidates[-1]

    report = json.loads(Path(path).read_text())
    out = args.out or Path(path).with_suffix(".pdf")
    build_pdf(report, out, include_evidence=args.evidence)

    sets = report.get("sets", [])
    print(f"Source : {path}")
    print(f"Filing : {report.get('filing',{}).get('company')} "
          f"FY{report.get('filing',{}).get('fiscal_year')}")
    print(f"Sets   : {', '.join(s['name'] for s in sets)}")
    print(f"Wrote  : {out}  ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
