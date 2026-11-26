"""Tests for the quote-backed Article 91 and 92 exemption snapshots."""

import hashlib
import json
import os
import re
from dataclasses import FrozenInstanceError
from importlib import resources
from pathlib import Path

import pytest

from openfisca_morocco.tva_article91_92 import (
    ARTICLE_91_92_SNAPSHOT_YEARS,
    TVAExemptionItemNotFoundError,
    UnsupportedTVAExemptionEditionError,
    get_article_91_item,
    get_article_91_subitem,
    get_article_92_item,
    get_article_92_subitem,
    list_article_91_items,
    list_article_91_subitems,
    list_article_92_items,
    list_article_92_subitems,
)

_CORPUS_DATASET = "laws/ma_tax_law/data/consolidated/tva_article_lists.json"
_ENV_CORPUS = os.environ.get("MOROCCO_HOLY_GRAPH")
if _ENV_CORPUS:
    _HOLY_GRAPH = Path(_ENV_CORPUS)
    if not (_HOLY_GRAPH / _CORPUS_DATASET).is_file():
        pytest.exit(
            f"MOROCCO_HOLY_GRAPH={_ENV_CORPUS!r} does not contain {_CORPUS_DATASET}",
            returncode=1,
        )
else:
    _HOLY_GRAPH = Path(__file__).resolve().parents[2].parent / "morocco-holy-graph"
_ASCII_ID = re.compile(r"\A[A-Za-z0-9-]+\Z")


def _catalog():
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article91_92_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def _all_rows():
    for edition_year in ARTICLE_91_92_SNAPSHOT_YEARS:
        for article, lister in (
            (91, list_article_91_items),
            (92, list_article_92_items),
            (91, list_article_91_subitems),
            (92, list_article_92_subitems),
        ):
            for item in lister(edition_year):
                assert item.article == article
                yield item


def test_supported_exemption_years_are_exact_consolidated_snapshots():
    assert ARTICLE_91_92_SNAPSHOT_YEARS == (2007, 2010, 2014, 2018, 2021, 2024, 2026)


def test_all_exemption_items_round_trip_with_source_quotes_and_no_validity_dates():
    catalog = _catalog()

    for edition in catalog["editions"]:
        year = edition["edition_year"]
        for bucket, getter in (
            (
                "items",
                lambda y, a, i: (
                    get_article_91_item if a == 91 else get_article_92_item
                )(y, i),
            ),
            (
                "subitems",
                lambda y, a, i: (
                    get_article_91_subitem if a == 91 else get_article_92_subitem
                )(y, i),
            ),
        ):
            for row in edition[bucket]:
                assert "valid_from" not in row
                assert "valid_to" not in row
                item = getter(year, row["article"], row["item_id"])
                assert item.article == row["article"]
                assert item.edition_year == year
                assert item.item_id == row["item_id"]
                assert item.source_item_id == row["source_item_id"]
                assert item.parent_item_id == row["parent_item_id"]
                assert item.nesting_depth == row["nesting_depth"]
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


def test_solar_water_heaters_cross_article_handoff_links_both_articles():
    """Article 99 says the item left for Article 91; Article 91 must show it.

    Loi 65-20 article 6 removed the solar water heaters from the Article 99
    reduced-rate list and added them as item 8° of the Article 91 exemptions.
    The Article 99 side records that handoff (``effect="exempted"``,
    ``successor_article=91``); this test pins the other end of the link, so the
    two catalogs cannot drift apart silently.
    """
    from openfisca_morocco.tva_article99 import get_article_99_item

    removed = get_article_99_item(2018, "2018-art99-10pct-008")
    handoff = removed.effective_attribution.end
    assert handoff.effect == "exempted"
    assert handoff.successor_article == 91
    assert handoff.instrument.key == "65-20"
    assert handoff.valid_date.isoformat() == "2021-01-01"

    target = get_article_91_item(2021, "2021-art91-clause-015")
    assert target.article == 91
    assert target.right_to_deduct is False
    assert target.clause_number == 8
    assert "chauffe-eaux solaires" in target.quote.casefold()
    # The clause carries the Article 6 of Loi 65-20 endnote (444 in CGI 2021).
    assert "65-20" in target.quote or "444" in target.quote

    # It went back to Article 99 in 2022: the 2024 and 2026 Article 91 lists no
    # longer contain it, and the Article 99 catalog lists it again at 10 %.
    for year in (2024, 2026):
        article_91_quotes = " ".join(
            item.quote.casefold() for item in list_article_91_items(year)
        )
        assert "chauffe-eaux solaires" not in article_91_quotes


# ---------------------------------------------------------------------------
# Itemization (issue #6 box 6) and the two provenance regressions it uncovered
# ---------------------------------------------------------------------------


def test_nested_subitems_are_itemized_and_parent_linked():
    """Box 6: nested bullets and letters are rows, not text inside a clause."""
    total = 0
    for edition_year in ARTICLE_91_92_SNAPSHOT_YEARS:
        for lister in (list_article_91_subitems, list_article_92_subitems):
            for item in lister(edition_year):
                total += 1
                assert item.is_subitem
                assert item.parent_item_id
                assert item.nesting_depth >= 1
                assert item.itemization in {"nested_bullet", "nested_letter"}
                assert item.item_role in {"leaf", "container"}
                assert item.quote.strip()
                # The packaged ID is stable and ASCII; the corpus ID is kept too.
                assert _ASCII_ID.match(item.item_id)
                assert item.source_item_id
    assert total == 603


def test_every_subitem_names_a_parent_that_contains_it():
    """A sub-item's parent is a real row in the same snapshot, and is shallower."""
    for edition_year in ARTICLE_91_92_SNAPSHOT_YEARS:
        for article, lister in (
            (91, list_article_91_subitems),
            (92, list_article_92_subitems),
        ):
            rows = {
                item.item_id: item
                for item in lister(edition_year)
                + (
                    list_article_91_items(edition_year)
                    if article == 91
                    else list_article_92_items(edition_year)
                )
            }
            for item in lister(edition_year):
                parent = rows[item.parent_item_id]
                assert parent.article == item.article
                assert parent.edition_year == edition_year
                assert parent.nesting_depth == item.nesting_depth - 1


def test_article_92_2007_keeps_consecutive_clause_numbering():
    """Regression: clauses 17° and 31° must not be merged into a neighbour.

    An earlier packaging pass joined 17° into the 16° row (and 31° into its
    predecessor) and then re-derived sequential IDs, so 24 packaged IDs named a
    different clause in the corpus. Both clauses are distinct legal exemptions
    and must be individually addressable.
    """
    items = {
        item.clause_number: item
        for item in list_article_92_items(2007)
        if item.clause_number is not None
    }
    assert sorted(items) == [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21,
        22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
        40, 41, 42,
    ]  # fmt: skip

    assert "Fondation Cheikh" in items[17].quote
    assert items[17].item_id == "2007-art92-clause-016"
    assert "Sala Al-Jadida" in items[31].quote
    assert items[31].item_id == "2007-art92-clause-030"

    # No clause number is claimed by two rows.
    numbers = [
        item.clause_number
        for item in list_article_92_items(2007)
        if item.clause_number is not None
    ]
    assert len(numbers) == len(set(numbers))


def test_packaged_ids_never_alias_a_different_clause():
    """Regression: an ID must resolve to the same clause in package and corpus."""
    for edition_year in ARTICLE_91_92_SNAPSHOT_YEARS:
        for article, lister in (
            (91, list_article_91_items),
            (92, list_article_92_items),
        ):
            for item in lister(edition_year):
                assert item.item_id == item.source_item_id
                if item.itemization == "article_level":
                    assert item.clause_number is None
                    continue
                # A numbered clause's printed marker must match its own number,
                # so a shifted ID cannot silently point at a neighbour.
                marker = re.match(r"\s*(\d+)\s*°", item.quote)
                if marker is not None:
                    assert int(marker.group(1)) == item.clause_number


def test_abrogated_clauses_keep_their_printed_status():
    """Regression: a repeal stub must not be published as in force."""
    abrogated = [item for item in _all_rows() if item.is_abrogated]
    assert abrogated
    for item in abrogated:
        assert "(abrogé)" in item.quote or "abrogé" in item.quote
        assert item.status == "abrogated"


@pytest.mark.skipif(
    not _HOLY_GRAPH.is_dir(), reason="Holy Graph corpus is not present locally"
)
def test_every_packaged_row_is_verbatim_from_the_corpus():
    """Every row's quote and status match the corpus row it names."""
    dataset = _HOLY_GRAPH / "laws/ma_tax_law/data/consolidated/tva_article_lists.json"
    corpus = json.loads(dataset.read_text(encoding="utf-8"))
    source = {row["item_id"]: row for row in corpus["items"]}

    checked = 0
    for edition_year in ARTICLE_91_92_SNAPSHOT_YEARS:
        for item in _all_rows():
            if item.edition_year != edition_year:
                continue
            origin = source[item.source_item_id]
            assert origin["quote"] == item.quote
            assert origin["status"] == item.status
            assert origin.get("clause_number") == item.clause_number
            assert origin["article"] == item.article
            checked += 1
    assert checked == 1209


@pytest.mark.skipif(
    not _HOLY_GRAPH.is_dir(), reason="Holy Graph corpus is not present locally"
)
def test_declared_snapshot_hashes_match_their_artifacts():
    """The two published snapshot hashes are re-computed from the artifacts."""
    catalog = _catalog()

    def digest(path):
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                hasher.update(block)
        return hasher.hexdigest()

    checked = 0
    for edition in catalog["editions"]:
        for field, path_field in (
            ("source_pdf_sha256", "source_pdf"),
            ("source_text_sha256", "corpus_file"),
        ):
            artifact = _HOLY_GRAPH / edition[path_field]
            assert artifact.is_file(), edition[path_field]
            assert digest(artifact) == edition[field], edition[path_field]
            checked += 1
    assert checked == 14
