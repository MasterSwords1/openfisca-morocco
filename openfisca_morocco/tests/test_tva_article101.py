"""Tests for the distinct, quote-backed 2006 LAR Article 101 snapshot."""

import json
from dataclasses import FrozenInstanceError
from importlib import resources

import pytest

from openfisca_morocco.tva_article101 import (
    Article101CorroboratingSource,
    Article101SourceCitation,
    LAR2006Article101ItemNotFoundError,
    get_lar_2006_article_101_item,
    get_lar_2006_article_101_snapshot,
    list_lar_2006_article_101_items,
)


def _load_packaged_source():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_lar_2006_article101.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def test_2006_lar_snapshot_preserves_source_metadata_and_legal_dates():
    source = _load_packaged_source()
    snapshot = get_lar_2006_article_101_snapshot()

    assert snapshot.edition_year == 2006
    assert snapshot.article == 101
    assert snapshot.document_title == "Livre d’Assiette et de Recouvrement 2006"
    assert snapshot.effective_from == "2006-01-01"
    assert snapshot.effective_date_citation == Article101SourceCitation(
        article=212,
        source_page=180,
        corpus_file=source["effective_date_citation"]["corpus_file"],
        quote=source["effective_date_citation"]["quote"],
    )
    assert "1er janvier 2006" in snapshot.effective_date_citation.quote
    assert snapshot.predecessor_repeal_citation.article == 213
    assert "loi n° 30- 85" in snapshot.predecessor_repeal_citation.quote
    assert "1er janvier 2006" in snapshot.predecessor_repeal_citation.quote
    assert (
        "sont abrogées les dispositions" in snapshot.predecessor_repeal_citation.quote
    )
    assert snapshot.predecessor_repeal_citation.source_page == 181
    assert snapshot.corpus_file == source["corpus_file"]
    assert snapshot.source_pdf == source["source_pdf"]
    assert snapshot.source_pdf_sha256 == source["source_pdf_sha256"]
    assert snapshot.source_text_sha256 == source["source_text_sha256"]
    assert snapshot.source_url == source["source_url"]
    assert snapshot.retrieval_url == source["retrieval_url"]
    assert "not claimed byte-identical" in snapshot.retrieval_note
    assert "visually checked" in snapshot.retrieval_note
    assert snapshot.publisher == source["publisher"]
    assert snapshot.source_pdf_page_count == 235
    assert snapshot.source_printed_folio_total == 241
    assert snapshot.source_pages == (95, 96, 97, 98)
    assert len(snapshot.source_pdf_sha256) == 64
    assert len(snapshot.source_text_sha256) == 64
    assert "2004–2005" in get_lar_2006_article_101_snapshot.__doc__


def test_all_38_items_round_trip_with_quotes_and_source_hashes():
    source = _load_packaged_source()
    items = list_lar_2006_article_101_items()

    assert isinstance(items, tuple)
    assert len(items) == len(source["items"]) == 38
    assert {item.rate for item in items} == {"7%", "10%", "14%"}
    assert {
        rate: sum(item.rate == rate for item in items) for rate in ("7%", "10%", "14%")
    } == {"7%": 14, "10%": 16, "14%": 8}

    for item, row in zip(items, source["items"]):
        assert get_lar_2006_article_101_item(row["item_id"]) == item
        assert item.edition_year == row["edition_year"] == 2006
        assert item.article == row["article"] == 101
        assert item.item_id == row["item_id"]
        assert item.rate == row["rate"]
        assert item.rate_context_quote == row["rate_context_quote"]
        assert item.item_type == row["item_type"]
        assert item.right_to_deduct == row.get("right_to_deduct")
        assert item.quote == row["quote"]
        assert item.status == row["status"]
        assert item.corpus_file == row["corpus_file"]
        assert item.itemization == row["itemization"]
        assert [
            {"kind": condition.kind, "quote": condition.quote}
            for condition in item.conditions
        ] == (row.get("conditions") or [])
        assert item.document_title == source["document_title"]
        assert item.source_pdf == source["source_pdf"]
        assert item.source_pdf_sha256 == source["source_pdf_sha256"]
        assert item.source_text_sha256 == source["source_text_sha256"]
        assert item.source_url == source["source_url"]
        assert item.retrieval_url == source["retrieval_url"]
        assert item.source_pages == (95, 96, 97, 98)
        assert "valid_from" not in row
        assert "valid_to" not in row
        assert not hasattr(item, "valid_from")
        assert not hasattr(item, "valid_to")


def test_exact_2006_items_keep_deduction_treatment_and_conditions():
    insurance_service = get_lar_2006_article_101_item(
        "2006-art101-14pct-insurance-no-deduction"
    )
    utility_vehicle = get_lar_2006_article_101_item("2006-art101-7pct-013")

    assert insurance_service.article == 101
    assert insurance_service.rate == "14%"
    assert insurance_service.right_to_deduct is False
    assert "courtier d’assurances" in insurance_service.quote
    assert utility_vehicle.rate == "7%"
    assert "voiture économique" in utility_vehicle.quote
    assert utility_vehicle.conditions
    assert all(
        condition.kind == "application_condition"
        for condition in utility_vehicle.conditions
    )

    pharmaceutical_items = [
        item
        for item in list_lar_2006_article_101_items()
        if item.rate == "7%" and "produits pharmaceutiques" in item.quote.lower()
    ]
    assert len(pharmaceutical_items) == 2
    assert all(
        any(
            "L’application du taux réduit est subordonnée" in condition.quote
            for condition in item.conditions
        )
        for item in pharmaceutical_items
    )


def test_article_101_lookup_rejects_unknown_ids_and_bad_arguments():
    with pytest.raises(LAR2006Article101ItemNotFoundError, match="2006 snapshot"):
        get_lar_2006_article_101_item("not-a-catalog-id")

    with pytest.raises(TypeError, match="item_id must be a string"):
        get_lar_2006_article_101_item(101)

    with pytest.raises(ValueError, match="must not be empty"):
        get_lar_2006_article_101_item("")


def test_returned_snapshot_and_items_are_immutable():
    snapshot = get_lar_2006_article_101_snapshot()
    item = list_lar_2006_article_101_items()[0]

    with pytest.raises(FrozenInstanceError):
        item.rate = "0%"

    with pytest.raises(FrozenInstanceError):
        snapshot.effective_from = "2004-01-01"


def test_snapshot_names_a_live_primary_source_with_its_own_hash():
    source = _load_packaged_source()
    snapshot = get_lar_2006_article_101_snapshot()
    primary = snapshot.corroborating_source

    assert isinstance(primary, Article101CorroboratingSource)
    assert primary.article == 101
    assert primary.url == "https://www.sgg.gov.ma/BO/bo_fr/2005/BO_5382-bis_fr.pdf"
    assert primary.url == source["corroborating_source"]["url"]
    assert len(primary.pdf_sha256) == 64
    assert primary.pdf_sha256 == source["corroborating_source"]["pdf_sha256"]
    assert primary.pdf_sha256 != snapshot.source_pdf_sha256
    assert primary.pdf_bytes == 16561566
    assert primary.pdf_pages == (46, 47)
    assert primary.printed_folios == (1018, 1019)
    assert "Bulletin officiel n° 5382 bis" in primary.document_title
    assert "35-05" in primary.instrument
    assert primary.retrieval_verified_on == "2026-11-14"
    assert "byte-identical" in primary.corroboration_note
    assert "Article 102 = specific rates" in primary.article_numbering_note
    assert "NOT the article" in primary.article_numbering_note
