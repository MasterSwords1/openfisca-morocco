"""Tests for the quote-backed Article 91 and 92 exemption snapshots."""

import json
from dataclasses import FrozenInstanceError
from importlib import resources

import pytest

from openfisca_morocco.tva_article91_92 import (
    ARTICLE_91_92_SNAPSHOT_YEARS,
    TVAExemptionItemNotFoundError,
    UnsupportedTVAExemptionEditionError,
    get_article_91_item,
    get_article_92_item,
    list_article_91_items,
    list_article_92_items,
)


def test_supported_exemption_years_are_exact_consolidated_snapshots():
    assert ARTICLE_91_92_SNAPSHOT_YEARS == (2007, 2010, 2014, 2018, 2021, 2024, 2026)


def test_all_exemption_items_round_trip_with_source_quotes_and_no_validity_dates():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article91_92_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)

    for edition in catalog["editions"]:
        year = edition["edition_year"]
        for row in edition["items"]:
            assert "valid_from" not in row
            assert "valid_to" not in row
            getter = (
                get_article_91_item if row["article"] == 91 else get_article_92_item
            )
            item = getter(year, row["item_id"])
            assert item.article == row["article"]
            assert item.edition_year == year
            assert item.item_id == row["item_id"]
            assert item.rate == row["rate"] == "exempt"
            assert item.right_to_deduct is (row["article"] == 92)
            assert item.quote == row["quote"]
            assert item.rate_context_quote == row["rate_context_quote"]
            assert item.status == row["status"]
            assert item.corpus_file == row["corpus_file"]
            assert item.source_pdf_sha256 == edition["source_pdf_sha256"]
            assert item.source_text_sha256 == edition["source_text_sha256"]
            assert not hasattr(item, "valid_from")
            assert not hasattr(item, "valid_to")


def test_2026_article_91_and_92_keep_distinct_deduction_treatment():
    article_91 = get_article_91_item(2026, "2026-art91-clause-001")
    article_92 = get_article_92_item(2026, "2026-art92-clause-001")

    assert article_91.right_to_deduct is False
    assert "pâtes alimentaires courtes" in article_91.quote
    assert article_92.right_to_deduct is True
    assert "exportation" in article_92.quote


def test_list_preserves_snapshot_item_order():
    assert list_article_91_items(2026)[0].itemization == "article_level"
    assert list_article_92_items(2026)[0].itemization == "article_level"
    assert list_article_91_items(2026)[1].item_id == "2026-art91-clause-001"


def test_unsupported_editions_and_items_fail_explicitly():
    with pytest.raises(UnsupportedTVAExemptionEditionError, match="supported editions"):
        list_article_91_items(2004)
    with pytest.raises(UnsupportedTVAExemptionEditionError, match="supported editions"):
        list_article_92_items(2025)
    with pytest.raises(TVAExemptionItemNotFoundError):
        get_article_91_item(2026, "not-a-catalog-id")


def test_lookup_validates_year_article_and_item_id():
    with pytest.raises(TypeError, match="integer snapshot year"):
        list_article_91_items("2026")
    with pytest.raises(TypeError, match="integer snapshot year"):
        list_article_92_items(True)
    with pytest.raises(TypeError, match="string catalog ID"):
        get_article_92_item(2026, 1)
    with pytest.raises(ValueError, match="must not be empty"):
        get_article_91_item(2026, "")


def test_items_are_immutable():
    item = get_article_91_item(2026, "2026-art91-clause-001")
    with pytest.raises(FrozenInstanceError):
        item.rate = "20%"
