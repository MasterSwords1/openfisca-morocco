"""Tests for the explicit, snapshot-scoped Article 99 catalog lookup."""

import json
from dataclasses import FrozenInstanceError
from importlib import resources

import pytest

from openfisca_morocco.tva_article99 import (
    ARTICLE_99_SNAPSHOT_YEARS,
    Article99ItemNotFoundError,
    UnsupportedArticle99EditionError,
    get_article_99_item,
    list_article_99_items,
)


def test_supported_article_99_editions_are_the_consolidated_snapshots():
    assert ARTICLE_99_SNAPSHOT_YEARS == (2007, 2010, 2014, 2018, 2021, 2024, 2026)


def test_every_catalog_item_round_trips_with_quote_and_provenance():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article99_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)

    for edition in catalog["editions"]:
        year = edition["edition_year"]
        for row in edition["items"]:
            item = get_article_99_item(year, row["item_id"])

            assert item.item_id == row["item_id"]
            assert item.rate == row["rate"]
            assert item.quote == row["quote"]
            assert item.corpus_file == row["corpus_file"]
            assert item.rate_context_quote == row["rate_context_quote"]
            assert item.item_type == row["item_type"]
            assert item.itemization == row["itemization"]
            assert item.right_to_deduct == row.get("right_to_deduct")
            assert item.status == row["status"]
            assert item.parent_context_item_id == row.get("parent_context_item_id")
            assert item.parent_context_quote == row.get("parent_context_quote")
            assert [
                {"kind": condition.kind, "quote": condition.quote}
                for condition in item.conditions
            ] == (row.get("conditions") or [])
            source_endnote_labels = row.get("source_endnote_labels")
            assert item.source_endnote_labels == (
                tuple(source_endnote_labels)
                if source_endnote_labels is not None
                else None
            )
            assert item.source_pdf == edition["source_pdf"]
            assert item.source_pdf_sha256 == edition["source_pdf_sha256"]
            assert item.source_text_sha256 == edition["source_text_sha256"]
            assert item.document_title == edition["document_title"]
            assert "valid_from" not in row
            assert "valid_to" not in row
        assert "snapshot_as_of" not in edition


def test_list_returns_the_exact_snapshot_items_in_source_order():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article99_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    for edition in catalog["editions"]:
        items = list_article_99_items(edition["edition_year"])

        assert isinstance(items, tuple)
        assert [item.item_id for item in items] == [
            row["item_id"] for row in edition["items"]
        ]
        assert [item.rate for item in items] == [
            row["rate"] for row in edition["items"]
        ]


def test_lookup_returns_verbatim_clause_and_provenance():
    item = get_article_99_item(2007, "2007-art99-7pct-001")

    assert item.edition_year == 2007
    assert item.item_id == "2007-art99-7pct-001"
    assert item.rate == "7%"
    assert "l'eau livrée" in item.quote
    assert "assainissement" in item.quote
    assert item.corpus_file == "laws/ma_tax_law/data/consolidated/CGI-2007-FR.pdf.txt"
    assert item.source_pdf
    assert item.source_pdf_sha256
    assert item.source_text_sha256
    assert not hasattr(item, "valid_from")
    assert not hasattr(item, "valid_to")
    assert not hasattr(item, "snapshot_as_of")


def test_2026_hotel_rental_clause_keeps_its_page_continuation():
    item = get_article_99_item(2026, "2026-art99-10pct-002")
    expected_quote = (
        "les opérations de location d'immeubles à usage d'hôtels, de\n"
        "              motels, de villages de vacances ou d'ensembles immobiliers à\n"
        "              destination touristique, équipés totalement ou partiellement, y\n"
        "\n"
        "compris le restaurant, le bar, le dancing, la piscine, dans la mesure\n"
        "              où ils font partie intégrante de l'ensemble touristique ;"
    )

    assert item.rate == "10%"
    assert item.quote == expected_quote
    assert item.corpus_file == "laws/ma_tax_law/data/consolidated/CGI-2026-FR.pdf.txt"


def test_source_endnote_labels_are_returned_as_immutable_provenance():
    item = get_article_99_item(2014, "2014-art99-7pct-008")

    assert item.source_endnote_labels == ("187",)


def test_item_ids_are_scoped_to_the_requested_edition():
    with pytest.raises(Article99ItemNotFoundError):
        get_article_99_item(2010, "2007-art99-7pct-001")


def test_2004_is_an_explicit_gap_not_an_interpolated_snapshot():
    with pytest.raises(UnsupportedArticle99EditionError, match="No consolidated"):
        get_article_99_item(2004, "2007-art99-7pct-001")

    with pytest.raises(UnsupportedArticle99EditionError, match="No consolidated"):
        list_article_99_items(2004)


def test_unknown_editions_and_item_ids_fail_explicitly():
    with pytest.raises(UnsupportedArticle99EditionError, match="supported editions"):
        get_article_99_item(2025, "2024-art99-general-20pct")

    with pytest.raises(Article99ItemNotFoundError):
        get_article_99_item(2024, "not-a-catalog-id")

    with pytest.raises(UnsupportedArticle99EditionError, match="supported editions"):
        list_article_99_items(2025)


def test_lookup_requires_an_integer_edition_and_nonempty_string_id():
    with pytest.raises(TypeError, match="integer snapshot year"):
        get_article_99_item("2007", "2007-art99-7pct-001")

    with pytest.raises(TypeError, match="integer snapshot year"):
        get_article_99_item(True, "2007-art99-7pct-001")

    with pytest.raises(TypeError, match="integer snapshot year"):
        list_article_99_items("2024")

    with pytest.raises(TypeError, match="integer snapshot year"):
        list_article_99_items(True)

    with pytest.raises(TypeError, match="item_id must be a string"):
        get_article_99_item(2007, 1)

    with pytest.raises(ValueError, match="must not be empty"):
        get_article_99_item(2007, "")


def test_returned_item_is_immutable():
    item = get_article_99_item(2024, "2024-art99-general-20pct")

    with pytest.raises(FrozenInstanceError):
        item.rate = "0%"
