"""Source-backed CGI Article 100 specific TVA rates and their effective dates.

This API covers the verified CGI Article 100 rate periods from 2007 through
2019. The article was repealed from 2020-01-01. It does not reconstruct the
pre-CGI predecessor regime or infer how a product is taxed after repeal.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from importlib import resources

_RATE_RE = re.compile(r"^(?P<value>\d+(?:\.\d+)?) MAD/(?P<unit>hl|g)$")


@dataclass(frozen=True)
class Article100RatePeriod:
    """A specific Article 100 rate with a verified continuous validity period."""

    article: int
    item_id: str
    product_group: str
    rate: str
    rate_value: Decimal
    rate_unit: str
    valid_from: date
    valid_to: date
    quote: str
    rate_context_quote: str
    source_snapshot: str
    corpus_file: str
    document_title: str
    source_pdf: str
    source_pdf_sha256: str
    source_text_sha256: str


@dataclass(frozen=True)
class Article100Amendment:
    """A primary-law amendment that changed or repealed Article 100 rates."""

    law: str
    law_article: int
    effective_from: date
    change_type: str
    corpus_file: str
    source_sha256: str
    quote: str


class Article100RateNotFoundError(LookupError):
    """Raised when no Article 100 rate exists for a product group and date."""


def _load_source_data() -> dict:
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article100_rates.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _as_date(value: str) -> date:
    return date.fromisoformat(value)


def _load_rate_periods(data: dict) -> tuple[Article100RatePeriod, ...]:
    if data.get("schema_version") != 1 or data.get("article") != 100:
        raise ValueError("The packaged specific-rate data must be CGI Article 100")
    if not data.get("rate_periods"):
        raise ValueError("The Article 100 rate catalog must not be empty")

    rows = []
    seen_ids = set()
    for row in data["rate_periods"]:
        if row.get("article") != 100 or row["item_id"] in seen_ids:
            raise ValueError("An Article 100 rate item is invalid or duplicated")
        seen_ids.add(row["item_id"])
        match = _RATE_RE.fullmatch(row["rate"])
        if not match:
            raise ValueError("An Article 100 rate must have a supported per-unit form")
        if len(row.get("source_pdf_sha256", "")) != 64:
            raise ValueError("Each Article 100 rate must retain its source PDF hash")
        if len(row.get("source_text_sha256", "")) != 64:
            raise ValueError("Each Article 100 rate must retain its source text hash")
        valid_from = _as_date(row["valid_from"])
        valid_to = _as_date(row["valid_to"])
        if valid_to < valid_from:
            raise ValueError("An Article 100 rate has an inverted validity interval")
        rows.append(
            Article100RatePeriod(
                article=100,
                item_id=row["item_id"],
                product_group=row["product_group"],
                rate=row["rate"],
                rate_value=Decimal(match.group("value")),
                rate_unit=match.group("unit"),
                valid_from=valid_from,
                valid_to=valid_to,
                quote=row["quote"],
                rate_context_quote=row["rate_context_quote"],
                source_snapshot=row["source_snapshot"],
                corpus_file=row["corpus_file"],
                document_title=row["document_title"],
                source_pdf=row["source_pdf"],
                source_pdf_sha256=row["source_pdf_sha256"],
                source_text_sha256=row["source_text_sha256"],
            )
        )
    return tuple(rows)


def _load_amendments(data: dict) -> tuple[Article100Amendment, ...]:
    amendments = tuple(
        Article100Amendment(
            law=row["law"],
            law_article=row["law_article"],
            effective_from=_as_date(row["valid_from"]),
            change_type=row["change_type"],
            corpus_file=row["corpus_file"],
            source_sha256=row["source_sha256"],
            quote=row["quote"],
        )
        for row in data["amendments"]
    )
    if not amendments or any(len(row.source_sha256) != 64 for row in amendments):
        raise ValueError("Article 100 amendments must retain source hashes")
    return amendments


_SOURCE_DATA = _load_source_data()
ARTICLE_100_RATE_PERIODS = _load_rate_periods(_SOURCE_DATA)
ARTICLE_100_AMENDMENTS = _load_amendments(_SOURCE_DATA)
ARTICLE_100_LATEST_STATUS = _SOURCE_DATA["latest_status"]


def _validate_as_of(as_of: date) -> None:
    if not isinstance(as_of, date) or isinstance(as_of, datetime):
        raise TypeError("as_of must be a datetime.date")


def list_article_100_rates(as_of: date) -> tuple[Article100RatePeriod, ...]:
    """Return rates in force on the supplied date, or an empty tuple outside coverage."""
    _validate_as_of(as_of)
    return tuple(
        row
        for row in ARTICLE_100_RATE_PERIODS
        if row.valid_from <= as_of <= row.valid_to
    )


def get_article_100_rate(product_group: str, as_of: date) -> Article100RatePeriod:
    """Return the exact specific rate for a named Article 100 product group."""
    if not isinstance(product_group, str):
        raise TypeError("product_group must be a string")
    if not product_group:
        raise ValueError("product_group must not be empty")
    for row in list_article_100_rates(as_of):
        if row.product_group == product_group:
            return row
    raise Article100RateNotFoundError(
        f"Article 100 has no {product_group!r} rate in force on {as_of}"
    )


def is_article_100_in_force(as_of: date) -> bool:
    """Return whether the catalog has Article 100 rates in force on this date."""
    return bool(list_article_100_rates(as_of))


def calculate_article_100_tax(
    as_of: date,
    *,
    wine_and_alcohol_hl: float | Decimal = 0,
    gold_platinum_g: float | Decimal = 0,
    silver_g: float | Decimal = 0,
) -> Decimal:
    """Calculate tax for quantities already classified under Article 100.

    Callers supply quantities in hectolitres or grams and must determine from
    the law whether a transaction belongs to one of these Article 100 groups.
    A non-zero amount outside the verified 2007–2019 periods raises instead of
    applying a stale specific rate.
    """
    _validate_as_of(as_of)
    quantities = {
        "wine_and_alcohol": wine_and_alcohol_hl,
        "gold_platinum": gold_platinum_g,
        "silver": silver_g,
    }
    decimal_quantities = {}
    for group, quantity in quantities.items():
        if isinstance(quantity, bool) or not isinstance(
            quantity, (int, float, Decimal)
        ):
            raise TypeError(f"{group} quantity must be numeric")
        try:
            normalized = Decimal(str(quantity))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise TypeError(f"{group} quantity must be numeric") from error
        if not normalized.is_finite() or normalized < 0:
            raise ValueError(f"{group} quantity must be finite and non-negative")
        decimal_quantities[group] = normalized

    rates = list_article_100_rates(as_of)
    if not rates:
        if any(decimal_quantities.values()):
            raise Article100RateNotFoundError(
                f"No Article 100 rate is available on {as_of}; check the predecessor "
                "regime or the law after the 2020 repeal"
            )
        return Decimal(0)

    by_group = {row.product_group: row for row in rates}
    return sum(
        (
            quantity * by_group[group].rate_value
            for group, quantity in decimal_quantities.items()
        ),
        start=Decimal(0),
    )


__all__ = [
    "ARTICLE_100_AMENDMENTS",
    "ARTICLE_100_LATEST_STATUS",
    "ARTICLE_100_RATE_PERIODS",
    "Article100Amendment",
    "Article100RateNotFoundError",
    "Article100RatePeriod",
    "calculate_article_100_tax",
    "get_article_100_rate",
    "is_article_100_in_force",
    "list_article_100_rates",
]
