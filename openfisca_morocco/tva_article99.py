"""Explicit lookup of documented CGI article 99 snapshot items.

This catalog is edition-scoped. It does not infer a rate from a product
description or treat a snapshot year as a continuous effective period.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from importlib import resources
from types import MappingProxyType


@dataclass(frozen=True)
class Article99Condition:
    """A verbatim condition attached to a catalog item."""

    kind: str
    quote: str


@dataclass(frozen=True)
class Article99AmendmentCitation:
    """A corpus endnote and the pinned finance-law text it identifies."""

    endnote: int
    endnote_label: str
    endnote_suffix: str
    law: str
    law_article: int
    budget_year: int
    source_edition: int
    corpus_file: str
    source_sha256: str
    quote: str
    amending_law_corpus_file: str
    amending_law_source_sha256: str
    amending_law_article_quote: str
    articles_mentioned: tuple[int, ...]
    source_scope: str


@dataclass(frozen=True)
class Article99Item:
    """A quoted Article 99 item from one consolidated text snapshot."""

    edition_year: int
    item_id: str
    rate: str
    corpus_file: str
    quote: str
    rate_context_quote: str
    item_type: str
    itemization: str
    right_to_deduct: bool | None
    status: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str
    document_title: str
    conditions: tuple[Article99Condition, ...]
    amendment_citations: tuple[Article99AmendmentCitation, ...]
    source_endnote_labels: tuple[str, ...] | None
    parent_context_item_id: str | None = None
    parent_context_quote: str | None = None


class UnsupportedArticle99EditionError(ValueError):
    """Raised when the requested consolidated Article 99 snapshot is absent."""


class Article99ItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the requested edition snapshot."""


class Article99TransitionalRateError(ValueError):
    """Raised when an item is subject to a separate transitional rate schedule."""


ARTICLE_99_SNAPSHOT_YEARS = (2007, 2010, 2014, 2018, 2021, 2024, 2026)


def _load_catalog():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article99_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


_CATALOG = _load_catalog()
_CATALOG_EDITION_YEARS = tuple(
    edition["edition_year"] for edition in _CATALOG["editions"]
)
if _CATALOG.get("article") != 99:
    raise ValueError("The packaged TVA catalog must be scoped to Article 99")
if _CATALOG_EDITION_YEARS != ARTICLE_99_SNAPSHOT_YEARS:
    raise ValueError(
        "The packaged Article 99 catalog editions do not match the supported snapshots"
    )
if not _CATALOG.get("unsupported_editions", {}).get("2004"):
    raise ValueError(
        "The packaged Article 99 catalog must retain the explicit 2004 gap"
    )

_ITEMS = {}
_EDITIONS = {edition["edition_year"]: edition for edition in _CATALOG["editions"]}
_ITEMS_BY_EDITION = {edition_year: [] for edition_year in _EDITIONS}

for _edition_year, _edition in _EDITIONS.items():
    if "as_of" in _edition or "snapshot_as_of" in _edition:
        raise ValueError(
            "Snapshot date markers must not be exposed as applicability dates"
        )
    for _row in _edition["items"]:
        if _row.get("article") != 99 or _row.get("edition_year") != _edition_year:
            raise ValueError("An Article 99 item is attached to the wrong edition")
        if {"valid_from", "valid_to"} & _row.keys():
            raise ValueError("Snapshot markers must not be exposed as validity periods")
        _item_key = (_edition_year, _row["item_id"])
        if _item_key in _ITEMS:
            raise ValueError("Duplicate Article 99 item ID in an edition snapshot")
        _conditions = tuple(
            Article99Condition(kind=condition["kind"], quote=condition["quote"])
            for condition in (_row.get("conditions") or ())
        )
        _amendment_citations = tuple(
            Article99AmendmentCitation(
                endnote=citation["endnote"],
                endnote_label=citation["endnote_label"],
                endnote_suffix=citation["endnote_suffix"],
                law=citation["law"],
                law_article=citation["law_article"],
                budget_year=citation["budget_year"],
                source_edition=citation["source_edition"],
                corpus_file=citation["corpus_file"],
                source_sha256=citation["source_sha256"],
                quote=citation["quote"],
                amending_law_corpus_file=citation["amending_law_corpus_file"],
                amending_law_source_sha256=citation["amending_law_source_sha256"],
                amending_law_article_quote=citation["amending_law_article_quote"],
                articles_mentioned=tuple(citation["articles_mentioned"]),
                source_scope=citation["source_scope"],
            )
            for citation in (_row.get("amendment_citations") or ())
        )
        _source_endnote_labels = _row.get("source_endnote_labels")
        _ITEMS[_item_key] = Article99Item(
            edition_year=_edition_year,
            item_id=_row["item_id"],
            rate=_row["rate"],
            corpus_file=_row["corpus_file"],
            quote=_row["quote"],
            rate_context_quote=_row["rate_context_quote"],
            item_type=_row["item_type"],
            itemization=_row["itemization"],
            right_to_deduct=_row.get("right_to_deduct"),
            status=_row["status"],
            source_pdf=_edition["source_pdf"],
            source_pdf_sha256=_edition["source_pdf_sha256"],
            source_text_sha256=_edition["source_text_sha256"],
            document_title=_edition["document_title"],
            conditions=_conditions,
            amendment_citations=_amendment_citations,
            source_endnote_labels=(
                tuple(_source_endnote_labels)
                if _source_endnote_labels is not None
                else None
            ),
            parent_context_item_id=_row.get("parent_context_item_id"),
            parent_context_quote=_row.get("parent_context_quote"),
        )
        _ITEMS_BY_EDITION[_edition_year].append(_ITEMS[_item_key])


def _require_supported_edition(edition_year: int) -> None:
    if isinstance(edition_year, bool) or not isinstance(edition_year, int):
        raise TypeError("edition_year must be an integer snapshot year")

    if edition_year in _EDITIONS:
        return

    supported_years = ", ".join(str(year) for year in ARTICLE_99_SNAPSHOT_YEARS)
    if edition_year == 2004:
        reason = _CATALOG["unsupported_editions"]["2004"]
        message = f"No consolidated Article 99 snapshot exists for 2004: {reason}"
    else:
        message = (
            f"No Article 99 snapshot for {edition_year}; supported editions: "
            f"{supported_years}"
        )
    raise UnsupportedArticle99EditionError(message)


def list_article_99_items(edition_year: int) -> tuple[Article99Item, ...]:
    """Return all quoted items from one exact Article 99 snapshot.

    Items remain in source order. The edition year is a consolidated-text
    snapshot label, not a legal effective date or a product classification.
    """
    _require_supported_edition(edition_year)
    return tuple(_ITEMS_BY_EDITION[edition_year])


def get_article_99_item(edition_year: int, item_id: str) -> Article99Item:
    """Return one exact item from a requested Article 99 snapshot.

    Args:
        edition_year: A supported consolidated snapshot year. This is not an
            effective year and is never matched to a nearest edition.
        item_id: The exact catalog ID from that edition.

    Raises:
        TypeError: If ``edition_year`` is not an integer or ``item_id`` is not
            a string.
        ValueError: If ``item_id`` is empty or the edition is unsupported.
        Article99ItemNotFoundError: If the exact ID is not present in that
            edition.
    """
    _require_supported_edition(edition_year)
    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string catalog ID")
    if not item_id:
        raise ValueError("item_id must not be empty")

    try:
        return _ITEMS[(edition_year, item_id)]
    except KeyError as error:
        raise Article99ItemNotFoundError(
            f"Article 99 item {item_id!r} is not present in the {edition_year} snapshot"
        ) from error


def aggregate_article_99_turnover(
    edition_year: int,
    turnover_by_item_id: Mapping[str, int | float | Decimal],
) -> Mapping[str, Decimal]:
    """Sum taxable bases by rate for caller-selected Article 99 item IDs.

    This is an explicit category-to-rate mapping, not a product-description
    classifier. A caller must first select the exact legal item ID for each
    transaction. Items that cite a separate Article 247 transitional schedule
    are rejected; declare those through the model's transitional-operation
    input instead.

    Args:
        edition_year: One supported consolidated Article 99 snapshot year.
        turnover_by_item_id: Exact catalog IDs mapped to their non-negative
            taxable bases in MAD.

    Returns:
        An immutable mapping from rate labels such as ``"10%"`` to summed
        taxable bases as ``Decimal`` values.
    """
    _require_supported_edition(edition_year)
    if not isinstance(turnover_by_item_id, Mapping):
        raise TypeError("turnover_by_item_id must be a mapping of item IDs to bases")

    totals: dict[str, Decimal] = {}
    for item_id, base in turnover_by_item_id.items():
        item = get_article_99_item(edition_year, item_id)
        if item.status != "in_force_in_snapshot":
            raise ValueError(
                f"Article 99 item {item_id!r} is not in force in the snapshot"
            )
        source_text = " ".join(
            (
                item.quote,
                item.rate_context_quote,
                item.parent_context_quote or "",
                *(condition.quote for condition in item.conditions),
            )
        ).casefold()
        if "247" in source_text or "xxxxi" in source_text:
            raise Article99TransitionalRateError(
                f"Article 99 item {item_id!r} cites a transitional schedule; "
                "use tva_operation_transitoire"
            )
        if not isinstance(base, (int, float, Decimal)) or isinstance(base, bool):
            raise TypeError(f"Turnover base for {item_id!r} must be numeric")
        try:
            normalized_base = Decimal(str(base))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise TypeError(f"Turnover base for {item_id!r} must be numeric") from error
        if not normalized_base.is_finite() or normalized_base < 0:
            raise ValueError(
                f"Turnover base for {item_id!r} must be finite and non-negative"
            )
        if not item.rate.endswith("%"):
            raise ValueError(f"Article 99 item {item_id!r} has no percentage rate")
        totals[item.rate] = totals.get(item.rate, Decimal(0)) + normalized_base

    return MappingProxyType(totals)


__all__ = [
    "ARTICLE_99_SNAPSHOT_YEARS",
    "Article99AmendmentCitation",
    "Article99Condition",
    "Article99Item",
    "Article99ItemNotFoundError",
    "Article99TransitionalRateError",
    "UnsupportedArticle99EditionError",
    "aggregate_article_99_turnover",
    "get_article_99_item",
    "list_article_99_items",
]
