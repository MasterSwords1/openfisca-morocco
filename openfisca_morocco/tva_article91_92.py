"""Quote-backed, snapshot-scoped lookups for CGI TVA Articles 91 and 92.

Article 91 lists exemptions without a right to deduct; Article 92 lists
exemptions with a right to deduct. This module exposes the exact rows of the
available consolidated snapshots at two levels:

* :func:`list_article_91_items` / :func:`list_article_92_items` return the
  article-level context and the numbered clauses, addressed by their corpus item
  ID;
* :func:`list_article_91_subitems` / :func:`list_article_92_subitems` return the
  nested bullets and letters printed *beneath* a clause, each linked to its
  parent by ``parent_item_id``.

Neither level classifies a product description, and no row claims that snapshot
contents remained unchanged between editions. A row's ``status`` is the one the
consolidated text prints, so ``abrogated`` rows are retained rather than
silently dropped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources

ARTICLE_91_92_CATALOG_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class TVAExemptionItem:
    """A quoted exemption row in one exact CGI snapshot.

    For a numbered clause or the article-level context, ``item_id`` is the
    corpus item ID and ``parent_item_id`` is ``None``. For a nested bullet or
    letter, ``item_id`` is the packaged stable ID, ``source_item_id`` is the
    corpus ID it came from, and ``parent_item_id`` names the clause it sits
    under.
    """

    article: int
    edition_year: int
    snapshot_date: str
    item_id: str
    source_item_id: str
    parent_item_id: str | None
    parent_source_item_id: str | None
    rate: str
    rate_context_quote: str
    subsection_context_quote: str | None
    parent_context_quote: str | None
    right_to_deduct: bool
    quote: str
    status: str
    itemization: str
    item_role: str | None
    nesting_depth: int
    source_marker: str | None
    source_marker_type: str | None
    clause_number: int | None
    corpus_file: str
    document_title: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str

    @property
    def is_subitem(self) -> bool:
        """Whether this row is a nested bullet or letter beneath a clause."""
        return self.parent_item_id is not None

    @property
    def is_abrogated(self) -> bool:
        """Whether the consolidated text prints this row as ``(abrogé)``."""
        return self.status == "abrogated"


class UnsupportedTVAExemptionEditionError(ValueError):
    """Raised when an Article 91/92 consolidated snapshot is unavailable."""


class TVAExemptionItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the requested article snapshot."""


_ITEM_STATUSES = ("in_force_in_snapshot", "abrogated")
_CORE_ITEMIZATIONS = ("article_level", "numbered_clause")
_NESTED_ITEMIZATIONS = ("nested_bullet", "nested_letter")


def _load_source_data() -> dict:
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article91_92_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _build_row(
    row: dict, article: int, year: int, edition: dict, *, nested: bool
) -> TVAExemptionItem:
    if row.get("article") != article:
        raise ValueError("An exemption item is attached to the wrong article")
    if row.get("edition_year") != year:
        raise ValueError("An exemption item is attached to the wrong edition")
    if {"valid_from", "valid_to", "as_of"} & row.keys():
        raise ValueError("Snapshot items must not claim continuous validity")
    if row.get("rate") != "exempt":
        raise ValueError("An Article 91/92 item must retain its exempt status")
    if row.get("status") not in _ITEM_STATUSES:
        raise ValueError("An exemption item has an unsupported snapshot status")
    expected_right_to_deduct = article == 92
    if row.get("right_to_deduct") is not expected_right_to_deduct:
        raise ValueError("An exemption item's deduction treatment is inconsistent")

    if nested:
        if row.get("itemization") not in _NESTED_ITEMIZATIONS:
            raise ValueError("A sub-item must be a nested bullet or letter")
        if not row.get("parent_item_id"):
            raise ValueError("A sub-item must name its parent clause")
        if not isinstance(row.get("nesting_depth"), int) or row["nesting_depth"] < 1:
            raise ValueError("A sub-item must sit at nesting depth 1 or deeper")
        if row.get("item_id") == row.get("source_item_id"):
            raise ValueError("A sub-item must carry a distinct packaged ID")
    else:
        if row.get("itemization") not in _CORE_ITEMIZATIONS:
            raise ValueError("A top-level exemption row has an unknown itemization")
        if row.get("parent_item_id") is not None:
            raise ValueError("A top-level exemption row must not name a parent")
        if row.get("item_id") != row.get("source_item_id"):
            raise ValueError("A top-level row must keep its corpus item ID")
        if row.get("nesting_depth") != 0:
            raise ValueError("A top-level row must sit at nesting depth 0")

    return TVAExemptionItem(
        article=article,
        edition_year=year,
        snapshot_date=edition["snapshot_date"],
        item_id=row["item_id"],
        source_item_id=row["source_item_id"],
        parent_item_id=row.get("parent_item_id"),
        parent_source_item_id=row.get("parent_source_item_id"),
        rate=row["rate"],
        rate_context_quote=row["rate_context_quote"],
        subsection_context_quote=row.get("subsection_context_quote"),
        parent_context_quote=row.get("parent_context_quote"),
        right_to_deduct=row["right_to_deduct"],
        quote=row["quote"],
        status=row["status"],
        itemization=row["itemization"],
        item_role=row.get("item_role"),
        nesting_depth=row["nesting_depth"],
        source_marker=row.get("source_marker"),
        source_marker_type=row.get("source_marker_type"),
        clause_number=row.get("clause_number"),
        corpus_file=row["corpus_file"],
        document_title=edition["document_title"],
        source_pdf=edition["source_pdf"],
        source_pdf_sha256=edition["source_pdf_sha256"],
        source_text_sha256=edition["source_text_sha256"],
    )


def _load_catalog(data: dict) -> tuple[dict, dict]:
    if data.get("schema_version") != ARTICLE_91_92_CATALOG_SCHEMA_VERSION:
        raise ValueError(
            "The packaged exemption catalog must use schema version "
            f"{ARTICLE_91_92_CATALOG_SCHEMA_VERSION}"
        )
    if data.get("articles") != [91, 92]:
        raise ValueError("The packaged exemption catalog must cover Articles 91 and 92")
    if "valid_from" in data or "valid_to" in data:
        raise ValueError("Snapshot metadata must not claim continuous validity")

    catalog: dict = {}
    subcatalog: dict = {}
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
                item = _build_row(row, article, year, edition, nested=False)
                if item.item_id in seen_ids:
                    raise ValueError("Duplicate item ID in an exemption snapshot")
                seen_ids.add(item.item_id)
                items.append(item)
            if not items:
                raise ValueError(f"The {year} Article {article} snapshot is empty")

            subitems = []
            for row in edition.get("subitems", ()):
                if row.get("article") != article:
                    continue
                item = _build_row(row, article, year, edition, nested=True)
                if item.item_id in seen_ids:
                    raise ValueError("Duplicate item ID in an exemption snapshot")
                seen_ids.add(item.item_id)
                if item.parent_item_id not in {parent.item_id for parent in items} | {
                    child.item_id for child in subitems
                }:
                    raise ValueError(
                        "A sub-item must name a parent that precedes it in source order"
                    )
                subitems.append(item)

            catalog[(year, article)] = tuple(items)
            subcatalog[(year, article)] = tuple(subitems)

    expected_years = (2007, 2010, 2014, 2018, 2021, 2024, 2026)
    if tuple(years) != expected_years:
        raise ValueError(
            "The exemption catalog editions do not match supported snapshots"
        )
    return catalog, subcatalog


_CATALOG, _SUBCATALOG = _load_catalog(_load_source_data())
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
    """Return the article-level row and numbered clauses for one snapshot.

    The source-level article context row comes first, followed by numbered
    clauses in source order, including the clauses the consolidated text prints
    as ``(abrogé)``. Nested bullets and letters are returned by
    :func:`list_tva_exemption_subitems`; they are not flattened into a parent
    quote.
    """
    _validate_edition_year(edition_year)
    _validate_article(article)
    return _CATALOG[(edition_year, article)]


def list_tva_exemption_subitems(
    edition_year: int, article: int
) -> tuple[TVAExemptionItem, ...]:
    """Return the nested bullets and letters printed beneath a clause.

    Each row names the clause it belongs to through ``parent_item_id``. An empty
    tuple means the source prints no nested sub-items for that article in that
    edition; it does not mean the edition is missing.
    """
    _validate_edition_year(edition_year)
    _validate_article(article)
    return _SUBCATALOG[(edition_year, article)]


def get_tva_exemption_item(
    edition_year: int, article: int, item_id: str
) -> TVAExemptionItem:
    """Return one exact exemption row from the requested snapshot."""
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


def get_tva_exemption_subitem(
    edition_year: int, article: int, item_id: str
) -> TVAExemptionItem:
    """Return one exact nested exemption sub-item from the requested snapshot."""
    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string catalog ID")
    if not item_id:
        raise ValueError("item_id must not be empty")
    for item in list_tva_exemption_subitems(edition_year, article):
        if item.item_id == item_id:
            return item
    raise TVAExemptionItemNotFoundError(
        f"Article {article} sub-item {item_id!r} is not in the {edition_year} snapshot"
    )


def list_article_91_items(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the Article 91 exemptions without a right to deduct."""
    return list_tva_exemption_items(edition_year, 91)


def list_article_92_items(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the Article 92 exemptions with a right to deduct."""
    return list_tva_exemption_items(edition_year, 92)


def list_article_91_subitems(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the nested sub-items of the Article 91 snapshot."""
    return list_tva_exemption_subitems(edition_year, 91)


def list_article_92_subitems(edition_year: int) -> tuple[TVAExemptionItem, ...]:
    """Return the nested sub-items of the Article 92 snapshot."""
    return list_tva_exemption_subitems(edition_year, 92)


def get_article_91_item(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact Article 91 item."""
    return get_tva_exemption_item(edition_year, 91, item_id)


def get_article_92_item(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact Article 92 item."""
    return get_tva_exemption_item(edition_year, 92, item_id)


def get_article_91_subitem(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact nested Article 91 sub-item."""
    return get_tva_exemption_subitem(edition_year, 91, item_id)


def get_article_92_subitem(edition_year: int, item_id: str) -> TVAExemptionItem:
    """Return one exact nested Article 92 sub-item."""
    return get_tva_exemption_subitem(edition_year, 92, item_id)


__all__ = [
    "ARTICLE_91_92_CATALOG_SCHEMA_VERSION",
    "ARTICLE_91_92_SNAPSHOT_YEARS",
    "ARTICLE_91_SNAPSHOT_YEARS",
    "ARTICLE_92_SNAPSHOT_YEARS",
    "TVAExemptionItem",
    "TVAExemptionItemNotFoundError",
    "UnsupportedTVAExemptionEditionError",
    "get_article_91_item",
    "get_article_91_subitem",
    "get_article_92_item",
    "get_article_92_subitem",
    "get_tva_exemption_item",
    "get_tva_exemption_subitem",
    "list_article_91_items",
    "list_article_91_subitems",
    "list_article_92_items",
    "list_article_92_subitems",
    "list_tva_exemption_items",
    "list_tva_exemption_subitems",
]
