"""Tests for the source-backed Article 100 per-unit rate history."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from openfisca_morocco.tva_article100 import (
    ARTICLE_100_AMENDMENTS,
    ARTICLE_100_LATEST_STATUS,
    Article100RateNotFoundError,
    calculate_article_100_tax,
    get_article_100_rate,
    is_article_100_in_force,
    list_article_100_rates,
)


def test_article_100_specific_rate_periods_and_2020_repeal_are_explicit():
    assert is_article_100_in_force(date(2007, 1, 1))
    assert is_article_100_in_force(date(2019, 12, 31))
    assert not is_article_100_in_force(date(2020, 1, 1))
    assert ARTICLE_100_LATEST_STATUS["status"] == "abrogated"
    assert ARTICLE_100_AMENDMENTS[-1].effective_from == date(2020, 1, 1)


def test_metal_rates_change_on_2011_01_01():
    assert get_article_100_rate("gold_platinum", date(2010, 12, 31)).rate == "4 MAD/g"
    assert get_article_100_rate("silver", date(2010, 12, 31)).rate == "0.05 MAD/g"
    assert get_article_100_rate("gold_platinum", date(2011, 1, 1)).rate == "5 MAD/g"
    assert get_article_100_rate("silver", date(2011, 1, 1)).rate == "0.10 MAD/g"
    assert (
        get_article_100_rate("wine_and_alcohol", date(2019, 12, 31)).rate
        == "100 MAD/hl"
    )


def test_specific_tax_uses_the_matching_physical_units():
    assert calculate_article_100_tax(
        date(2010, 6, 1),
        wine_and_alcohol_hl=2,
        gold_platinum_g=3,
        silver_g=10,
    ) == Decimal("212.50")
    assert calculate_article_100_tax(
        date(2011, 1, 1), gold_platinum_g=3, silver_g=10
    ) == Decimal("16.00")


def test_nonzero_amounts_outside_the_verified_period_are_not_given_a_stale_rate():
    assert list_article_100_rates(date(2006, 12, 31)) == ()
    assert list_article_100_rates(date(2020, 1, 1)) == ()
    assert calculate_article_100_tax(date(2020, 1, 1)) == Decimal(0)
    with pytest.raises(Article100RateNotFoundError, match="predecessor regime"):
        calculate_article_100_tax(date(2006, 12, 31), wine_and_alcohol_hl=1)
    with pytest.raises(Article100RateNotFoundError, match="law after the 2020 repeal"):
        calculate_article_100_tax(date(2020, 1, 1), silver_g=1)


def test_article100_lookup_validates_date_and_quantity_inputs():
    with pytest.raises(TypeError, match="datetime.date"):
        list_article_100_rates("2011-01-01")
    with pytest.raises(TypeError, match="datetime.date"):
        list_article_100_rates(datetime(2011, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="finite and non-negative"):
        calculate_article_100_tax(date(2011, 1, 1), silver_g=-1)
    with pytest.raises(ValueError, match="finite and non-negative"):
        calculate_article_100_tax(date(2011, 1, 1), silver_g=float("nan"))
