#!/usr/bin/env python3
"""Derive per-row Article 99 effective attribution.

The packaged ``tva_article99_catalog.json`` is a set of point-in-time snapshots.
A snapshot row is evidence that a clause was in force on the snapshot date; it
is not a validity period. This script turns those snapshots into dated segments
so the catalog can answer "which rate applied on this date", without ever
inventing a date that no source supports.

How a segment is derived
------------------------
1. Rows are grouped into product identities across the seven anchor editions
   (quote similarity, with a guard that forbids two rows of the same edition
   from joining one identity).
2. Each identity is cut into segments: a maximal run of consecutive anchors in
   which the rate is unchanged.
3. A segment boundary is dated only when a source names the instrument:

   * the first anchor is dated by the original enactment (Loi de finances
     n° 43-06, article 5, which created the CGI);
   * any later boundary is dated when the row's own consolidated endnote names
     exactly one instrument whose budget year falls inside the interval;
   * a hand-checked assertion may date a boundary when the amending law
     reproduces the clause but no endnote records it.

   Everything else stays a bracket and the row is not dated.

Every dated row therefore carries the instrument, the witness artifact, a hash
labelled by artifact kind, and a verbatim quote. ``tests/test_tva_article99.py``
re-checks all of it.

Run ``--report`` for coverage, ``--check`` in CI for idempotency.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "openfisca_morocco" / "data" / "tva_article99_catalog.json"
HOLY_GRAPH = Path("/home/masterswords/Desktop/morocco-holy-graph-issue80-final")
CORPUS_DATASET = Path("laws/ma_tax_law/data/consolidated/tva_article_lists.json")

YEARS = (2007, 2010, 2014, 2018, 2021, 2024, 2026)

SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Witnesses
# ---------------------------------------------------------------------------

#: The BO supplement that carries the original CGI as enacted by Loi 43-06.
#: The catalog previously pointed at a ``BO_5487_2007_SGG_index.pdf`` volume
#: that contains no Article 99 at all; this is the volume that does.
BASELINE_PDF = "laws/ma_fin_law/documents/BO_5487-bis_fr.pdf"

#: Consolidated editions: the PDF that is the primary snapshot witness.
EDITION_PDF = {
    2007: BASELINE_PDF,
    2010: "laws/ma_tax_law/data/consolidated/CGI-2010-FR.pdf",
    2014: "laws/ma_tax_law/data/consolidated/CGI-2014-FR.pdf",
    2018: "laws/ma_tax_law/data/consolidated/CGI-2018-FR.pdf",
    2021: "laws/ma_tax_law/data/consolidated/CGI-2021-FR.pdf",
    2024: "laws/ma_tax_law/data/consolidated/CGI-2024-FR.pdf",
    2026: "laws/ma_tax_law/data/consolidated/CGI-2026-FR.pdf",
}

#: Finance-law transcriptions. These are OCR transcriptions, so every quoted
#: fragment below is verified against the file at build time (whitespace
#: normalised only). ``date_basis`` records *why* the date is what it is, so a
#: reader can see which dates rest on an explicit clause and which rest on the
#: budget-year default.
INSTRUMENTS = {
    "43-06": {
        "law": "Loi de finances n° 43-06 pour l'année budgétaire 2007",
        "law_article": 5,
        "budget_year": 2007,
        "effective_from": "2007-01-01",
        "date_basis": "original_enactment",
        "bo": "5487 bis",
        "bo_date": "2007-01-01",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2015_100-14.txt",
            "quote": (
                "institué par l’article 5 de la loi de finances n° 43-06 pour "
                "l’année budgétaire 2007, promulguée par le dahir n° 1-06-232 "
                "du 10 hija"
            ),
        },
    },
    "38-07": {
        "law": "Loi n° 38-07 pour l'année budgétaire 2008",
        "law_article": 8,
        "budget_year": 2008,
        "effective_from": "2008-01-01",
        "date_basis": "explicit_in_article",
        "bo": "5591 bis",
        "bo_date": "2007-12-31",
        "fl": "data/text/finance-laws/FL_2008_38-07.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2008_38-07.txt",
            "quote": (
                "A compter du 1% janvier 2008, les dispositions des articles 2, "
                "6, 7, 10, 13, 19, 25, 28, 29, 31, 57, 61, 62, 63, 64, 65, 73, "
                "83, 92, 94, 99"
            ),
        },
    },
    "40-08": {
        "law": "Loi n° 40-08 pour l'année budgétaire 2009",
        "law_article": 7,
        "budget_year": 2009,
        "effective_from": "2009-01-01",
        "date_basis": "explicit_in_article",
        "bo": "5695 bis",
        "bo_date": "2008-12-31",
        "fl": "data/text/finance-laws/FL_2009_40-08.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2009_40-08.txt",
            "quote": (
                "A compter du 1e janvier 2009, les dispositions des articles 2, "
                "6, 7 (IV, VI et VIIT), 9 (I-C), 16, 20-I, 28, 39, 40, 41,47-II, "
                "57-10°, 59, 68-IT, 73, 74, 91, 92-I, 99 (1° et 2°),"
            ),
        },
    },
    "48-09": {
        "law": "Loi n° 48-09 pour l'année budgétaire 2010",
        "law_article": 7,
        "budget_year": 2010,
        "effective_from": "2010-01-01",
        "date_basis": "explicit_in_article",
        "bo": "5800 bis",
        "bo_date": "2009-12-31",
        "fl": "data/text/finance-laws/FL_2010_48-09.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2010_48-09.txt",
            "quote": (
                "I. A compter du 1% janvier 2010, les dispositions des articles "
                "26-II, 28, 44, 59, 63, 68, 70, 73, 79, 82, 85-II, 91, 92, 93, "
                "99, 105,"
            ),
        },
    },
    "115-12": {
        "law": "Loi n° 115-12 pour l'année budgétaire 2013",
        "law_article": 9,
        "budget_year": 2013,
        "effective_from": "2013-01-01",
        "date_basis": "budget_year_default",
        "fl": "data/text/finance-laws/FL_2013_115-12.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2013_115-12.txt",
            "quote": (
                "I. — Les dispositions des articles 6 (I-A-17°}, 7, 9, 11-IV, "
                "14, 19, 57, 60, 62-IL, 63, 65, 66, 67-IL, 68, 73-11, 74, 79, "
                "84-III-B, 89-1-7°, 91, 92, 93, 96, 99,"
            ),
            "note": (
                "Article 9 carries no date clause; the law is the finance law "
                "for budget year 2013, so the amendments apply from "
                "1 January 2013."
            ),
        },
    },
    "110-13": {
        "law": "Loi n° 110-13 pour l'année budgétaire 2014",
        "law_article": 4,
        "budget_year": 2014,
        "effective_from": "2014-01-01",
        "date_basis": "budget_year_default",
        "fl": "data/text/finance-laws/FL_2014_110-13.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2014_110-13.txt",
            "quote": (
                "I. Les dispositions des articles 6, 11, 19-I1-C, 26, 32, 43, "
                "44, 46, 60-1, 63 ,73, 82-IV, 86, 91, 92, 99,"
            ),
            "note": (
                "Article 4 carries no date clause; the law is the finance law "
                "for budget year 2014, so the amendments apply from "
                "1 January 2014."
            ),
        },
    },
    "100-14": {
        "law": "Loi n° 100-14 pour l'année budgétaire 2015",
        "law_article": 6,
        "budget_year": 2015,
        "effective_from": "2015-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2015_100-14.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2015_100-14.txt",
            "quote": (
                "I. – A compter du 1 er janvier 2015, les dispositions des "
                "articles 8, 10, 19-II, 20-I, 25 (3ème alinéa), 28-III, 42 ter, "
                "57, 60, 61, 65, 66, 70, 73 (II et III), 79, 84-III, 91, 92, 99,"
            ),
        },
    },
    "70-15": {
        "law": "Loi n° 70-15 pour l'année budgétaire 2016",
        "law_article": 8,
        "budget_year": 2016,
        "effective_from": "2016-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2016_70-15.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2016_70-15.txt",
            "quote": (
                "I.- A compter du 1 janvier 2016, les dispositions des articles "
                "6, 11-II, 19, 28-II, 44, 59-V, 63-II-B, 64-III, 65, 82-I, 86, "
                "89, 92-I, 93, 96, 99,"
            ),
        },
    },
    "73-16": {
        "law": "Loi n° 73-16 pour l'année budgétaire 2017",
        "law_article": 6,
        "budget_year": 2017,
        "effective_from": "2017-01-01",
        "date_basis": "budget_year_default",
        "fl": "data/text/finance-laws/FL_2017_73-16.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2017_73-16.txt",
            "quote": (
                "I. — Les dispositions des articles 2-IL, 6, 7, 9, 13, 14, 31, "
                "57, 62-INI, 66, 73, 79, 83, 86, 89, 90, 91, 92, 93, 95, 96, 99,"
            ),
            "note": (
                "Article 6 carries no date clause; the law is the finance law "
                "for budget year 2017, so the amendments apply from "
                "1 January 2017."
            ),
        },
    },
    "70-19": {
        "law": "Loi n° 70-19 pour l'année budgétaire 2020",
        "law_article": 6,
        "budget_year": 2020,
        "effective_from": "2020-01-01",
        "date_basis": "explicit_in_article",
        "bo": "6838 bis",
        "bo_date": "2019-12-14",
        "fl": "data/text/finance-laws/FL_2020_70-19.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2020_70-19.txt",
            "quote": (
                "I. – A compter du 1 janvier 2020, les dispositions des articles "
                "6, 7, 19, 20 bis, 28, 29, 31, 38, 40, 41, 47, 57, 60, 61, 63, "
                "68, 89, 90, 91, 92, 96, 99,"
            ),
        },
    },
    "65-20": {
        "law": "Loi n° 65-20 pour l'année budgétaire 2021",
        "law_article": 6,
        "budget_year": 2021,
        "effective_from": "2021-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2021_65-20.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2021_65-20.txt",
            "quote": (
                "I- A compter du 1 janvier 2021, les dispositions des articles 6, "
                "7, 9 bis, 10, 11-IV, 26, 32, 42 bis, 43, 44, 46, 60, 73, 82-I, "
                "82 bis-IV, 85, 86, 89, 91, 92, 99,"
            ),
        },
    },
    "76-21": {
        "law": "Loi n° 76-21 pour l'année budgétaire 2022",
        "law_article": 6,
        "budget_year": 2022,
        "effective_from": "2022-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2022_76-21.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2022_76-21.txt",
            "quote": (
                "A compter du 1janvier 2022, les dispositions des articles 11-IV, "
                "19, 40, 91, 92, 99,102,"
            ),
        },
    },
    "50-22": {
        "law": "Loi n° 50-22 pour l'année budgétaire 2023",
        "law_article": 6,
        "budget_year": 2023,
        "effective_from": "2023-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2023_50-22.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2023_50-22.txt",
            "quote": (
                "I. – A compter du 1 janvier 2023, les dispositions des articles "
                "4, 6, 10, 13, 19, 28, 31, 40-I, 42 bis, 46, 47, 57, 58, 59, 60, "
                "61, 63, 64, 65-II, 66-I, 68, 73, 82-I, 82 quater-I, 86, 89, 91, "
                "99,"
            ),
        },
    },
    "55-23": {
        "law": "Loi n° 55-23 pour l'année budgétaire 2024",
        "law_article": 6,
        "budget_year": 2024,
        "effective_from": "2024-01-01",
        "date_basis": "explicit_in_article",
        "bo": "7362 bis",
        "bo_date": "2023-12-19",
        "fl": "data/text/finance-laws/FL_2024_55-23.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2024_55-23.txt",
            "quote": (
                "I. – A compter du 1 janvier 2024, les dispositions des articles "
                "6, 10, 19, 29, 30, 34, 35, 38-II, 39, 60, 65, 70, 88, 89, 91, "
                "92, 93, 99,"
            ),
        },
    },
    "50-25": {
        "law": "Loi n° 50-25 pour l'année budgétaire 2026",
        "law_article": 7,
        "budget_year": 2026,
        "effective_from": "2026-01-01",
        "date_basis": "explicit_in_article",
        "fl": "data/text/finance-laws/FL_2026_50-25.txt",
        "date_witness": {
            "kind": "finance_law_transcription",
            "file": "data/text/finance-laws/FL_2026_50-25.txt",
            "quote": (
                "I. – A compter du 1 janvier 2026, les dispositions des articles "
                "4, 6, 9, 10, 13, 14, 19, 20-III, 31, 57, 66-II, 73-II, 74-I, "
                "79, 84-I, 91, 92-I, 99,"
            ),
        },
    },
}

#: Boundaries that the consolidated endnotes do not record, dated instead from
#: the amending law's own text. ``match`` is applied to the canonical quote.
#: Each entry must carry a verbatim quote from ``quote_file``; the generator
#: verifies it.
HAND_ASSERTIONS = [
    {
        "from_year": 2018,
        "to_year": 2021,
        "match": r"chauffeeauxsolaires",
        "law": "65-20",
        "method": "verbatim_reproduction",
        "derivation": "cross_article_handoff",
        "effect": "exempted",
        "successor": {
            "article": 91,
            "kind": "exoneration_sans_droit_a_deduction",
            "quote": "« 8° – les chauffe-eaux solaires.",
            "quote_file": "data/text/finance-laws/FL_2021_65-20.txt",
        },
        "note": (
            "Loi 65-20 article 6 removes the item from Article 99 and adds the "
            "same product as item 8° of the Article 91 exemption list, so the "
            "transaction became exempt rather than taxable at another rate."
        ),
    },
]

_LAW_NAME = re.compile(r"n°\s*(\d+)\s*-\s*(\d+)")

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_LEADING_ENUM = re.compile(r"^(?:\d+\s*°|[-–—•*]+|[a-z]\))\s*", re.IGNORECASE)
#: Trailing citation debris: endnote numbers, page references, punctuation.
#: Snapshot quotes end in forms like ``raffinées583 ;`` or
#: ``... solaires369;\n\n76-21 ``; none of that belongs to the clause.
_TRAILING_DEBRIS = re.compile(r"(?:[\s;.,:]+(?:\d{1,4}(?:-\d{1,4})?))+\s*$")
_GLUED_ENDNOTE = re.compile(r"(?<=[^\W\d_])[ \t]*\d{1,4}\s*$")
_TRAILING_PUNCT = re.compile(r"[\s;.,:]+$")

#: A quote that the corpus transcription truncated is still the same clause as
#: the longer quote it starts. Merging them needs a floor so that a stray short
#: fragment cannot join an unrelated identity.
_PREFIX_FLOOR = 30

#: Set by ``--debug`` to trace identity merges that only the truncation rule made.
_DEBUG = False


def canonical(quote: str) -> str:
    """Return the accent-free, punctuation-free identity key for a quote."""
    text = unicodedata.normalize("NFKD", quote)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    text = _LEADING_ENUM.sub("", text)
    text = _TRAILING_DEBRIS.sub("", text)
    text = _TRAILING_PUNCT.sub("", text)
    text = _GLUED_ENDNOTE.sub("", text)
    text = _TRAILING_PUNCT.sub("", text)
    return re.sub(r"[^a-z0-9]", "", text)


def flatten(text: str) -> str:
    """Flatten arbitrary text the same way, without stripping endnote digits."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def squash(text: str) -> str:
    """Collapse whitespace so a quote can match across line wrapping."""
    return re.sub(r"\s+", " ", text)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


_SOURCE_TEXT: dict[str, str] = {}
_FLAT_TEXT: dict[str, str] = {}


def source_text(relative: str) -> str:
    if relative not in _SOURCE_TEXT:
        _SOURCE_TEXT[relative] = (HOLY_GRAPH / relative).read_text(
            encoding="utf-8", errors="replace"
        )
    return _SOURCE_TEXT[relative]


def flat_text(relative: str) -> str:
    if relative not in _FLAT_TEXT:
        _FLAT_TEXT[relative] = flatten(source_text(relative))
    return _FLAT_TEXT[relative]


def contains_quote(relative: str, quote: str) -> bool:
    return squash(quote) in squash(source_text(relative))


# ---------------------------------------------------------------------------
# Identity resolution
# ---------------------------------------------------------------------------


def resolve_identities(rows):
    """Group snapshot rows into product identities.

    Two rows may join only if they come from different editions: an edition
    cannot list the same clause twice, so a same-edition collision always means
    the similarity threshold over-merged.
    """
    keys = [canonical(row["quote"]) for row in rows]
    parent = list(range(len(rows)))
    occupied = [{row["edition_year"]} for row in rows]

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    candidates = []
    joins = []
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            a, b = len(keys[left]), len(keys[right])
            if not a or not b:
                continue
            short, long = (
                (keys[left], keys[right]) if a <= b else (keys[right], keys[left])
            )
            truncated = len(short) >= _PREFIX_FLOOR and long.startswith(short)
            if not truncated and 2.0 * min(a, b) / (a + b) < 0.75:
                continue
            matcher = difflib.SequenceMatcher(None, keys[left], keys[right])
            if not truncated and matcher.quick_ratio() < 0.80:
                continue
            ratio = matcher.ratio()
            if ratio >= 0.80 or truncated:
                candidates.append((ratio, left, right))
                if truncated and ratio < 0.80:
                    joins.append((left, right, ratio))
    candidates.sort(reverse=True)

    for _ratio, left, right in candidates:
        a, b = find(left), find(right)
        if a == b or occupied[a] & occupied[b]:
            continue
        parent[b] = a
        occupied[a] |= occupied[b]

    if _DEBUG:
        for left, right, ratio in joins:
            print(
                f"truncation merge ({ratio:.2f}): {rows[left]['item_id']} ~ "
                f"{rows[right]['item_id']}",
                file=sys.stderr,
            )

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        groups[find(index)].append(index)
    return list(groups.values()), keys


def segments_of(group, rows):
    """Cut one identity into maximal same-rate runs of consecutive anchors."""
    present = sorted({rows[index]["edition_year"] for index in group})
    segments = []
    for year in present:
        rate = next(
            rows[index]["rate"]
            for index in group
            if rows[index]["edition_year"] == year
        )
        if (
            segments
            and segments[-1]["rate"] == rate
            and YEARS.index(segments[-1]["last"]) + 1 == YEARS.index(year)
        ):
            segments[-1]["last"] = year
        else:
            segments.append({"first": year, "last": year, "rate": rate})
    return segments


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


def law_key(law_name: str) -> str | None:
    match = _LAW_NAME.search(law_name or "")
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def instrument_record(key: str):
    """The single authoritative record for one amending instrument."""
    spec = INSTRUMENTS[key]
    record = {
        "law": spec["law"],
        "law_article": spec["law_article"],
        "budget_year": spec["budget_year"],
        "effective_from": spec["effective_from"],
        "date_basis": spec["date_basis"],
    }
    if spec.get("bo"):
        record["bo"] = spec["bo"]
        record["bo_date"] = spec["bo_date"]
    witness = dict(spec["date_witness"])
    witness["text_sha256"] = sha256_of(HOLY_GRAPH / witness["file"])
    record["date_witness"] = witness
    return record


def endnote_candidates(group, rows, from_year, to_year, all_editions=False):
    """Return the in-interval instruments named by this identity's endnotes.

    When the identity is absent on one side of the boundary, every row of the
    identity was created or last touched inside the interval, so an endnote on
    any edition is evidence for this boundary. When the identity spans both
    anchors there is a row on each side and only those two can speak for the
    boundary.
    """
    found = {}
    for index in group:
        row = rows[index]
        if not all_editions and row["edition_year"] not in (from_year, to_year):
            continue
        for citation in row.get("amendment_citations") or ():
            budget_year = citation.get("budget_year")
            if budget_year is None or not from_year < budget_year <= to_year:
                continue
            found[(citation["law"], citation["law_article"], budget_year)] = citation
    return found


def hand_assertion(from_year, to_year, key):
    for assertion in HAND_ASSERTIONS:
        if assertion["from_year"] != from_year or assertion["to_year"] != to_year:
            continue
        if re.search(assertion["match"], key):
            return assertion
    return None


def endnote_witness(citation, edition_pdf, edition_pdf_sha):
    return {
        "kind": "consolidated_endnote",
        "edition": citation["source_edition"],
        "corpus_file": citation["corpus_file"],
        "text_sha256": citation["source_sha256"],
        "endnote": citation["endnote"],
        "endnote_quote": citation["quote"],
        "amending_law_corpus_file": citation["amending_law_corpus_file"],
        "amending_law_text_sha256": citation["amending_law_source_sha256"],
        "pdf_file": edition_pdf,
        "pdf_sha256": edition_pdf_sha,
    }


def bracketed(reason, earliest, latest, candidates=None):
    payload = {
        "status": "bracketed",
        "validity_bracket": {"earliest": earliest, "latest": latest},
        "reason": reason,
    }
    if candidates:
        payload["candidates"] = sorted(set(candidates))
    return payload


def dated_boundary(group, rows, from_year, to_year, key, side, edition_pdfs, continues):
    """Date one segment boundary, or explain why it stays bracketed."""
    earliest = f"{from_year}-01-01"
    latest = f"{to_year}-01-01"
    withdrawn = "superseded" if continues else "repealed"

    present = {rows[index]["edition_year"] for index in group}
    spans_both = from_year in present and to_year in present
    cited = endnote_candidates(
        group, rows, from_year, to_year, all_editions=not spans_both
    )
    cited_laws = {law_key(name) or name for name, _article, _year in cited}
    assertion = hand_assertion(from_year, to_year, key)

    if assertion and cited and assertion["law"] not in cited_laws:
        return bracketed(
            "instrument_conflict",
            earliest,
            latest,
            candidates=cited_laws | {assertion["law"]},
        )

    if assertion:
        spec = INSTRUMENTS[assertion["law"]]
        payload = {
            "status": "proven",
            "valid_from": spec["effective_from"],
            "valid_to": spec["effective_from"],
            "method": assertion["method"],
            "derivation": assertion["derivation"],
            "instrument": assertion["law"],
            "witness": {
                "kind": "finance_law_transcription",
                "file": assertion["successor"]["quote_file"],
                "text_sha256": sha256_of(
                    HOLY_GRAPH / assertion["successor"]["quote_file"]
                ),
                "quote": assertion["successor"]["quote"],
            },
            "note": assertion["note"],
        }
        if side == "end":
            payload["effect"] = assertion.get("effect", withdrawn)
            payload["successor"] = {
                "article": assertion["successor"]["article"],
                "kind": assertion["successor"]["kind"],
                "quote": assertion["successor"]["quote"],
            }
            payload.pop("valid_from", None)
        else:
            payload.pop("valid_to", None)
        return payload

    if len(cited) == 1:
        (law, _article, _year), citation = next(iter(cited.items()))
        key_for_law = law_key(law)
        if key_for_law is None or key_for_law not in INSTRUMENTS:
            return bracketed("unmapped_instrument", earliest, latest, [law])
        spec = INSTRUMENTS[key_for_law]
        edition = citation["source_edition"]
        payload = {
            "status": "proven",
            "valid_from": spec["effective_from"],
            "valid_to": spec["effective_from"],
            "method": "consolidated_endnote",
            "derivation": "snapshot_endnote",
            "instrument": key_for_law,
            "witness": endnote_witness(
                citation, edition_pdfs[edition][0], edition_pdfs[edition][1]
            ),
        }
        if "fl" in spec:
            quote = canonical(rows[group[0]]["quote"])
            if len(quote) >= 25 and quote in flat_text(spec["fl"]):
                payload["corroboration"] = {
                    "kind": "amending_law_transcription_contains_quote",
                    "file": spec["fl"],
                    "text_sha256": sha256_of(HOLY_GRAPH / spec["fl"]),
                }
        if side == "end":
            payload["effect"] = withdrawn
            payload.pop("valid_from", None)
        else:
            payload.pop("valid_to", None)
        return payload

    if len(cited) > 1:
        return bracketed("ambiguous_instruments", earliest, latest, cited_laws)

    if side == "start" and not cited:
        match = verbatim_introduction(group, rows, from_year, to_year, edition_pdfs)
        if match is not None:
            return match

    if side == "end":
        reason = "rate_change_not_witnessed" if continues else "repeal_not_witnessed"
    else:
        reason = "introduction_not_witnessed"
    return bracketed(reason, earliest, latest)


#: A verbatim match shorter than this is too weak to attribute an introduction.
_VERBATIM_FLOOR = 40


def verbatim_introduction(group, rows, from_year, to_year, edition_pdfs):
    """Attribute an introduction from the amending law's own reproduction.

    Only used when no endnote speaks, and only for an introduction: an item that
    is absent on the earlier anchor and whose clause text appears verbatim in
    exactly one in-interval finance law was put there by that law. A removal
    cannot be witnessed this way, and a rate change needs the endnote because
    the wording is unchanged.
    """
    quote = canonical(rows[group[0]]["quote"])
    if len(quote) < _VERBATIM_FLOOR:
        return None

    hits = []
    for law, spec in INSTRUMENTS.items():
        if "fl" not in spec:
            continue
        if not from_year < spec["budget_year"] <= to_year:
            continue
        if quote in flat_text(spec["fl"]):
            hits.append(law)
    if len(hits) != 1:
        return None

    law = hits[0]
    spec = INSTRUMENTS[law]
    return {
        "status": "proven",
        "valid_from": spec["effective_from"],
        "method": "verbatim_reproduction",
        "derivation": "primary_text_match",
        "instrument": law,
        "witness": {
            "kind": "finance_law_transcription",
            "file": spec["fl"],
            "text_sha256": sha256_of(HOLY_GRAPH / spec["fl"]),
            "quote": rows[group[0]]["quote"],
        },
    }


def baseline_start(row, edition_pdfs):
    return {
        "status": "proven",
        "valid_from": INSTRUMENTS["43-06"]["effective_from"],
        "method": "verbatim_reproduction",
        "derivation": "original_enactment",
        "instrument": "43-06",
        "witness": {
            "kind": "consolidated_edition",
            "edition": 2007,
            "corpus_file": "laws/ma_tax_law/data/consolidated/CGI-2007-FR.pdf.txt",
            "text_sha256": sha256_of(
                HOLY_GRAPH / "laws/ma_tax_law/data/consolidated/CGI-2007-FR.pdf.txt"
            ),
            "quote": row["quote"],
            "pdf_file": edition_pdfs[2007][0],
            "pdf_sha256": edition_pdfs[2007][1],
        },
    }


def build_row_attribution(row, key, segment, continues, group, rows, edition_pdfs):
    if segment["first"] == YEARS[0]:
        start = baseline_start(row, edition_pdfs)
    else:
        previous = YEARS[YEARS.index(segment["first"]) - 1]
        start = dated_boundary(
            group,
            rows,
            previous,
            segment["first"],
            key,
            "start",
            edition_pdfs,
            continues,
        )

    if segment["last"] == YEARS[-1]:
        end = {
            "status": "proven",
            "valid_to": None,
            "still_in_force_at": f"{YEARS[-1]}-01-01",
        }
    else:
        following = YEARS[YEARS.index(segment["last"]) + 1]
        end = dated_boundary(
            group,
            rows,
            segment["last"],
            following,
            key,
            "end",
            edition_pdfs,
            continues,
        )

    proven = start["status"] == "proven" and end["status"] == "proven"
    return {
        "status": "proven" if proven else "bracketed",
        "rate_segment": {
            "first_anchor": segment["first"],
            "last_anchor": segment["last"],
            "rate": segment["rate"],
        },
        "start": start,
        "end": end,
    }


# ---------------------------------------------------------------------------
# Verification of the evidence table
# ---------------------------------------------------------------------------


def verify_evidence():
    """Fail loudly if a quoted date clause is not verbatim in its source."""
    problems = []
    for key, spec in INSTRUMENTS.items():
        witness = spec["date_witness"]
        path = HOLY_GRAPH / witness["file"]
        if not path.exists():
            problems.append(f"{key}: missing witness file {witness['file']}")
            continue
        if not contains_quote(witness["file"], witness["quote"]):
            problems.append(f"{key}: quote not found in {witness['file']}")
    for assertion in HAND_ASSERTIONS:
        successor = assertion["successor"]
        if not contains_quote(successor["quote_file"], successor["quote"]):
            problems.append(
                f"handoff {assertion['match']}: quote not found in "
                f"{successor['quote_file']}"
            )
        if assertion["law"] not in INSTRUMENTS:
            problems.append(f"handoff {assertion['match']}: unknown law")
    return problems


def attach_subitems(catalog):
    """Attach the corpus's nested Article 99 leaves to their parent clause.

    The catalog's ``items`` are the 420 top-level rows. The corpus also splits
    multi-product clauses into ``billable_leaf`` rows (134 across the seven
    editions). Those are real nested sub-items, not duplicates, so they are
    exposed under ``subitems`` with an explicit ``parent_item_id`` instead of
    being flattened away.

    Effective dates are deliberately *not* copied here: a leaf is dated only by
    its parent's segment, so the loader resolves ``effective_attribution`` from
    the parent at import time. Storing a second copy would let the two drift.
    """
    dataset = HOLY_GRAPH / CORPUS_DATASET
    corpus = json.loads(dataset.read_text(encoding="utf-8"))

    leaves_by_edition = defaultdict(list)
    for row in corpus["items"]:
        if row.get("article") != 99 or "-leaf-" not in row["item_id"]:
            continue
        leaves_by_edition[row["edition_year"]].append(row)

    for edition in catalog["editions"]:
        year = edition["edition_year"]
        parent_ids = {row["item_id"] for row in edition["items"]}
        subitems = []
        for row in leaves_by_edition.get(year, ()):
            if row["parent_item_id"] not in parent_ids:
                raise SystemExit(
                    f"Article 99 leaf {row['item_id']} names a parent "
                    f"{row['parent_item_id']} that is not packaged"
                )
            if row.get("status") != "in_force_in_snapshot":
                raise SystemExit(
                    f"Article 99 leaf {row['item_id']} has an unsupported status"
                )
            if row.get("itemization_role") != "billable_leaf":
                raise SystemExit(
                    f"Article 99 leaf {row['item_id']} is not a billable_leaf"
                )
            subitems.append(
                {
                    "article": 99,
                    "edition_year": year,
                    "item_id": row["item_id"],
                    "parent_item_id": row["parent_item_id"],
                    "product_key": row.get("product_key"),
                    "item_type": row.get("item_type"),
                    "itemization": row["itemization"],
                    "itemization_role": row["itemization_role"],
                    "billable": row.get("billable"),
                    "right_to_deduct": row.get("right_to_deduct"),
                    "status": row["status"],
                    "rate": row["rate"],
                    "rate_context_quote": row["rate_context_quote"],
                    "quote": row["quote"],
                    "conditions": row.get("conditions") or [],
                    "corpus_file": row["corpus_file"],
                }
            )
        subitems.sort(key=lambda item: item["item_id"])
        edition["subitems"] = subitems

    return sum(len(edition["subitems"]) for edition in catalog["editions"])


def project_corpus_conditions(catalog):
    """Re-project each item's ``conditions`` from the corpus row it names.

    ``conditions`` are qualifiers that narrow a listed clause (for example
    *à l'exclusion des autres aliments simples tels que céréales, issues,
    pulpes, drêches et pailles*). They are part of the law, so they are copied
    verbatim from the corpus row rather than re-parsed. Quote and rate are
    checked at the same time: a row that disagrees with its corpus row about the
    law's text is an error, not something to overwrite silently.
    """
    dataset = HOLY_GRAPH / CORPUS_DATASET
    corpus = json.loads(dataset.read_text(encoding="utf-8"))
    source = {
        (row["edition_year"], row["item_id"]): row
        for row in corpus["items"]
        if row.get("article") == 99
    }

    changed = []
    for edition in catalog["editions"]:
        year = edition["edition_year"]
        for row in edition["items"]:
            origin = source.get((year, row["item_id"]))
            if origin is None:
                raise SystemExit(
                    f"Article 99 item {row['item_id']} has no corpus row in {year}"
                )
            if origin["quote"] != row["quote"]:
                raise SystemExit(
                    f"Article 99 item {row['item_id']} quote differs from the corpus"
                )
            if origin["rate"] != row["rate"]:
                raise SystemExit(
                    f"Article 99 item {row['item_id']} rate differs from the corpus"
                )
            projected = origin.get("conditions") or []
            if projected == (row.get("conditions") or []):
                continue
            changed.append(row["item_id"])
            row["conditions"] = projected

    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the catalog is not up to date"
    )
    parser.add_argument("--report", action="store_true", help="print a coverage report")
    parser.add_argument(
        "--debug", action="store_true", help="trace truncation-driven merges"
    )
    args = parser.parse_args(argv)

    global _DEBUG
    _DEBUG = args.debug

    problems = verify_evidence()
    if problems:
        for problem in problems:
            print(f"evidence error: {problem}", file=sys.stderr)
        return 1

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    edition_pdfs = {}
    for edition in catalog["editions"]:
        year = edition["edition_year"]
        relative = EDITION_PDF[year]
        edition_pdfs[year] = (relative, sha256_of(HOLY_GRAPH / relative))
        edition["source_pdf"] = relative
        edition["source_pdf_sha256"] = edition_pdfs[year][1]

    rows = [row for edition in catalog["editions"] for row in edition["items"]]
    conditions_restored = project_corpus_conditions(catalog)
    groups, keys = resolve_identities(rows)

    uncovered_laws = set()
    for citation_law in (
        citation["law"]
        for row in rows
        for citation in (row.get("amendment_citations") or ())
    ):
        key = law_key(citation_law)
        if key not in INSTRUMENTS:
            uncovered_laws.add(citation_law)

    for group in groups:
        key = keys[group[0]]
        segments = segments_of(group, rows)
        for index in group:
            row = rows[index]
            segment = next(
                item
                for item in segments
                if item["first"] <= row["edition_year"] <= item["last"]
            )
            row["effective_attribution"] = build_row_attribution(
                row,
                key,
                segment,
                segment is not segments[-1],
                group,
                rows,
                edition_pdfs,
            )

    catalog["schema_version"] = SCHEMA_VERSION
    subitem_count = attach_subitems(catalog)
    catalog["date_semantics"] = (
        "edition_year identifies a consolidated text snapshot, not a continuous "
        "effective period. Effective dates come only from effective_attribution: "
        "each row records a dated segment whose boundaries are either witnessed "
        "(status 'proven', with method, instrument, artifact, SHA-256 and quote) "
        "or left as an explicit validity_bracket (status 'bracketed', no dates). "
        "valid_to is exclusive: it is the first day the successor text applied. "
        "Instruments are defined once in 'instruments' and referenced by key."
    )

    instruments = {key: instrument_record(key) for key in INSTRUMENTS}
    ordered = {}
    for name, value in catalog.items():
        if name == "editions":
            ordered["instruments"] = instruments
        ordered[name] = value
    catalog = ordered

    if args.report:
        proven = sum(
            1 for row in rows if row["effective_attribution"]["status"] == "proven"
        )
        print(f"rows: {len(rows)}  identities: {len(groups)}")
        print(f"nested subitems: {subitem_count}")
        print(f"conditions re-projected from the corpus: {len(conditions_restored)}")
        print(f"proven: {proven} ({proven / len(rows):.1%})")
        print(f"bracketed: {len(rows) - proven}")

        reasons = defaultdict(int)
        for row in rows:
            attribution = row["effective_attribution"]
            for side in ("start", "end"):
                part = attribution[side]
                if part["status"] != "proven":
                    reasons[part["reason"]] += 1

        print("\nunwitnessed boundaries by reason:")
        for reason, count in sorted(reasons.items(), key=lambda item: -item[1]):
            print(f"   {reason}: {count}")

        methods = defaultdict(int)
        for row in rows:
            attribution = row["effective_attribution"]
            for side in ("start", "end"):
                part = attribution[side]
                if part["status"] == "proven" and part.get("method"):
                    methods[part["method"]] += 1
        print("\nwitnessed boundaries by method:")
        for method, count in sorted(methods.items(), key=lambda item: -item[1]):
            print(f"   {method}: {count}")

        print("\nper segment:")
        for group in sorted(
            groups, key=lambda g: (min(rows[i]["edition_year"] for i in g), keys[g[0]])
        ):
            segments = segments_of(group, rows)
            label = squash(rows[group[0]]["quote"])[:56]
            present = [seg["rate"] for seg in segments]
            statuses = []
            for index in group:
                attribution = rows[index]["effective_attribution"]
                statuses.append(attribution["status"][0].upper())
            print(
                f"   {''.join(sorted(set(statuses))):2s} {present} "
                f"{[seg['first'] for seg in segments]}..{segments[-1]['last']} | {label}"
            )

    if uncovered_laws:
        print(
            "\ncitations naming an instrument absent from INSTRUMENTS: "
            + ", ".join(sorted(uncovered_laws)),
            file=sys.stderr,
        )

    rendered = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if rendered != CATALOG.read_text(encoding="utf-8"):
            print(
                "catalog is out of date; run scripts/build_article99_attribution.py",
                file=sys.stderr,
            )
            return 1
        return 0

    CATALOG.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
