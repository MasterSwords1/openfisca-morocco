"""Quote-backed, snapshot-scoped lookups for CGI TVA Articles 91 and 92.

Article 91 lists exemptions without a right to deduct; Article 92 lists
exemptions with a right to deduct. This module exposes the exact numbered
clauses from the available consolidated snapshots. It does not classify
product descriptions or claim that snapshot contents remained unchanged
between editions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class TVAExemptionItem:
    """A quoted exemption clause in one exact CGI snapshot."""

    article: int
    edition_year: int
    snapshot_date: str
    item_id: str
    rate: str
    rate_context_quote: str
    subsection_context_quote: str | None
    right_to_deduct: bool
    quote: str
    status: str
    itemization: str
    clause_number: int | None
    corpus_file: str
    document_title: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str


class UnsupportedTVAExemptionEditionError(ValueError):
    """Raised when an Article 91/92 consolidated snapshot is unavailable."""


class TVAExemptionItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the requested article snapshot."""


def _load_source_data() -> dict:
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article91_92_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _load_catalog(data: dict) -> dict:
    if data.get("schema_version") != 1 or data.get("articles") != [91, 92]:
        raise ValueError("The packaged exemption catalog must cover Articles 91 and 92")
    if "valid_from" in data or "valid_to" in data:
        raise ValueError("Snapshot metadata must not claim continuous validity")

    catalog = {}
    years = []
    for edition in data["editions"]:
        year = edition["edition_year"]
        if year in years:
            raise ValueError("Duplicate year in the Article 91/92 snapshot catalog")
        years.append(year)
        if edition.get("snapshot_date") != f"{year}-01-01":
            raise ValueError("An exemption edition has an unsupported snapshot date")
        if {"valid_from", "valid_to", "as_of"} & edition.keys():
            raise ValueError("Snapshot editions must not imply continuous validity")
        if (
            len(edition.get("source_pdf_sha256", "")) != 64
            or len(edition.get("source_text_sha256", "")) != 64
        ):
            raise ValueError("Each exemption snapshot must retain both source hashes")

        for article in (91, 92):
            items = []
            seen_ids = set()
            for row in edition["items"]:
                if row.get("article") != article:
                    continue
                if row.get("edition_year") != year:
                    raise ValueError(
                        "An exemption item is attached to the wrong edition"
                    )
                if {"valid_from", "valid_to", "as_of"} & row.keys():
                    raise ValueError(
                        "Snapshot items must not claim continuous validity"
                    )
                if row["item_id"] in seen_ids:
                    raise ValueError("Duplicate item ID in an exemption snapshot")
                seen_ids.add(row["item_id"])
                expected_right_to_deduct = article == 92
                if row.get("right_to_deduct") is not expected_right_to_deduct:
                    raise ValueError(
                        "An exemption item's deduction treatment is inconsistent"
                    )
                if row.get("rate") != "exempt":
                    raise ValueError(
                        "An Article 91/92 item must retain its exempt status"
                    )
                if row.get("status") != "in_force_in_snapshot":
                    raise ValueError(
                        "An exemption item has an unsupported snapshot status"
                    )
                items.append(
                    TVAExemptionItem(
                        article=article,
                        edition_year=year,
                        snapshot_date=edition["snapshot_date"],
                        item_id=row["item_id"],
                        rate=row["rate"],
                        rate_context_quote=row["rate_context_quote"],
                        subsection_context_quote=row.get("subsection_context_quote"),
                        right_to_deduct=row["right_to_deduct"],
                        quote=row["quote"],
                        status=row["status"],
                        itemization=row["itemization"],
                        clause_number=row.get("clause_number"),
                        corpus_file=row["corpus_file"],
                        document_title=edition["document_title"],
                        source_pdf=edition["source_pdf"],
                        source_pdf_sha256=edition["source_pdf_sha256"],
                        source_text_sha256=edition["source_text_sha256"],
                    )
                )
            if not items:
                raise ValueError(f"The {year} Article {article} snapshot is empty")
            catalog[(year, article)] = tuple(items)

    expected_years = (2007, 2010, 2014, 2018, 2021, 2024, 2026)
    if tuple(years) != expected_years:
        raise ValueError(
            "The exemption catalog editions do not match supported snapshots"
        )
    return catalog


_CATALOG = _load_catalog(_load_source_data())
ARTICLE_91_92_SNAPSHOT_YEARS = tuple(year for year, _ in _CATALOG if _ == 91)
ARTICLE_91_SNAPSHOT_YEARS = ARTICLE_91_92_SNAPSHOT_YEARS
ARTICLE_92_SNAPSHOT_YEARS = ARTICLE_91_92_SNAPSHOT_YEARS


def _validate_edition_year(edition_year: int) -> None:
    if not isinstance(edition_year, int) or isinstance(edition_year, bool):
        raise TypeError("edition_year must be an integer snapshot year")
    if edition_year not in ARTICLE_91_92_SNAPSHOT_YEARS:
        years = ", ".join(str(year) for year in ARTICLE_91_92_SNAPSHOT_YEARS)
        raise UnsupportedTVAExemptionEditionError(
            f"No Article 91/92 snapshot for {edition_year}; supported editions: {years}"
        )


def _validate_article(article: int) -> None:
    if not isinstance(article, int) or isinstance(article, bool):
        raise TypeError("article must be integer 91 or 92")
    if article not in (91, 92):
        raise ValueError("article must be 91 or 92")


def list_tva_exemption_items(
    edition_year: int, article: int
) -> tuple[TVAExemptionItem, ...]:
    """Return all quoted rows for one exact Article 91 or 92 snapshot.

    The source-level article context row comes first, followed by numbered
    clauses in source order. Nested bullets and combined subclauses are quoted
    as they appear in the source catalog and are not expanded into new legal
    categories.
    """
    _validate_edition_year(edition_year)
    _validate_article(article)
    return _CATALOG[(edition_year, article)]


def get_tva_exemption_item(
    edition_year: int, article: int, item_id: str
) -> TVAExemptionItem:
    """Return one exact exemption item from the requested snapshot."""
    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string catalog ID")
    if not item_id:
        raise ValueError("item_id must not be empty")
    for item in list_tva_exemption_items(edition_year, article):
        if item.item_id == item_id:
            return item
    raise TVAExemptionItemNotFoundError(
        f"Article {article} item {item_id!r} is not in the {edition_year} snapshot"
    )


def list_article_91_items(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the Article 91 exemptions without a right to deduct."""
    return list_tva_exemption_items(edition_year, 91)


def get_article_91_item(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact Article 91 item."""
    return get_tva_exemption_item(edition_year, 91, item_id)


def list_article_92_items(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the Article 92 exemptions with a right to deduct."""
    return list_tva_exemption_items(edition_year, 92)


def get_article_92_item(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact Article 92 item."""
    return get_tva_exemption_item(edition_year, 92, item_id)


__all__ = [
    "ARTICLE_91_92_SNAPSHOT_YEARS",
    "ARTICLE_91_SNAPSHOT_YEARS",
    "ARTICLE_92_SNAPSHOT_YEARS",
    "TVAExemptionItem",
    "TVAExemptionItemNotFoundError",
    "UnsupportedTVAExemptionEditionError",
    "get_article_91_item",
    "get_article_92_item",
    "get_tva_exemption_item",
    "list_article_91_items",
    "list_article_92_items",
    "list_tva_exemption_items",
]
