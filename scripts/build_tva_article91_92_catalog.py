#!/usr/bin/env python3
"""Build the packaged Article 91/92 exemption catalog from the Holy Graph corpus.

The catalog is a *verbatim projection* of one corpus dataset: every row keeps the
corpus item ID, clause number, quote and status exactly as published. Nothing is
re-parsed from a PDF, so a row can never be renumbered or merged with a
neighbour.

Two buckets are emitted per edition:

``items``
    The source-level article context and the numbered clauses. These are the
    stable, human-addressable rows and keep the corpus ``item_id`` verbatim.

``subitems``
    The nested bullets and letters beneath a clause. They are real legal sub-items
    (``item_role`` is ``leaf`` or ``container``), so they get their own row rather
    than being flattened into the parent's quote. Their corpus ID embeds
    extraction noise (a bullet glyph, a content hash) and is not a usable key, so
    they also get a stable ASCII ID of the form ``<parent>-sub-<n>``, where ``n``
    is the 1-based position among that parent's children in source order. The
    corpus ID is preserved verbatim as ``source_item_id``.

Run with ``--check`` to fail when the packaged artifact is stale, or ``--report``
to print the coverage summary without writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

DEFAULT_CORPUS = Path(
    os.environ.get("MOROCCO_HOLY_GRAPH")
    or Path(__file__).resolve().parent.parent.parent / "morocco-holy-graph"
)
CORPUS_DATASET = Path("laws/ma_tax_law/data/consolidated/tva_article_lists.json")
PACKAGE_CATALOG = Path("openfisca_morocco/data/tva_article91_92_catalog.json")

SCHEMA_VERSION = 2
ARTICLES = (91, 92)
EDITION_YEARS = (2007, 2010, 2014, 2018, 2021, 2024, 2026)

CORE_ITEMIZATIONS = ("article_level", "numbered_clause")
NESTED_ITEMIZATIONS = ("nested_bullet", "nested_letter")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def corpus_path(corpus_root: Path, relative: str) -> Path:
    candidate = corpus_root / relative
    if not candidate.is_file():
        raise SystemExit(f"missing corpus artifact: {candidate}")
    return candidate


def load_corpus(corpus_root: Path) -> dict:
    path = corpus_path(corpus_root, str(CORPUS_DATASET))
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sibling_ordinals(rows: list[dict]) -> dict[str, int]:
    """Map a nested corpus ID to its 1-based position among its siblings.

    Source order is the corpus order, which is the order the consolidated text
    prints. A parent's children therefore keep a stable ordinal as long as the
    source does not reorder them.
    """
    counts: dict[str, int] = {}
    ordinals: dict[str, int] = {}
    for row in rows:
        parent = row["parent_item_id"]
        counts[parent] = counts.get(parent, 0) + 1
        ordinals[row["item_id"]] = counts[parent]
    return ordinals


def build_edition(corpus: dict, snapshot: dict, year: int) -> dict:
    rows = [
        row
        for row in corpus["items"]
        if row.get("edition_year") == year and row.get("article") in ARTICLES
    ]
    core = [row for row in rows if row.get("itemization") in CORE_ITEMIZATIONS]
    nested = [row for row in rows if row.get("itemization") in NESTED_ITEMIZATIONS]

    unknown = [
        row["item_id"]
        for row in rows
        if row.get("itemization") not in CORE_ITEMIZATIONS + NESTED_ITEMIZATIONS
    ]
    if unknown:
        raise SystemExit(f"unclassified source itemizations: {unknown[:5]}")

    ordinals = sibling_ordinals(nested)
    # Corpus ID -> packaged ID. Core rows keep their corpus ID.
    packaged_ids = {row["item_id"]: row["item_id"] for row in core}

    subitems = []
    for row in nested:
        parent_corpus_id = row["parent_item_id"]
        parent_packaged_id = packaged_ids.get(parent_corpus_id)
        if parent_packaged_id is None:
            raise SystemExit(
                f"nested item {row['item_id']} has an unknown parent "
                f"{parent_corpus_id}; the parent must precede it in source order"
            )
        packaged_id = f"{parent_packaged_id}-sub-{ordinals[row['item_id']]}"
        packaged_ids[row["item_id"]] = packaged_id
        subitems.append(
            {
                "article": row["article"],
                "edition_year": year,
                "item_id": packaged_id,
                "source_item_id": row["item_id"],
                "parent_item_id": parent_packaged_id,
                "parent_source_item_id": parent_corpus_id,
                "clause_number": row.get("clause_number"),
                "itemization": row["itemization"],
                "item_role": row.get("item_role"),
                "nesting_depth": row.get("nesting_depth"),
                "source_marker": row.get("source_marker"),
                "source_marker_type": row.get("source_marker_type"),
                "status": row["status"],
                "rate": row["rate"],
                "right_to_deduct": row["right_to_deduct"],
                "quote": row["quote"],
                "rate_context_quote": row["rate_context_quote"],
                "subsection_context_quote": row.get("subsection_context_quote"),
                "parent_context_quote": row.get("parent_context_quote"),
                "corpus_file": row["corpus_file"],
            }
        )

    items = []
    for row in core:
        items.append(
            {
                "article": row["article"],
                "edition_year": year,
                "item_id": row["item_id"],
                "source_item_id": row["item_id"],
                "parent_item_id": None,
                "parent_source_item_id": None,
                "clause_number": row.get("clause_number"),
                "itemization": row["itemization"],
                "item_role": row.get("item_role"),
                "nesting_depth": 0,
                "source_marker": row.get("source_marker"),
                "source_marker_type": row.get("source_marker_type"),
                "status": row["status"],
                "rate": row["rate"],
                "right_to_deduct": row["right_to_deduct"],
                "quote": row["quote"],
                "rate_context_quote": row["rate_context_quote"],
                "subsection_context_quote": row.get("subsection_context_quote"),
                "parent_context_quote": None,
                "corpus_file": row["corpus_file"],
            }
        )

    # Source order must survive the projection: article context, then clauses,
    # then each clause's sub-items immediately after it.
    order = {row["item_id"]: index for index, row in enumerate(rows)}
    items.sort(key=lambda item: order[item["source_item_id"]])
    subitems.sort(key=lambda item: order[item["source_item_id"]])

    return {
        "edition_year": year,
        "snapshot_date": snapshot["as_of"],
        "document_title": snapshot["document_title"],
        "corpus_file": snapshot["corpus_file"],
        "source_pdf": snapshot["source_pdf"],
        "source_pdf_sha256": snapshot["source_pdf_sha256"],
        "source_text_sha256": snapshot["source_text_sha256"],
        "items": items,
        "subitems": subitems,
    }


def build(corpus_root: Path) -> dict:
    corpus = load_corpus(corpus_root)
    snapshots = {snapshot["year"]: snapshot for snapshot in corpus["snapshots"]}
    missing = [year for year in EDITION_YEARS if year not in snapshots]
    if missing:
        raise SystemExit(f"corpus is missing Article 91/92 snapshots: {missing}")

    editions = [build_edition(corpus, snapshots[year], year) for year in EDITION_YEARS]

    for edition in editions:
        for row in edition["items"] + edition["subitems"]:
            if "valid_from" in row or "valid_to" in row:
                raise SystemExit("snapshot rows must not carry effective dates")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_catalog": "morocco-holy-graph/laws/ma_tax_law/data/consolidated/tva_article_lists.json",
        "articles": list(ARTICLES),
        "date_semantics": (
            "edition_year and snapshot_date identify one consolidated text "
            "snapshot; they do not claim continuous validity between snapshots. "
            "No valid_from or valid_to fields are included."
        ),
        "coverage": coverage_summary(editions),
        "editions": editions,
    }


def coverage_summary(editions: list[dict]) -> dict:
    items = [row for edition in editions for row in edition["items"]]
    subitems = [row for edition in editions for row in edition["subitems"]]
    subitem_years = {}
    for article in ARTICLES:
        subitem_years[str(article)] = [
            edition["edition_year"]
            for edition in editions
            if any(row["article"] == article for row in edition["subitems"])
        ]
    return {
        "edition_years": [edition["edition_year"] for edition in editions],
        "items_by_article": {
            str(article): sum(1 for row in items if row["article"] == article)
            for article in ARTICLES
        },
        "subitems_by_article": {
            str(article): sum(1 for row in subitems if row["article"] == article)
            for article in ARTICLES
        },
        "subitem_edition_years": subitem_years,
        "subitem_roles": sorted(
            {str(row["item_role"]) for row in subitems if row["item_role"]}
        ),
        "editions_without_subitems": {
            str(article): [
                edition["edition_year"]
                for edition in editions
                if not any(row["article"] == article for row in edition["subitems"])
            ]
            for article in ARTICLES
            if any(
                not any(row["article"] == article for row in edition["subitems"])
                for edition in editions
            )
        },
        "notes": (
            "items are the source-level article context and the numbered "
            "clauses, addressed by their corpus item ID. subitems are the nested "
            "bullets and letters the consolidated text prints beneath a clause, "
            "addressed by <parent>-sub-<n> with the corpus ID kept as "
            "source_item_id. A missing subitem edition means the source prints no "
            "nested sub-items there; it is not an extraction gap. CGI Article 99 "
            "is not covered here: its corpus rows are all flat listed_clause rows."
        ),
    }


def serialise(catalog: dict) -> str:
    return json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"


def verify_against_corpus(corpus_root: Path, catalog: dict) -> list[str]:
    """Every packaged quote must be byte-identical to its corpus source row."""
    corpus = load_corpus(corpus_root)
    source = {row["item_id"]: row for row in corpus["items"]}
    problems = []
    for edition in catalog["editions"]:
        for row in edition["items"] + edition["subitems"]:
            origin = row["source_item_id"]
            if origin not in source:
                problems.append(f"{row['item_id']}: no corpus row {origin}")
                continue
            if source[origin]["quote"] != row["quote"]:
                problems.append(f"{row['item_id']}: quote differs from {origin}")
            if source[origin]["status"] != row["status"]:
                problems.append(f"{row['item_id']}: status differs from {origin}")
            if source[origin].get("clause_number") != row["clause_number"]:
                problems.append(
                    f"{row['item_id']}: clause number differs from {origin}"
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=PACKAGE_CATALOG)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)

    if not (args.corpus / CORPUS_DATASET).is_file():
        raise SystemExit(f"corpus dataset not found under {args.corpus}")

    catalog = build(args.corpus)
    problems = verify_against_corpus(args.corpus, catalog)
    if problems:
        for problem in problems[:20]:
            print(f"PROVENANCE FAILURE: {problem}", file=sys.stderr)
        raise SystemExit(f"{len(problems)} provenance failures")

    rendered = serialise(catalog)
    coverage = catalog["coverage"]

    if args.report or args.check:
        print(f"editions: {coverage['edition_years']}")
        print(f"items by article: {coverage['items_by_article']}")
        print(f"subitems by article: {coverage['subitems_by_article']}")
        print(f"subitem edition years: {coverage['subitem_edition_years']}")
        print(f"editions without subitems: {coverage['editions_without_subitems']}")
        total = sum(coverage["items_by_article"].values()) + sum(
            coverage["subitems_by_article"].values()
        )
        print(f"total packaged rows: {total}")

    if args.check:
        if not args.output.is_file():
            raise SystemExit(f"packaged catalog missing: {args.output}")
        if args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"{args.output} is stale; re-run without --check")
        print(f"{args.output} is up to date")
        return 0

    if args.report:
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output} ({len(rendered.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
