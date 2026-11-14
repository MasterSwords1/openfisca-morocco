"""Explicit lookup of the 2006 LAR Article 101 snapshot.

This historical snapshot is from the Livre d'Assiette et de Recouvrement
(LAR), not a CGI Article 99 edition. It does not represent the missing
2004–2005 Article 15 product lists or imply continuous validity after 2006.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class Article101Condition:
    """A verbatim condition attached to a 2006 LAR Article 101 item."""

    kind: str
    quote: str


@dataclass(frozen=True)
class Article101SourceCitation:
    """A quoted legal citation in the 2006 LAR snapshot."""

    article: int
    source_page: int
    corpus_file: str
    quote: str


@dataclass(frozen=True)
class LAR2006Article101Item:
    """A quoted item from LAR Article 101 as published for 2006."""

    edition_year: int
    article: int
    item_id: str
    rate: str
    rate_context_quote: str
    item_type: str
    right_to_deduct: bool | None
    quote: str
    conditions: tuple[Article101Condition, ...]
    status: str
    corpus_file: str
    itemization: str
    document_title: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str
    source_url: str
    retrieval_url: str
    source_pages: tuple[int, ...]


@dataclass(frozen=True)
class LAR2006Article101Snapshot:
    """Source and applicability metadata for the distinct 2006 LAR snapshot."""

    edition_year: int
    article: int
    document_title: str
    effective_from: str
    effective_date_citation: Article101SourceCitation
    predecessor_repeal_citation: Article101SourceCitation
    corpus_file: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str
    source_url: str
    retrieval_url: str
    retrieval_note: str
    publisher: str
    source_pdf_bytes: int
    source_pdf_page_count: int
    source_printed_folio_total: int
    source_text_bytes: int
    source_pages: tuple[int, ...]
    items: tuple[LAR2006Article101Item, ...]


class LAR2006Article101ItemNotFoundError(LookupError):
    """Raised when an exact item ID is absent from the 2006 LAR snapshot."""


def _load_source_data() -> dict:
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_lar_2006_article101.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _citation(data: dict) -> Article101SourceCitation:
    return Article101SourceCitation(
        article=data["article"],
        source_page=data["source_page"],
        corpus_file=data["corpus_file"],
        quote=data["quote"],
    )


def _load_snapshot(data: dict) -> LAR2006Article101Snapshot:
    if data.get("edition_year") != 2006 or data.get("article") != 101:
        raise ValueError("The packaged source must be the 2006 LAR Article 101")
    if (
        len(data.get("source_pdf_sha256", "")) != 64
        or len(data.get("source_text_sha256", "")) != 64
    ):
        raise ValueError("The packaged 2006 source must retain both SHA-256 hashes")

    items = []
    seen_ids = set()
    for row in data["items"]:
        if row.get("edition_year") != 2006 or row.get("article") != 101:
            raise ValueError("A packaged item is outside the 2006 LAR Article 101")
        if {"valid_from", "valid_to", "as_of"} & row.keys():
            raise ValueError("Snapshot items must not claim continuous validity")
        if row["item_id"] in seen_ids:
            raise ValueError("Duplicate item ID in the 2006 LAR Article 101 snapshot")
        seen_ids.add(row["item_id"])
        conditions = tuple(
            Article101Condition(kind=item["kind"], quote=item["quote"])
            for item in (row.get("conditions") or ())
        )
        items.append(
            LAR2006Article101Item(
                edition_year=2006,
                article=101,
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
                document_title=data["document_title"],
                source_pdf=data["source_pdf"],
                source_pdf_sha256=data["source_pdf_sha256"],
                source_text_sha256=data["source_text_sha256"],
                source_url=data["source_url"],
                retrieval_url=data["retrieval_url"],
                source_pages=tuple(data["source_pages"]),
            )
        )

    if not items:
        raise ValueError("The packaged 2006 LAR Article 101 snapshot is empty")

    return LAR2006Article101Snapshot(
        edition_year=2006,
        article=101,
        document_title=data["document_title"],
        effective_from=data["effective_from"],
        effective_date_citation=_citation(data["effective_date_citation"]),
        predecessor_repeal_citation=_citation(data["predecessor_repeal_citation"]),
        corpus_file=data["corpus_file"],
        source_pdf=data["source_pdf"],
        source_pdf_sha256=data["source_pdf_sha256"],
        source_text_sha256=data["source_text_sha256"],
        source_url=data["source_url"],
        retrieval_url=data["retrieval_url"],
        retrieval_note=data["retrieval_note"],
        publisher=data["publisher"],
        source_pdf_bytes=data["source_pdf_bytes"],
        source_pdf_page_count=data["source_pdf_page_count"],
        source_printed_folio_total=data["source_printed_folio_total"],
        source_text_bytes=data["source_text_bytes"],
        source_pages=tuple(data["source_pages"]),
        items=tuple(items),
    )


LAR_2006_ARTICLE_101_SNAPSHOT = _load_snapshot(_load_source_data())


def get_lar_2006_article_101_snapshot() -> LAR2006Article101Snapshot:
    """Return source metadata and all items for the exact LAR 2006 snapshot.

    The date and item coverage describe this source snapshot only. They do not
    fill the 2004–2005 Article 15 gap or define a continuous validity interval.
    """
    return LAR_2006_ARTICLE_101_SNAPSHOT


def list_lar_2006_article_101_items() -> tuple[LAR2006Article101Item, ...]:
    """Return the 38 quoted items in their source order."""
    return LAR_2006_ARTICLE_101_SNAPSHOT.items


def get_lar_2006_article_101_item(item_id: str) -> LAR2006Article101Item:
    """Return one exact item from LAR Article 101's 2006 snapshot.

    Args:
        item_id: The exact catalog ID from the 2006 snapshot.

    Raises:
        TypeError: If ``item_id`` is not a string.
        ValueError: If ``item_id`` is empty.
        LAR2006Article101ItemNotFoundError: If the ID is not in the snapshot.
    """
    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string catalog ID")
    if not item_id:
        raise ValueError("item_id must not be empty")

    for item in LAR_2006_ARTICLE_101_SNAPSHOT.items:
        if item.item_id == item_id:
            return item
    raise LAR2006Article101ItemNotFoundError(
        f"LAR Article 101 item {item_id!r} is not in the 2006 snapshot"
    )


__all__ = [
    "LAR_2006_ARTICLE_101_SNAPSHOT",
    "Article101Condition",
    "Article101SourceCitation",
    "LAR2006Article101Item",
    "LAR2006Article101ItemNotFoundError",
    "LAR2006Article101Snapshot",
    "get_lar_2006_article_101_item",
    "get_lar_2006_article_101_snapshot",
    "list_lar_2006_article_101_items",
]
