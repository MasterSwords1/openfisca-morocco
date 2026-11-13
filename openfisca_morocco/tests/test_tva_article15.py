"""Tests for the historical, point-in-time Loi 30-85 Article 15 catalog."""

import json
from collections import Counter
from dataclasses import FrozenInstanceError
from importlib import resources

import pytest

from openfisca_morocco.tva_article15 import (
    ARTICLE_15_CATALOG,
    ARTICLE_15_SNAPSHOT_DATES,
    ARTICLE_15_SNAPSHOT_YEARS,
    Article15AmendmentCitation,
    Article15DGIEndnoteCitation,
    Article15ItemNotFoundError,
    UnsupportedArticle15SnapshotError,
    get_article_15_item,
    get_article_15_snapshot,
    list_article_15_items,
)


def _load_packaged_source():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article15_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)["historical_article15_2004_2005"]


def test_article_15_exposes_only_the_two_point_in_time_snapshots():
    source = _load_packaged_source()

    assert ARTICLE_15_SNAPSHOT_YEARS == (2004, 2005)
    assert ARTICLE_15_SNAPSHOT_DATES == ("2004-01-01", "2005-01-01")
    assert ARTICLE_15_CATALOG.edition_basis == (
        "pre-CGI statutory snapshots; not CGI Article 99 or LAR Article 101"
    )
    assert "point-in-time" in ARTICLE_15_CATALOG.date_semantics
    assert "valid_to" in ARTICLE_15_CATALOG.date_semantics
    assert ARTICLE_15_CATALOG.source_chain_audit.status == (
        "available_source_search_completed"
    )
    assert "non-finance" in ARTICLE_15_CATALOG.source_chain_audit.scope
    assert "cannot prove an exhaustive negative" in (
        ARTICLE_15_CATALOG.source_chain_audit.limitation
    )
    reviewed_sources = ARTICLE_15_CATALOG.source_chain_audit.reviewed_sources
    assert {item.id for item in reviewed_sources} == {
        "loi-45-02-article9-article15-absence-check",
        "dgi-cgi-2014-tva-amendment-reference-table",
    }
    article9 = next(
        item
        for item in reviewed_sources
        if item.id == "loi-45-02-article9-article15-absence-check"
    )
    assert article9.source_pages == (10,)
    assert "does not name Article 15" in article9.finding
    assert article9.verified_quote and article9.transcription_file
    reference_table = next(
        item
        for item in reviewed_sources
        if item.id == "dgi-cgi-2014-tva-amendment-reference-table"
    )
    assert reference_table.source_pages == (427, 428)
    assert "not a complete negative audit" in reference_table.finding
    assert [snapshot["as_of"] for snapshot in source["snapshots"]] == list(
        ARTICLE_15_SNAPSHOT_DATES
    )
    assert all("effective_from" not in snapshot for snapshot in source["snapshots"])

    for year, date in zip(ARTICLE_15_SNAPSHOT_YEARS, ARTICLE_15_SNAPSHOT_DATES):
        snapshot = get_article_15_snapshot(year)
        assert snapshot.as_of == date
        assert not hasattr(snapshot, "effective_from")
        assert not hasattr(snapshot, "valid_from")
        assert not hasattr(snapshot, "valid_to")


def test_all_items_round_trip_with_quotes_and_provenance():
    source = _load_packaged_source()
    expected_counts = {2004: 40, 2005: 41}
    expected_rate_counts = {
        2004: {"7%": 26, "10%": 5, "14%": 9},
        2005: {"7%": 25, "10%": 7, "14%": 9},
    }

    for snapshot_data in source["snapshots"]:
        year = snapshot_data["edition_year"]
        snapshot = get_article_15_snapshot(year)
        items = list_article_15_items(year)

        assert isinstance(items, tuple)
        assert len(items) == expected_counts[year] == len(snapshot_data["items"])
        assert Counter(item.rate for item in items) == expected_rate_counts[year]
        assert [item.item_id for item in items] == [
            row["item_id"] for row in snapshot_data["items"]
        ]
        assert len(snapshot.items) == expected_counts[year]

        for item, row in zip(items, snapshot_data["items"]):
            assert get_article_15_item(year, row["item_id"]) == item
            assert item.edition_year == year
            assert item.snapshot_date == snapshot_data["as_of"]
            assert item.article == row["article"] == 15
            assert item.rate == row["rate"]
            assert item.rate_context_quote == row["rate_context_quote"]
            assert item.item_type == row["item_type"]
            assert item.right_to_deduct == row.get("right_to_deduct")
            assert item.quote == row["quote"]
            assert item.status == row["status"]
            assert item.corpus_file == row["corpus_file"]
            assert item.itemization == row["itemization"]
            assert item.source_sha256 == row["source_sha256"]
            assert item.source_pages == tuple(row["source_pages"])
            assert item.rate_context_corpus_file == row.get("rate_context_corpus_file")
            assert [
                {"kind": condition.kind, "quote": condition.quote}
                for condition in item.conditions
            ] == (row.get("conditions") or [])
            assert all(
                isinstance(citation, Article15AmendmentCitation)
                for citation in item.amendment_citations
            )
            assert [
                {
                    field: (
                        list(getattr(citation, field))
                        if field == "source_pdf_pages"
                        else getattr(citation, field)
                    )
                    for field in (
                        "law",
                        "law_article",
                        "article_amended",
                        "effective_from",
                        "corpus_file",
                        "source_pdf",
                        "source_pdf_sha256",
                        "source_pdf_pages",
                        "source_url",
                        "source_quote",
                        "transcription_sha256",
                        "quote_verification",
                    )
                }
                for citation in item.amendment_citations
            ] == (row.get("amendment_citations") or [])
            assert all(
                isinstance(citation, Article15DGIEndnoteCitation)
                for citation in item.dgi_endnote_citations
            )
            assert [
                {
                    "label": citation.label,
                    "corpus_file": citation.corpus_file,
                    "quote": citation.quote,
                    "source_sha256": citation.source_sha256,
                }
                for citation in item.dgi_endnote_citations
            ] == (row.get("dgi_endnote_citations") or [])
            assert not hasattr(item, "valid_from")
            assert not hasattr(item, "valid_to")


def test_2004_and_2005_lists_preserve_the_documented_changes():
    water_2004 = get_article_15_item(2004, "2004-art15-7pct-deduct-001")
    water_2005 = get_article_15_item(2005, "2005-art15-7pct-deduct-001")
    oils_2004 = get_article_15_item(2004, "2004-art15-7pct-deduct-004")
    oils_2005 = get_article_15_item(2005, "2005-art15-10pct-deduct-006")
    salt_2005 = get_article_15_item(2005, "2005-art15-10pct-deduct-007")
    electricity_2004 = get_article_15_item(2004, "2004-art15-14pct-deduct-008")
    feed_2004 = next(
        item
        for item in list_article_15_items(2004)
        if "aliments destinés" in item.quote
    )
    feed_2005 = next(
        item
        for item in list_article_15_items(2005)
        if "aliments destinés" in item.quote
    )
    car_2004 = next(
        item
        for item in list_article_15_items(2004)
        if "voiture économique" in item.quote
    )
    car_2005 = next(
        item
        for item in list_article_15_items(2005)
        if "voiture économique" in item.quote
    )

    assert water_2004.rate == water_2005.rate == "7%"
    assert "assainissement" not in water_2004.quote
    assert "assainissement" in water_2005.quote
    assert oils_2004.rate == "7%"
    assert oils_2005.rate == "10%"
    assert salt_2005.rate == "10%"
    assert "sel de cuisine" in salt_2005.quote
    assert electricity_2004.rate == "14%"
    assert electricity_2004.rate_context_corpus_file is not None
    assert electricity_2004.amendment_citations[0].law_article == 12
    assert electricity_2004.amendment_citations[0].effective_from == "2004-01-01"
    assert "tourteaux servant" not in feed_2004.quote
    assert "tourteaux servant" in feed_2005.quote
    assert "prestations de montage" not in car_2004.quote
    assert "prestations de montage" in car_2005.quote
    assert any(
        "aux prestations de montage" in condition.quote
        for condition in car_2005.conditions
    )

    items_2004 = list_article_15_items(2004)
    electricity_index = items_2004.index(electricity_2004)
    no_deduction_index = next(
        index
        for index, item in enumerate(items_2004)
        if item.rate == "14%" and item.right_to_deduct is False
    )
    assert electricity_index == no_deduction_index - 1

    items_2005 = list_article_15_items(2005)
    oils_index = items_2005.index(oils_2005)
    salt_index = items_2005.index(salt_2005)
    first_14_percent_index = next(
        index for index, item in enumerate(items_2005) if item.rate == "14%"
    )
    last_preexisting_10_percent_index = max(
        index
        for index, item in enumerate(items_2005)
        if item.rate == "10%"
        and item.item_id not in {oils_2005.item_id, salt_2005.item_id}
    )
    assert oils_index == last_preexisting_10_percent_index + 1
    assert salt_index == oils_index + 1
    assert salt_index == first_14_percent_index - 1

    changes = ARTICLE_15_CATALOG.changes
    assert len(changes) == 1
    assert (changes[0].from_edition, changes[0].to_edition) == (2004, 2005)
    assert changes[0].effective_from == "2005-01-01"
    source_change = _load_packaged_source()["changes"][0]
    assert changes[0].documented_changes == tuple(source_change["documented_changes"])
    assert any("sanitation services" in item for item in changes[0].documented_changes)
    assert any("Fluid edible oils" in item for item in changes[0].documented_changes)
    assert any("oilseed cakes" in item for item in changes[0].documented_changes)
    assert any("assembly services" in item for item in changes[0].documented_changes)
    assert any("Cooking salt" in item for item in changes[0].documented_changes)
    assert changes[0].source_citation.law_article == 15


def test_source_caveats_and_gazette_citations_are_exposed():
    snapshot_2004 = get_article_15_snapshot(2004)
    snapshot_2005 = get_article_15_snapshot(2005)

    assert "scribd" in snapshot_2004.baseline_source.source_url.lower()
    assert "not the DGI or SGG" in (snapshot_2004.baseline_source.retrieval_limitation)
    assert "not locally pinned" in (snapshot_2004.baseline_source.retrieval_limitation)
    assert snapshot_2004.amendment_chain[0].law_article == 12
    assert "visually_transcribed_from_pinned_bulletin_officiel_scan" == (
        snapshot_2004.amendment_chain[0].quote_verification
    )
    assert snapshot_2005.amendment_chain[-1].law_article == 15
    assert snapshot_2005.amendment_chain[-1].source_pdf_sha256
    assert snapshot_2005.amendment_chain[-1].source_pdf_pages == (13,)


def test_snapshot_and_item_lookup_rejects_unknown_years_ids_and_bad_arguments():
    with pytest.raises(UnsupportedArticle15SnapshotError, match="supported snapshots"):
        get_article_15_snapshot(2006)

    with pytest.raises(UnsupportedArticle15SnapshotError, match="supported snapshots"):
        list_article_15_items(2003)

    with pytest.raises(Article15ItemNotFoundError, match="2004 snapshot"):
        get_article_15_item(2004, "2005-art15-10pct-deduct-006")

    with pytest.raises(Article15ItemNotFoundError, match="2004 snapshot"):
        get_article_15_item(2004, "not-a-catalog-id")

    with pytest.raises(TypeError, match="integer snapshot year"):
        get_article_15_snapshot("2004")

    with pytest.raises(TypeError, match="integer snapshot year"):
        list_article_15_items(True)

    with pytest.raises(TypeError, match="item_id must be a string"):
        get_article_15_item(2004, 15)

    with pytest.raises(ValueError, match="must not be empty"):
        get_article_15_item(2004, "")


def test_returned_snapshots_and_items_are_immutable():
    snapshot = get_article_15_snapshot(2004)
    item = list_article_15_items(2004)[0]

    with pytest.raises(FrozenInstanceError):
        snapshot.as_of = "2005-01-01"

    with pytest.raises(FrozenInstanceError):
        item.rate = "0%"
