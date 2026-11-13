"""Read-only access to historical Loi 30-85 TVA Article 15 snapshots.

The catalog contains separate lists as of 2004-01-01 and 2005-01-01. These
pre-CGI snapshots do not define continuous validity and do not classify
products from their descriptions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class Article15Condition:
    """A verbatim condition attached to an Article 15 list item."""

    kind: str
    quote: str


@dataclass(frozen=True)
class Article15DGIEndnoteCitation:
    """An endnote in the 2002 DGI compilation."""

    label: str
    corpus_file: str
    quote: str
    source_sha256: str


@dataclass(frozen=True)
class Article15AmendmentCitation:
    """A visually transcribed Gazette excerpt amending Loi 30-85 Article 15."""

    law: str
    law_article: int
    article_amended: int
    effective_from: str
    corpus_file: str
    source_pdf: str
    source_pdf_sha256: str
    source_pdf_pages: tuple[int, ...]
    source_url: str
    source_quote: str
    transcription_sha256: str
    quote_verification: str


@dataclass(frozen=True)
class Article15BaselineSource:
    """Source metadata for the DGI compilation used as the list baseline."""

    corpus_file: str
    source_sha256: str
    source_url: str
    source_pages: tuple[int, ...]
    retrieval_limitation: str


@dataclass(frozen=True)
class Article15Item:
    """A quoted item in one exact Article 15 snapshot."""

    edition_year: int
    snapshot_date: str
    article: int
    item_id: str
    rate: str
    rate_context_quote: str
    item_type: str
    right_to_deduct: bool | None
    quote: str
    conditions: tuple[Article15Condition, ...]
    status: str
    corpus_file: str
    itemization: str
    source_sha256: str
    source_pages: tuple[int, ...]
    rate_context_corpus_file: str | None
    amendment_citations: tuple[Article15AmendmentCitation, ...]
    dgi_endnote_citations: tuple[Article15DGIEndnoteCitation, ...]


@dataclass(frozen=True)
class Article15Snapshot:
    """Metadata and items for a point-in-time Article 15 list."""

    edition_year: int
    as_of: str
    article: int
    law: str
    document_title: str
    baseline_source: Article15BaselineSource
    amendment_chain: tuple[Article15AmendmentCitation, ...]
    items: tuple[Article15Item, ...]


@dataclass(frozen=True)
class Article15ReviewedSource:
    """One pinned source reviewed for the Article 15 amendment chain."""

    id: str
    title: str
    corpus_file: str
    source_sha256: str
    source_pdf: str
    source_pdf_sha256: str
    source_url: str
    source_pages: tuple[int, ...]
    finding: str
    transcription_file: str | None
    transcription_sha256: str | None
    verified_quote: str | None


@dataclass(frozen=True)
class Article15SourceChainAudit:
    """Coverage and source-quality limits recorded by the source catalog."""

    status: str
    scope: str
    limitation: str
    reviewed_sources: tuple[Article15ReviewedSource, ...]


@dataclass(frozen=True)
class Article15Change:
    """Documented changes between the two Article 15 snapshots."""

    from_edition: int
    to_edition: int
    amending_law: str
    effective_from: str
    documented_changes: tuple[str, ...]
    source_citation: Article15AmendmentCitation
    limitation: str


@dataclass(frozen=True)
class Article15Catalog:
    """Top-level source and audit metadata for the historical catalog."""

    source_catalog: str
    law: str
    edition_basis: str
    date_semantics: str
    baseline_source_id: str
    source_chain_audit: Article15SourceChainAudit
    snapshots: tuple[Article15Snapshot, ...]
    changes: tuple[Article15Change, ...]


class UnsupportedArticle15SnapshotError(ValueError):
    """Raised when a requested Article 15 snapshot is not in the catalog."""


class Article15ItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the requested snapshot."""


ARTICLE_15_SNAPSHOT_YEARS = (2004, 2005)
ARTICLE_15_SNAPSHOT_DATES = ("2004-01-01", "2005-01-01")


def _load_source_data() -> dict:
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article15_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _amendment_citation(data: dict) -> Article15AmendmentCitation:
    if data.get("article_amended") != 15:
        raise ValueError("An amendment citation must identify Article 15")
    return Article15AmendmentCitation(
        law=data["law"],
        law_article=data["law_article"],
        article_amended=data["article_amended"],
        effective_from=data["effective_from"],
        corpus_file=data["corpus_file"],
        source_pdf=data["source_pdf"],
        source_pdf_sha256=data["source_pdf_sha256"],
        source_pdf_pages=tuple(data["source_pdf_pages"]),
        source_url=data["source_url"],
        source_quote=data["source_quote"],
        transcription_sha256=data["transcription_sha256"],
        quote_verification=data["quote_verification"],
    )


def _baseline_source(data: dict) -> Article15BaselineSource:
    return Article15BaselineSource(
        corpus_file=data["corpus_file"],
        source_sha256=data["source_sha256"],
        source_url=data["source_url"],
        source_pages=tuple(data["source_pages"]),
        retrieval_limitation=data["retrieval_limitation"],
    )


def _load_snapshot(data: dict) -> Article15Snapshot:
    edition_year = data["edition_year"]
    snapshot_date = data["as_of"]
    if data.get("article") != 15:
        raise ValueError("The packaged historical snapshot must be Article 15")
    if snapshot_date not in ARTICLE_15_SNAPSHOT_DATES:
        raise ValueError("An Article 15 snapshot has an unsupported as-of date")
    if {"effective_from", "valid_from", "valid_to"} & data.keys():
        raise ValueError("Snapshot metadata must not imply a validity interval")

    items = []
    seen_ids = set()
    for row in data["items"]:
        if row.get("edition_year") != edition_year or row.get("article") != 15:
            raise ValueError("An item is attached to the wrong Article 15 snapshot")
        if row.get("snapshot_date") != snapshot_date:
            raise ValueError("An item has a mismatched snapshot date")
        if {"valid_from", "valid_to"} & row.keys():
            raise ValueError("Snapshot items must not claim continuous validity")
        if row["item_id"] in seen_ids:
            raise ValueError("Duplicate item ID in an Article 15 snapshot")
        seen_ids.add(row["item_id"])

        conditions = tuple(
            Article15Condition(kind=item["kind"], quote=item["quote"])
            for item in (row.get("conditions") or ())
        )
        amendment_citations = tuple(
            _amendment_citation(item) for item in (row.get("amendment_citations") or ())
        )
        dgi_endnote_citations = tuple(
            Article15DGIEndnoteCitation(
                label=item["label"],
                corpus_file=item["corpus_file"],
                quote=item["quote"],
                source_sha256=item["source_sha256"],
            )
            for item in (row.get("dgi_endnote_citations") or ())
        )
        items.append(
            Article15Item(
                edition_year=edition_year,
                snapshot_date=snapshot_date,
                article=15,
                item_id=row["item_id"],
                rate=row["rate"],
                rate_context_quote=row["rate_context_quote"],
                item_type=row["item_type"],
                right_to_deduct=row.get("right_to_deduct"),
                quote=row["quote"],
                conditions=conditions,
                status=row["status"],
                corpus_file=row["corpus_file"],
                itemization=row["itemization"],
                source_sha256=row["source_sha256"],
                source_pages=tuple(row["source_pages"]),
                rate_context_corpus_file=row.get("rate_context_corpus_file"),
                amendment_citations=amendment_citations,
                dgi_endnote_citations=dgi_endnote_citations,
            )
        )

    if len(items) != data["item_count"]:
        raise ValueError("The Article 15 snapshot item count does not match its data")
    if not items:
        raise ValueError("An Article 15 snapshot must contain items")

    return Article15Snapshot(
        edition_year=edition_year,
        as_of=snapshot_date,
        article=15,
        law=data["law"],
        document_title=data["document_title"],
        baseline_source=_baseline_source(data["baseline_source"]),
        amendment_chain=tuple(
            _amendment_citation(item) for item in data["amendment_chain"]
        ),
        items=tuple(items),
    )


def _load_catalog(data: dict) -> Article15Catalog:
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported Article 15 catalog schema version")
    source = data["historical_article15_2004_2005"]
    if source.get("article") != 15:
        raise ValueError("The packaged source must be scoped to Article 15")
    if source.get("edition_basis") != (
        "pre-CGI statutory snapshots; not CGI Article 99 or LAR Article 101"
    ):
        raise ValueError("Article 15 snapshots must retain their pre-CGI scope")

    audit = source["source_chain_audit"]
    if audit.get("status") != "available_source_search_completed":
        raise ValueError(
            "The available-source Article 15 chain review must be explicit"
        )
    reviewed_sources = tuple(
        Article15ReviewedSource(
            id=item["id"],
            title=item["title"],
            corpus_file=item["corpus_file"],
            source_sha256=item["source_sha256"],
            source_pdf=item["source_pdf"],
            source_pdf_sha256=item["source_pdf_sha256"],
            source_url=item["source_url"],
            source_pages=tuple(item["source_pages"]),
            finding=item["finding"],
            transcription_file=item.get("transcription_file"),
            transcription_sha256=item.get("transcription_sha256"),
            verified_quote=item.get("verified_quote"),
        )
        for item in audit["reviewed_sources"]
    )
    if not reviewed_sources:
        raise ValueError("The Article 15 chain review must list its reviewed sources")
    snapshots = tuple(_load_snapshot(item) for item in source["snapshots"])
    years = tuple(item.edition_year for item in snapshots)
    dates = tuple(item.as_of for item in snapshots)
    if years != ARTICLE_15_SNAPSHOT_YEARS or dates != ARTICLE_15_SNAPSHOT_DATES:
        raise ValueError(
            "The catalog must contain the 2004 and 2005 snapshots in order"
        )

    changes = tuple(
        Article15Change(
            from_edition=item["from_edition"],
            to_edition=item["to_edition"],
            amending_law=item["amending_law"],
            effective_from=item["effective_from"],
            documented_changes=tuple(item["documented_changes"]),
            source_citation=_amendment_citation(item["source_citation"]),
            limitation=item["limitation"],
        )
        for item in source["changes"]
    )
    return Article15Catalog(
        source_catalog=data["source_catalog"],
        law=source["law"],
        edition_basis=source["edition_basis"],
        date_semantics=source["date_semantics"],
        baseline_source_id=source["baseline_source_id"],
        source_chain_audit=Article15SourceChainAudit(
            status=audit["status"],
            scope=audit["scope"],
            limitation=audit["limitation"],
            reviewed_sources=reviewed_sources,
        ),
        snapshots=snapshots,
        changes=changes,
    )


ARTICLE_15_CATALOG = _load_catalog(_load_source_data())
_SNAPSHOTS = {item.edition_year: item for item in ARTICLE_15_CATALOG.snapshots}
_ITEMS = {
    (snapshot.edition_year, item.item_id): item
    for snapshot in ARTICLE_15_CATALOG.snapshots
    for item in snapshot.items
}


def _require_supported_snapshot(edition_year: int) -> None:
    if isinstance(edition_year, bool) or not isinstance(edition_year, int):
        raise TypeError("edition_year must be an integer snapshot year")
    if edition_year not in _SNAPSHOTS:
        supported = ", ".join(
            f"{year} ({date})"
            for year, date in zip(ARTICLE_15_SNAPSHOT_YEARS, ARTICLE_15_SNAPSHOT_DATES)
        )
        raise UnsupportedArticle15SnapshotError(
            f"No Article 15 snapshot for {edition_year}; supported snapshots: {supported}"
        )


def get_article_15_snapshot(edition_year: int) -> Article15Snapshot:
    """Return one exact Article 15 snapshot and its source-chain metadata.

    ``edition_year`` selects a point-in-time source list. It is not a legal
    effective year, a continuous validity range, or a product classification.
    """
    _require_supported_snapshot(edition_year)
    return _SNAPSHOTS[edition_year]


def list_article_15_items(edition_year: int) -> tuple[Article15Item, ...]:
    """Return all quoted items in source order for one exact snapshot."""
    return get_article_15_snapshot(edition_year).items


def get_article_15_item(edition_year: int, item_id: str) -> Article15Item:
    """Return an exact item ID from one 2004 or 2005 snapshot.

    Args:
        edition_year: A supported point-in-time snapshot year.
        item_id: The exact item ID from that snapshot.

    Raises:
        TypeError: If the year is not an integer or the ID is not a string.
        ValueError: If the year is unsupported or the ID is empty.
        Article15ItemNotFoundError: If the ID is absent from that snapshot.
    """
    _require_supported_snapshot(edition_year)
    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string catalog ID")
    if not item_id:
        raise ValueError("item_id must not be empty")
    try:
        return _ITEMS[(edition_year, item_id)]
    except KeyError as error:
        raise Article15ItemNotFoundError(
            f"Article 15 item {item_id!r} is not present in the {edition_year} snapshot"
        ) from error


__all__ = [
    "ARTICLE_15_CATALOG",
    "ARTICLE_15_SNAPSHOT_DATES",
    "ARTICLE_15_SNAPSHOT_YEARS",
    "Article15AmendmentCitation",
    "Article15BaselineSource",
    "Article15Catalog",
    "Article15Change",
    "Article15Condition",
    "Article15DGIEndnoteCitation",
    "Article15Item",
    "Article15ItemNotFoundError",
    "Article15Snapshot",
    "Article15SourceChainAudit",
    "UnsupportedArticle15SnapshotError",
    "get_article_15_item",
    "get_article_15_snapshot",
    "list_article_15_items",
]
