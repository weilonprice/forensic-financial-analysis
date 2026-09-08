"""Finding and describing an uploaded SEC filing package.

The user drops an extracted EDGAR XBRL folder — `0001652044-26-000018-xbrl` —
into `Latest 10k/` or `Past 10k/`. This module turns that directory into a
`Filing`: who filed it, what period it covers, which of the files is the actual
annual report, and what every other file in the package is for.

Nothing here talks to Claude or parses financial figures. It answers three
questions: what did the user give us, whose is it, and how do we read it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from functools import cached_property
from pathlib import Path

from . import ixbrl

#: EDGAR accession number: <10-digit filer CIK>-<2-digit year>-<6-digit seq>.
#: The folder EDGAR hands you is that number plus an `-xbrl` suffix.
_ACCESSION_RE = re.compile(r"(\d{10})-(\d{2})-(\d{6})")

#: Filing documents are named `<filer-prefix>-<period end YYYYMMDD>.<ext>`,
#: e.g. `goog-20251231.htm`.
_DOCUMENT_RE = re.compile(r"^(?P<prefix>[a-z0-9]+)-(?P<date>\d{8})(?P<suffix>.*)$", re.I)

#: Files macOS and archive tools scatter through extracted folders. Not part
#: of the filing; silently ignored so they never appear in a manifest or get
#: mistaken for a document.
_JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
_JUNK_PREFIXES = ("._", "~$")


class FileRole(str, Enum):
    """What each file in the package is for."""

    #: The 10-K itself — inline XBRL, human-readable and machine-readable at once.
    PRIMARY_DOCUMENT = "primary_document"
    #: Exhibits filed alongside it (consents, certifications, subsidiaries).
    EXHIBIT = "exhibit"
    #: The filer's extension taxonomy — concepts not in standard US-GAAP.
    SCHEMA = "schema"
    #: The filer's own arithmetic: which children sum to which parent.
    CALCULATION_LINKBASE = "calculation_linkbase"
    #: Dimensional structure — segments, scenarios, and axes.
    DEFINITION_LINKBASE = "definition_linkbase"
    #: Human-readable labels the filer chose for each concept.
    LABEL_LINKBASE = "label_linkbase"
    #: Statement ordering and hierarchy as presented.
    PRESENTATION_LINKBASE = "presentation_linkbase"
    #: A separately extracted XBRL instance. Often absent — when the filing is
    #: inline XBRL, the primary document *is* the instance.
    INSTANCE = "instance"
    IMAGE = "image"
    OTHER = "other"


@dataclass(frozen=True)
class FilingFile:
    path: Path
    role: FileRole
    size_bytes: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_human(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
            size /= 1024
        return f"{size:,.1f} GB"

    def read_text(self) -> str:
        """Raw file contents. For the primary document you almost always want
        `Filing.document_text()` instead, which strips the XBRL markup."""
        return self.path.read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class Accession:
    """A parsed EDGAR accession number."""

    raw: str
    filer_cik: str
    filed_year: int
    sequence: int

    @classmethod
    def parse(cls, text: str) -> "Accession | None":
        match = _ACCESSION_RE.search(text)
        if not match:
            return None
        cik, year_2, seq = match.groups()
        # 2-digit year: EDGAR has been running since 1993, so anything in the
        # 90s is last century and everything else is this one.
        year = int(year_2)
        full_year = 1900 + year if year >= 93 else 2000 + year
        return cls(
            raw=f"{cik}-{year_2}-{seq}",
            filer_cik=cik,
            filed_year=full_year,
            sequence=int(seq),
        )


@dataclass
class Filing:
    """One uploaded filing package."""

    root: Path
    #: Which input folder it came from ("Latest 10k" / "Past 10k").
    source_label: str
    accession: Accession | None
    files: list[FilingFile] = field(default_factory=list)

    # -- file access ------------------------------------------------------

    def by_role(self, role: FileRole) -> list[FilingFile]:
        return [f for f in self.files if f.role is role]

    @property
    def primary_document(self) -> FilingFile | None:
        docs = self.by_role(FileRole.PRIMARY_DOCUMENT)
        return docs[0] if docs else None

    @property
    def exhibits(self) -> list[FilingFile]:
        return self.by_role(FileRole.EXHIBIT)

    @property
    def total_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)

    # -- identity ---------------------------------------------------------

    @cached_property
    def facts(self) -> ixbrl.EntityFacts:
        """DEI cover-page facts, read from the primary document.

        Cached because parsing a multi-megabyte filing is the expensive part of
        this module and callers ask for identity fields repeatedly.
        """
        document = self.primary_document
        if document is None:
            raise FileNotFoundError(
                f"no primary iXBRL document found in {self.root}"
            )
        return ixbrl.entity_facts(ixbrl.parse(document.path))

    @property
    def company_name(self) -> str | None:
        return self.facts.company_name

    @property
    def cik(self) -> str | None:
        return self.facts.cik

    @property
    def period_end(self) -> date | None:
        return self.facts.period_end

    @property
    def fiscal_year(self) -> int | None:
        return self.facts.fiscal_year

    @property
    def shares_outstanding_total(self) -> Decimal | None:
        """Summed across share classes.

        Alphabet tags Class A, B, and C separately; a single-class issuer tags
        one value. Summing is right for both, but the per-class figures remain
        available on `facts.shares_outstanding` — for a dual-class company the
        split is itself a governance fact worth keeping.
        """
        values = self.facts.shares_outstanding
        return sum(values) if values else None

    # -- reading ----------------------------------------------------------

    def document_text(self) -> str:
        """The annual report as plain text, ready to send to Claude."""
        document = self.primary_document
        if document is None:
            raise FileNotFoundError(f"no primary document in {self.root}")
        return ixbrl.to_text(ixbrl.parse(document.path))

    def exhibit_text(self, exhibit: FilingFile) -> str:
        return ixbrl.to_text(ixbrl.parse(exhibit.path))

    def fact_counts(self) -> tuple[int, int]:
        """(numeric, non-numeric) tagged facts in the primary document."""
        document = self.primary_document
        if document is None:
            return (0, 0)
        return ixbrl.count_facts(ixbrl.parse(document.path))

    # -- integrity --------------------------------------------------------

    def consistency_warnings(self) -> list[str]:
        """Checks that the upload is what it claims to be.

        Cheap to run and worth running: a filing analyzed under the wrong
        identity, or a "latest" folder holding last year's report, produces a
        confident and completely wrong analysis.
        """
        warnings: list[str] = []

        if self.primary_document is None:
            warnings.append(
                "No primary iXBRL document found — this may not be an EDGAR "
                "XBRL package."
            )
            return warnings

        if self.accession is None:
            warnings.append(
                f"Folder name {self.root.name!r} does not contain an accession "
                "number; provenance cannot be recorded."
            )
        elif self.cik and self.accession.filer_cik != self.cik:
            # Normal when an agent files on the company's behalf, so this is a
            # note rather than an error — but for a self-filer it means the
            # package and the document disagree about who filed.
            warnings.append(
                f"Accession filer CIK {self.accession.filer_cik} differs from "
                f"the document's CIK {self.cik} (filing agent, or mismatched files)."
            )

        doc_type = self.facts.document_type
        if doc_type and doc_type.upper() not in {"10-K", "10-K/A", "10-KT"}:
            warnings.append(
                f"Document type is {doc_type!r}, not a 10-K."
            )

        if self.facts.is_amendment:
            warnings.append(
                "This is an amended filing (AmendmentFlag=true) — it may "
                "restate figures from the original."
            )

        return warnings


# ------------------------------------------------------------------ discovery


def _is_junk(path: Path) -> bool:
    return path.name in _JUNK_NAMES or path.name.startswith(_JUNK_PREFIXES)


def _classify(path: Path, primary_name: str | None) -> FileRole:
    """Assign a role to one file.

    `primary_name` comes from the extension schema (`goog-20251231.xsd` implies
    `goog-20251231.htm`), which is more reliable than picking the largest HTML
    file — an unusually long exhibit would defeat that heuristic.
    """
    name = path.name
    lower = name.lower()
    suffix = path.suffix.lower()

    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".svg"}:
        return FileRole.IMAGE
    if suffix == ".xsd":
        return FileRole.SCHEMA

    if suffix == ".xml":
        if lower.endswith("_cal.xml"):
            return FileRole.CALCULATION_LINKBASE
        if lower.endswith("_def.xml"):
            return FileRole.DEFINITION_LINKBASE
        if lower.endswith("_lab.xml"):
            return FileRole.LABEL_LINKBASE
        if lower.endswith("_pre.xml"):
            return FileRole.PRESENTATION_LINKBASE
        if lower.endswith("_htm.xml"):
            return FileRole.INSTANCE
        return FileRole.OTHER

    if suffix in {".htm", ".html"}:
        if primary_name and name == primary_name:
            return FileRole.PRIMARY_DOCUMENT
        return FileRole.EXHIBIT

    return FileRole.OTHER


def _expected_primary_name(paths: list[Path]) -> str | None:
    """Derive the primary document's filename from the extension schema."""
    for path in paths:
        if path.suffix.lower() == ".xsd":
            return path.stem + ".htm"

    # No schema: fall back to the `<prefix>-<YYYYMMDD>.htm` naming convention,
    # which exhibits (`googexhibit3101q42025.htm`) do not follow.
    candidates = [
        p for p in paths
        if p.suffix.lower() in {".htm", ".html"} and _DOCUMENT_RE.match(p.stem)
        and not _DOCUMENT_RE.match(p.stem).group("suffix")  # type: ignore[union-attr]
    ]
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size).name
    return None


def _package_root(directory: Path) -> Path | None:
    """Find the directory actually holding the filing files.

    Handles the two shapes an upload takes: files sitting directly in the
    folder, or wrapped in one or more nesting levels by the unzip tool.
    """
    files = [p for p in directory.iterdir() if p.is_file() and not _is_junk(p)]
    if any(p.suffix.lower() in {".htm", ".html", ".xsd"} for p in files):
        return directory

    for child in sorted(directory.iterdir()):
        if child.is_dir() and not _is_junk(child):
            found = _package_root(child)
            if found is not None:
                return found
    return None


def load(directory: Path, *, source_label: str | None = None) -> Filing:
    """Build a `Filing` from an extracted EDGAR package directory."""
    directory = Path(directory)
    root = _package_root(directory)
    if root is None:
        raise FileNotFoundError(
            f"no filing documents found under {directory} — expected an "
            "extracted EDGAR XBRL folder"
        )

    paths = sorted(p for p in root.iterdir() if p.is_file() and not _is_junk(p))
    primary_name = _expected_primary_name(paths)

    files = [
        FilingFile(path=p, role=_classify(p, primary_name), size_bytes=p.stat().st_size)
        for p in paths
    ]

    # The accession number may be on the package folder or on a parent, since
    # the user may have renamed or re-nested the upload.
    accession = None
    for candidate in (root, *root.parents):
        accession = Accession.parse(candidate.name)
        if accession is not None:
            break

    return Filing(
        root=root,
        source_label=source_label or directory.name,
        accession=accession,
        files=files,
    )


def discover(directory: Path, *, source_label: str | None = None) -> list[Filing]:
    """Find every filing package inside an input folder.

    `Past 10k/` may legitimately hold several years, so this returns a list.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    label = source_label or directory.name
    filings: list[Filing] = []

    # Files sitting loose in the folder: the folder itself is one package.
    loose = [p for p in directory.iterdir() if p.is_file() and not _is_junk(p)]
    if any(p.suffix.lower() in {".htm", ".html", ".xsd"} for p in loose):
        return [load(directory, source_label=label)]

    for child in sorted(directory.iterdir()):
        if not child.is_dir() or _is_junk(child):
            continue
        try:
            filings.append(load(child, source_label=label))
        except FileNotFoundError:
            continue  # not a filing package; skip quietly

    return filings
