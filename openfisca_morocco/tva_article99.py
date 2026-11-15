"""Explicit lookup of documented CGI article 99 snapshot items.

This catalog is edition-scoped. It does not infer a rate from a product
description or treat a snapshot year as a continuous effective period.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
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
class Article99Instrument:
    """One amending instrument, defined once for the whole catalog.

    ``date_basis`` records why the effective date is what it is, so a consumer
    can tell an explicit ``à compter du 1er janvier`` clause from the
    budget-year default.
    """

    key: str
    law: str
    law_article: int
    budget_year: int
    effective_from: date
    date_basis: str
    bo: str | None
    bo_date: date | None
    date_witness_kind: str
    date_witness_file: str
    date_witness_text_sha256: str
    date_witness_quote: str
    date_witness_note: str | None


@dataclass(frozen=True)
class Article99EffectiveBoundary:
    """One end of a dated segment: witnessed, or an explicit bracket.

    A ``proven`` boundary either carries ``valid_date`` or, for the open end of
    a segment that is still in force at the last snapshot, ``still_in_force_at``.
    """

    status: str
    method: str | None
    valid_date: date | None
    still_in_force_at: date | None
    instrument: Article99Instrument | None
    witness_kind: str | None
    witness_file: str | None
    witness_pdf_sha256: str | None
    witness_text_sha256: str | None
    witness_endnote: int | None
    witness_quote: str | None
    derivation: str | None
    bracket_earliest: date | None
    bracket_latest: date | None
    reason: str | None
    effect: str | None
    successor_article: int | None

    @property
    def is_open_ended(self) -> bool:
        return self.valid_date is None and self.still_in_force_at is not None


@dataclass(frozen=True)
class Article99Attribution:
    """The dated segment a snapshot row belongs to.

    ``status`` is ``"proven"`` only when both ends are witnessed. The two ends
    are kept apart rather than collapsed into one interval, so a row can expose
    a proven ``valid_from`` while its repeal date is still bracketed.
    """

    status: str
    first_anchor: int
    last_anchor: int
    rate: str
    start: Article99EffectiveBoundary
    end: Article99EffectiveBoundary

    @property
    def valid_from(self) -> date | None:
        """The first day the segment applied, if it is witnessed."""
        return self.start.valid_date

    @property
    def valid_to(self) -> date | None:
        """The first day of the successor text, exclusive, if witnessed."""
        return self.end.valid_date

    @property
    def still_in_force_at(self) -> date | None:
        """The last date this catalog can confirm for an open-ended segment."""
        return self.end.still_in_force_at

    def covers(self, on_date: date) -> bool:
        """Return whether this segment is proven to cover ``on_date``."""
        if not isinstance(on_date, date) or isinstance(on_date, datetime):
            raise TypeError("on_date must be a datetime.date")
        if self.status != "proven" or self.valid_from is None:
            return False
        if on_date < self.valid_from:
            return False
        if self.valid_to is not None:
            return on_date < self.valid_to
        horizon = self.end.still_in_force_at
        return horizon is not None and on_date <= horizon


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
    effective_attribution: Article99Attribution | None = None


class UnsupportedArticle99EditionError(ValueError):
    """Raised when the requested consolidated Article 99 snapshot is absent."""


class Article99ItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the requested edition snapshot."""


class Article99TransitionalRateError(ValueError):
    """Raised when an item is subject to a separate transitional rate schedule."""


class Article99UndatedItemError(ValueError):
    """Raised when a date query reaches an item whose dates are not proven."""


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

_ATTRIBUTION_METHODS = frozenset(
    {"verbatim_reproduction", "positional_abrogation", "consolidated_endnote"}
)
_ATTRIBUTION_STATUSES = frozenset({"proven", "bracketed"})
_DATE_BASES = frozenset(
    {"explicit_in_article", "budget_year_default", "original_enactment"}
)
_WITNESS_KINDS_WITH_PDF = frozenset(
    {"consolidated_edition", "consolidated_endnote", "bulletin_officiel"}
)


def _iso_date(value, field: str) -> date:
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        raise ValueError(f"{field} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} is not a real calendar date") from error


def _optional_iso_date(value, field: str) -> date | None:
    return None if value is None else _iso_date(value, field)


def _hex64(value, field: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise ValueError(f"{field} must be a 64-character lowercase SHA-256")
    return value


def _load_instruments(catalog) -> Mapping[str, Article99Instrument]:
    raw = catalog.get("instruments")
    if not isinstance(raw, Mapping) or not raw:
        raise ValueError("The Article 99 catalog must define its instruments once")
    instruments = {}
    for key, row in raw.items():
        witness = row.get("date_witness") or {}
        basis = row.get("date_basis")
        if basis not in _DATE_BASES:
            raise ValueError(f"Instrument {key!r} has an unknown date basis")
        instruments[key] = Article99Instrument(
            key=key,
            law=row["law"],
            law_article=row["law_article"],
            budget_year=row["budget_year"],
            effective_from=_iso_date(row["effective_from"], f"{key}.effective_from"),
            date_basis=basis,
            bo=row.get("bo"),
            bo_date=_optional_iso_date(row.get("bo_date"), f"{key}.bo_date"),
            date_witness_kind=witness["kind"],
            date_witness_file=witness["file"],
            date_witness_text_sha256=_hex64(
                witness["text_sha256"], f"{key}.date_witness.text_sha256"
            ),
            date_witness_quote=witness["quote"],
            date_witness_note=witness.get("note"),
        )
    return MappingProxyType(instruments)


def _boundary(
    part, side: str, instruments: Mapping[str, Article99Instrument]
) -> Article99EffectiveBoundary:
    """Validate one end of a segment and build its dataclass."""
    if not isinstance(part, Mapping):
        raise TypeError(f"The {side} boundary must be a mapping")
    status = part.get("status")
    if status not in _ATTRIBUTION_STATUSES:
        raise ValueError(f"The {side} boundary has an unknown status")

    if status == "bracketed":
        if {"valid_from", "valid_to"} & part.keys():
            raise ValueError(f"A bracketed {side} boundary must not carry a date")
        bracket = part.get("validity_bracket") or {}
        earliest = _iso_date(
            bracket.get("earliest"), f"{side}.validity_bracket.earliest"
        )
        latest = _iso_date(bracket.get("latest"), f"{side}.validity_bracket.latest")
        if not earliest < latest:
            raise ValueError(f"The {side} validity bracket must be a real interval")
        if not part.get("reason"):
            raise ValueError(f"A bracketed {side} boundary must state a reason")
        return Article99EffectiveBoundary(
            status=status,
            method=None,
            valid_date=None,
            still_in_force_at=None,
            instrument=None,
            witness_kind=None,
            witness_file=None,
            witness_pdf_sha256=None,
            witness_text_sha256=None,
            witness_endnote=None,
            witness_quote=None,
            derivation=part.get("derivation"),
            bracket_earliest=earliest,
            bracket_latest=latest,
            reason=part["reason"],
            effect=part.get("effect"),
            successor_article=None,
        )

    if side == "end" and "valid_to" in part and part["valid_to"] is None:
        if "still_in_force_at" not in part:
            raise ValueError("An open-ended segment must state still_in_force_at")
        if {"instrument", "method", "witness"} & part.keys():
            raise ValueError(
                "An open-ended segment must not claim a successor instrument"
            )
        return Article99EffectiveBoundary(
            status=status,
            method=None,
            valid_date=None,
            still_in_force_at=_iso_date(
                part["still_in_force_at"], "end.still_in_force_at"
            ),
            instrument=None,
            witness_kind=None,
            witness_file=None,
            witness_pdf_sha256=None,
            witness_text_sha256=None,
            witness_endnote=None,
            witness_quote=None,
            derivation=part.get("derivation"),
            bracket_earliest=None,
            bracket_latest=None,
            reason=None,
            effect=part.get("effect"),
            successor_article=None,
        )

    method = part.get("method")
    if method not in _ATTRIBUTION_METHODS:
        raise ValueError(f"A proven {side} boundary must state a supported method")
    instrument = instruments.get(part.get("instrument"))
    if instrument is None:
        raise ValueError(f"A proven {side} boundary must reference a known instrument")

    witness = part.get("witness") or {}
    kind = witness.get("kind")
    quote = witness.get("quote") or witness.get("endnote_quote")
    if not isinstance(quote, str) or not quote.strip():
        raise ValueError(f"A proven {side} boundary must carry a verbatim quote")
    if kind == "finance_law_transcription":
        pdf_sha = None
        text_sha = _hex64(witness.get("text_sha256"), f"{side}.witness.text_sha256")
    elif kind in _WITNESS_KINDS_WITH_PDF:
        pdf_sha = _hex64(witness.get("pdf_sha256"), f"{side}.witness.pdf_sha256")
        text_sha = _hex64(witness.get("text_sha256"), f"{side}.witness.text_sha256")
    else:
        raise ValueError(f"A proven {side} boundary has an unknown witness kind")

    if side == "start":
        if "valid_from" not in part:
            raise ValueError("A proven start boundary must state valid_from")
        valid = _iso_date(part["valid_from"], "start.valid_from")
        if valid != instrument.effective_from:
            raise ValueError(
                "start.valid_from must equal the instrument's effective date"
            )
    else:
        if "valid_to" not in part:
            raise ValueError("A proven end boundary must state valid_to")
        valid = _iso_date(part["valid_to"], "end.valid_to")
        if valid != instrument.effective_from:
            raise ValueError("end.valid_to must equal the successor's effective date")

    successor = part.get("successor") or {}
    return Article99EffectiveBoundary(
        status=status,
        method=method,
        valid_date=valid,
        still_in_force_at=None,
        instrument=instrument,
        witness_kind=kind,
        witness_file=(
            witness.get("file") or witness.get("pdf_file") or witness.get("corpus_file")
        ),
        witness_pdf_sha256=pdf_sha,
        witness_text_sha256=text_sha,
        witness_endnote=witness.get("endnote"),
        witness_quote=quote,
        derivation=part.get("derivation"),
        bracket_earliest=None,
        bracket_latest=None,
        reason=None,
        effect=part.get("effect"),
        successor_article=successor.get("article"),
    )


def _attribution(
    raw, instruments: Mapping[str, Article99Instrument]
) -> Article99Attribution:
    """Validate ``effective_attribution`` and build its dataclass."""
    if not isinstance(raw, Mapping):
        raise TypeError("Each Article 99 item must carry effective_attribution")
    segment = raw.get("rate_segment") or {}
    if segment.get("rate") is None or segment.get("first_anchor") is None:
        raise ValueError("Each Article 99 row must state its rate segment")
    start = _boundary(raw.get("start"), "start", instruments)
    end = _boundary(raw.get("end"), "end", instruments)
    if (
        start.valid_date is not None
        and end.valid_date is not None
        and not start.valid_date < end.valid_date
    ):
        raise ValueError("An Article 99 segment cannot end before it starts")
    expected = (
        "proven" if start.status == "proven" and end.status == "proven" else "bracketed"
    )
    if raw.get("status") != expected:
        raise ValueError(
            "An Article 99 row is proven only when both segment ends are witnessed"
        )
    return Article99Attribution(
        status=expected,
        first_anchor=segment["first_anchor"],
        last_anchor=segment["last_anchor"],
        rate=segment["rate"],
        start=start,
        end=end,
    )


ARTICLE_99_SNAPSHOT_YEARS = (2007, 2010, 2014, 2018, 2021, 2024, 2026)
ARTICLE_99_CATALOG_SCHEMA_VERSION = 2


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
if _CATALOG.get("schema_version") != ARTICLE_99_CATALOG_SCHEMA_VERSION:
    raise ValueError(
        "The packaged Article 99 catalog must use schema version "
        f"{ARTICLE_99_CATALOG_SCHEMA_VERSION}"
    )

_INSTRUMENTS = _load_instruments(_CATALOG)

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
            raise ValueError(
                "Effective dates belong inside effective_attribution, not on the "
                "snapshot row"
            )
        _effective_attribution = _attribution(
            _row.get("effective_attribution"), _INSTRUMENTS
        )
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
            effective_attribution=_effective_attribution,
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


def _describe_end(attribution: Article99Attribution) -> str:
    """Render the exclusive end of a proven segment for an error message."""
    if attribution.valid_to is not None:
        return f"{attribution.valid_to.isoformat()} (exclusive)"
    if attribution.still_in_force_at is not None:
        return f"{attribution.still_in_force_at.isoformat()} (still in force)"
    return "an unknown date"


def aggregate_article_99_turnover(
    edition_year: int,
    turnover_by_item_id: Mapping[str, int | float | Decimal],
    *,
    on_date: date | None = None,
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
        on_date: If given, every item must be *proven* to be in force on that
            date. The check uses the witnessed segment, whose ``valid_to`` is
            exclusive (it is the first day the successor text applied). Any
            item whose effective dates are still bracketed is rejected rather
            than assumed to apply.

    Returns:
        An immutable mapping from rate labels such as ``"10%"`` to summed
        taxable bases as ``Decimal`` values.

    Raises:
        Article99UndatedItemError: If ``on_date`` is given and an item's
            effective period is not proven to cover that date.
    """
    _require_supported_edition(edition_year)
    if not isinstance(turnover_by_item_id, Mapping):
        raise TypeError("turnover_by_item_id must be a mapping of item IDs to bases")
    if on_date is not None and (
        not isinstance(on_date, date) or isinstance(on_date, datetime)
    ):
        raise TypeError("on_date must be a datetime.date")

    totals: dict[str, Decimal] = {}
    for item_id, base in turnover_by_item_id.items():
        item = get_article_99_item(edition_year, item_id)
        if item.status != "in_force_in_snapshot":
            raise ValueError(
                f"Article 99 item {item_id!r} is not in force in the snapshot"
            )
        if on_date is not None:
            attribution = item.effective_attribution
            if attribution is None or attribution.status != "proven":
                raise Article99UndatedItemError(
                    f"Article 99 item {item_id!r} has no proven effective dates; "
                    "it cannot be placed on a specific tax date"
                )
            if not attribution.covers(on_date):
                raise Article99UndatedItemError(
                    f"Article 99 item {item_id!r} is not proven to be in force on "
                    f"{on_date.isoformat()} (segment proven from "
                    f"{attribution.valid_from.isoformat()} "
                    f"to {_describe_end(attribution)}); select the item that "
                    "applies on that date"
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
    "ARTICLE_99_CATALOG_SCHEMA_VERSION",
    "ARTICLE_99_SNAPSHOT_YEARS",
    "Article99AmendmentCitation",
    "Article99Attribution",
    "Article99Condition",
    "Article99EffectiveBoundary",
    "Article99Instrument",
    "Article99Item",
    "Article99ItemNotFoundError",
    "Article99TransitionalRateError",
    "Article99UndatedItemError",
    "UnsupportedArticle99EditionError",
    "aggregate_article_99_turnover",
    "get_article_99_item",
    "list_article_99_items",
]
