"""Tests for the explicit, snapshot-scoped Article 99 catalog lookup."""

import hashlib
import json
import os
import re
from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib import resources
from pathlib import Path

import pytest

from openfisca_morocco.tva_article99 import (
    ARTICLE_99_SNAPSHOT_YEARS,
    Article99AmendmentCitation,
    Article99ItemNotFoundError,
    Article99TransitionalRateError,
    Article99UndatedItemError,
    UnsupportedArticle99EditionError,
    aggregate_article_99_turnover,
    get_article_99_item,
    get_article_99_subitem,
    list_article_99_items,
    list_article_99_subitems,
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
            citation_fields = (
                "endnote",
                "endnote_label",
                "endnote_suffix",
                "law",
                "law_article",
                "budget_year",
                "source_edition",
                "corpus_file",
                "source_sha256",
                "quote",
                "amending_law_corpus_file",
                "amending_law_source_sha256",
                "amending_law_article_quote",
                "articles_mentioned",
                "source_scope",
            )
            assert all(
                isinstance(citation, Article99AmendmentCitation)
                for citation in item.amendment_citations
            )
            assert [
                {
                    field: (
                        list(getattr(citation, field))
                        if field == "articles_mentioned"
                        else getattr(citation, field)
                    )
                    for field in citation_fields
                }
                for citation in item.amendment_citations
            ] == (row.get("amendment_citations") or [])
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
            # Effective dates live only inside the parsed attribution.
            assert item.effective_attribution is not None
            assert item.effective_attribution.rate == row["rate"]
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


def test_ambiguous_page_footer_notes_are_not_assigned_to_neighbor_items():
    item = get_article_99_item(2014, "2014-art99-7pct-008")

    assert item.quote == "le lait en poudre ;"
    assert item.right_to_deduct is True
    assert item.source_endnote_labels is None
    assert item.amendment_citations == ()

    farm_equipment = get_article_99_item(2018, "2018-art99-10pct-024")
    assert farm_equipment.source_endnote_labels is None
    assert [
        (citation.endnote, citation.law, citation.law_article)
        for citation in farm_equipment.amendment_citations
    ] == [(376, "Loi n° 110-13", 4)]


def test_item_returns_its_amending_law_citations():
    item = get_article_99_item(2018, "2018-art99-10pct-009")

    assert item.quote.endswith("pailles ;370")
    assert item.right_to_deduct is True
    assert len(item.amendment_citations) == 2
    citation = item.amendment_citations[0]
    assert citation.law == "Loi n° 115-12"
    assert citation.law_article == 9
    assert citation.source_scope == "item_quote"
    assert citation.corpus_file.endswith("CGI-2018-FR.pdf.txt")
    assert citation.source_sha256
    assert citation.amending_law_corpus_file.endswith("FL_2013_115-12.txt")
    assert citation.amending_law_source_sha256
    assert "article 99" in citation.amending_law_article_quote.lower()
    assert citation.articles_mentioned == (99,)
    assert item.amendment_citations[1].law == "Loi n° 110-13"
    assert item.amendment_citations[1].law_article == 4


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


def test_explicit_article_99_item_ids_aggregate_turnover_by_rate():
    turnover = aggregate_article_99_turnover(
        2024,
        {
            "2024-art99-general-20pct": Decimal(1000),
            "2024-art99-10pct-001": Decimal(400),
            "2024-art99-10pct-002": Decimal(100),
        },
    )

    assert dict(turnover) == {
        "20%": Decimal(1000),
        "10%": Decimal(500),
    }
    with pytest.raises(TypeError):
        turnover["10%"] = Decimal(0)


def test_aggregation_rejects_transitional_categories_and_bad_bases():
    with pytest.raises(
        Article99TransitionalRateError, match="tva_operation_transitoire"
    ):
        aggregate_article_99_turnover(2024, {"2024-art99-10pct-079": Decimal(100)})
    with pytest.raises(Article99ItemNotFoundError):
        aggregate_article_99_turnover(2024, {"sugar": Decimal(100)})
    with pytest.raises(ValueError, match="finite and non-negative"):
        aggregate_article_99_turnover(2024, {"2024-art99-general-20pct": Decimal(-1)})


# ---------------------------------------------------------------------------
# Effective attribution (see docs/work-packages/tva-article99-attribution.md §7)
# ---------------------------------------------------------------------------

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
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


def _all_items():
    for edition_year in ARTICLE_99_SNAPSHOT_YEARS:
        yield from list_article_99_items(edition_year)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _proven_boundaries(item):
    attribution = item.effective_attribution
    yield "start", attribution.start
    yield "end", attribution.end


def test_proven_rows_carry_method_instrument_and_hash():
    """Acceptance test 1: a proven row is fully evidenced, not just dated."""
    proven = 0
    for item in _all_items():
        attribution = item.effective_attribution
        if attribution.status != "proven":
            continue
        proven += 1
        assert attribution.valid_from is not None
        assert attribution.first_anchor <= item.edition_year <= attribution.last_anchor
        for side, boundary in _proven_boundaries(item):
            if boundary.is_open_ended:
                assert boundary.valid_date is None
                assert boundary.still_in_force_at is not None
                continue
            assert boundary.status == "proven"
            assert boundary.valid_date is not None
            assert boundary.method in {
                "verbatim_reproduction",
                "consolidated_endnote",
                "positional_abrogation",
            }
            assert boundary.instrument is not None
            assert boundary.instrument.key
            assert (
                isinstance(boundary.witness_quote, str)
                and boundary.witness_quote.strip()
            )
            # The date is the instrument's own effective date, never interpolated.
            assert boundary.valid_date == boundary.instrument.effective_from
            if side == "start":
                assert boundary.valid_date == attribution.valid_from
            # Exactly one artifact kind is hashed, and it is hashed with the
            # matching label: a PDF hash is never passed off as a text hash.
            assert boundary.witness_kind in {
                "consolidated_endnote",
                "consolidated_edition",
                "finance_law_transcription",
                "bulletin_officiel",
            }
            if boundary.witness_pdf_sha256 is not None:
                assert _HEX64.match(boundary.witness_pdf_sha256)
            if boundary.witness_text_sha256 is not None:
                assert _HEX64.match(boundary.witness_text_sha256)
            assert boundary.witness_pdf_sha256 or boundary.witness_text_sha256
            assert boundary.witness_file
    assert proven > 0


def test_bracketed_rows_carry_no_dates():
    """Acceptance test 2 (adapted): a date exists only where it was witnessed.

    The work package originally stated that any non-proven row carries neither
    ``valid_from`` nor ``valid_to``. The implemented contract splits the two
    ends instead, because a row whose creation is endnoted but whose repeal is
    not is genuinely proven on one side only. So the invariant tested here is
    the stronger, per-side one: a date exists if and only if that side is
    witnessed, and a bracketed side carries no date and no hash.
    """
    bracketed = partial = 0
    for item in _all_items():
        attribution = item.effective_attribution
        assert attribution.status == (
            "proven"
            if attribution.start.status == attribution.end.status == "proven"
            else "bracketed"
        )
        if attribution.valid_from is not None:
            assert attribution.start.status == "proven"
            assert attribution.valid_from == attribution.start.valid_date
        if attribution.valid_to is not None:
            assert attribution.end.status == "proven"
            assert attribution.valid_to == attribution.end.valid_date

        if attribution.status == "proven":
            continue
        bracketed += 1
        # A date query never reaches a row with an unwitnessed end.
        assert not attribution.covers(date(item.edition_year, 6, 1))
        for _side, boundary in _proven_boundaries(item):
            if boundary.is_open_ended:
                assert boundary.still_in_force_at is not None
                continue
            if boundary.status == "proven":
                assert boundary.valid_date is not None
                continue
            partial += 1
            assert boundary.valid_date is None
            assert boundary.still_in_force_at is None
            assert boundary.reason
            assert boundary.bracket_earliest is not None
            assert boundary.bracket_latest is not None
            assert boundary.bracket_earliest < boundary.bracket_latest
            assert boundary.instrument is None
            assert boundary.witness_pdf_sha256 is None
            assert boundary.witness_text_sha256 is None
    assert bracketed > 0
    assert partial > 0


def test_proven_intervals_are_well_formed_and_never_disagree():
    """Acceptance test 3 (adapted): order, non-overlap, one date per segment.

    A product identity is not exposed by the loader, so the invariant is
    checked on what is: one witnessed segment must report one interval. Two
    rows that name the same segment but disagree on its dates would be a real
    defect, and a segment whose end precedes its start is impossible.
    """
    by_segment = {}
    for item in _all_items():
        attribution = item.effective_attribution
        if attribution.status != "proven":
            continue
        if attribution.valid_to is not None:
            assert attribution.valid_from < attribution.valid_to
        else:
            assert attribution.still_in_force_at is not None
            assert attribution.valid_from <= attribution.still_in_force_at
        key = (
            attribution.first_anchor,
            attribution.last_anchor,
            attribution.rate,
            attribution.valid_from,
            attribution.valid_to,
            attribution.still_in_force_at,
        )
        by_segment.setdefault(key, []).append(item)
    # Every segment is a maximal same-rate run of consecutive anchors.
    for (first, last, _rate, _from, _to, _still), items in by_segment.items():
        assert first <= last
        assert first in ARTICLE_99_SNAPSHOT_YEARS
        assert last in ARTICLE_99_SNAPSHOT_YEARS
        for item in items:
            assert first <= item.edition_year <= last
            assert item.rate == _rate


def test_renumber_is_not_a_repeal():
    """Acceptance test 4: an editorial renumber creates no dated boundary."""
    for left_id, right_id in (
        ("2007-art99-14pct-007", "2010-art99-14pct-006"),
        ("2010-art99-10pct-012", "2014-art99-10pct-014"),
    ):
        left = get_article_99_item(int(left_id[:4]), left_id)
        right = get_article_99_item(int(right_id[:4]), right_id)
        left_attribution = left.effective_attribution
        right_attribution = right.effective_attribution

        assert left.rate == right.rate
        # One unwitnessed boundary check: the two IDs are one segment, so no
        # instrument was sought between their editions.
        assert (
            left_attribution.first_anchor,
            left_attribution.last_anchor,
            left_attribution.rate,
        ) == (
            right_attribution.first_anchor,
            right_attribution.last_anchor,
            right_attribution.rate,
        )
        assert left_attribution.valid_from == right_attribution.valid_from
        assert left_attribution.valid_to == right_attribution.valid_to


def test_motorway_toll_rate_move_is_not_a_repeal():
    """Acceptance test 5: a 7 % → 10 % move is a supersession, not a repeal."""
    old = get_article_99_item(2007, "2007-art99-7pct-014")
    new = get_article_99_item(2010, "2010-art99-10pct-016")

    assert old.rate == "7%"
    assert new.rate == "10%"

    end = old.effective_attribution.end
    assert end.status == "proven"
    assert end.effect == "superseded"
    assert end.effect != "repealed"
    assert end.valid_date == date(2009, 1, 1)
    assert end.instrument.key == "40-08"

    start = new.effective_attribution.start
    assert start.status == "proven"
    assert start.valid_date == date(2009, 1, 1)
    assert start.instrument.key == "40-08"

    # Contiguous: the successor text applies on the very day the old one ends.
    assert end.valid_date == start.valid_date


def test_solar_water_heater_handoff_to_article91_is_an_exemption():
    """Acceptance test 6: leaving Article 99 for Article 91 is an exemption."""
    removed = get_article_99_item(2018, "2018-art99-10pct-008")
    assert "chauffe-eaux solaires" in removed.quote.casefold()

    end = removed.effective_attribution.end
    assert end.status == "proven"
    assert end.valid_date == date(2021, 1, 1)
    assert end.effect == "exempted"
    assert end.effect != "repealed"
    assert end.successor_article == 91
    assert end.instrument.key == "65-20"
    assert end.method == "verbatim_reproduction"

    # And it came back: the 2022 finance law re-listed it at 10 % in Article 99.
    returned = get_article_99_item(2024, "2024-art99-10pct-010")
    start = returned.effective_attribution.start
    assert start.status == "proven"
    assert start.valid_date == date(2022, 1, 1)
    assert start.instrument.key == "76-21"


def test_aggregation_rejects_undated_rows():
    """Acceptance test 7: a date query never reaches a bracketed row."""
    bracketed = get_article_99_item(2014, "2014-art99-7pct-001")
    assert bracketed.effective_attribution.status == "bracketed"

    with pytest.raises(Article99UndatedItemError, match="no proven effective dates"):
        aggregate_article_99_turnover(
            bracketed.edition_year,
            {bracketed.item_id: Decimal(100)},
            on_date=date(2014, 6, 1),
        )

    # Without a date the same row is still usable, as before.
    assert dict(
        aggregate_article_99_turnover(
            bracketed.edition_year, {bracketed.item_id: Decimal(100)}
        )
    ) == {"7%": Decimal(100)}


def test_aggregation_uses_the_witnessed_segment_when_a_date_is_given():
    item = get_article_99_item(2007, "2007-art99-7pct-014")
    attribution = item.effective_attribution
    assert attribution.status == "proven"

    # valid_to is exclusive: 2009-01-01 already belongs to the successor text.
    assert attribution.covers(date(2008, 12, 31))
    assert not attribution.covers(date(2009, 1, 1))

    assert dict(
        aggregate_article_99_turnover(
            2007, {item.item_id: Decimal(250)}, on_date=date(2008, 12, 31)
        )
    ) == {"7%": Decimal(250)}
    with pytest.raises(Article99UndatedItemError, match="not proven to be in force"):
        aggregate_article_99_turnover(
            2007, {item.item_id: Decimal(250)}, on_date=date(2009, 1, 1)
        )
    with pytest.raises(TypeError):
        aggregate_article_99_turnover(
            2007,
            {item.item_id: Decimal(1)},
            on_date=datetime(2008, 12, 31, 12, tzinfo=UTC),
        )


@pytest.mark.skipif(
    not _HOLY_GRAPH.is_dir(), reason="Holy Graph corpus is not present locally"
)
def test_declared_witness_hashes_match_their_artifacts():
    """Every hash the catalog publishes is re-computed from the artifact."""
    checked = set()
    for item in _all_items():
        for _side, boundary in _proven_boundaries(item):
            if boundary.is_open_ended or not boundary.witness_file:
                continue
            if boundary.witness_file in checked:
                continue
            checked.add(boundary.witness_file)
            path = _HOLY_GRAPH / boundary.witness_file
            assert path.is_file(), f"missing witness artifact {boundary.witness_file}"
            digest = _sha256(path)
            if boundary.witness_file.endswith(".pdf"):
                assert digest == boundary.witness_pdf_sha256, boundary.witness_file
            else:
                assert digest == boundary.witness_text_sha256, boundary.witness_file

            instrument = boundary.instrument
            witness_path = _HOLY_GRAPH / instrument.date_witness_file
            assert witness_path.is_file()
            assert _sha256(witness_path) == instrument.date_witness_text_sha256
    assert checked


# ---------------------------------------------------------------------------
# Nested sub-items (issue #6 box 6)
# ---------------------------------------------------------------------------


def _all_subitems():
    for edition_year in ARTICLE_99_SNAPSHOT_YEARS:
        yield from list_article_99_subitems(edition_year)


def test_article_99_leaves_are_itemized_rather_than_flattened():
    """Box 6: a multi-product clause keeps its billable leaves addressable."""
    total = 0
    for edition_year in ARTICLE_99_SNAPSHOT_YEARS:
        for subitem in list_article_99_subitems(edition_year):
            total += 1
            assert subitem.edition_year == edition_year
            assert subitem.parent_item_id
            assert subitem.itemization_role == "billable_leaf"
            assert subitem.itemization == "listed_clause"
            assert subitem.billable is True
            assert subitem.status == "in_force_in_snapshot"
            assert subitem.rate in {"7%", "10%", "14%", "20%"}
            assert subitem.quote.strip()
            assert subitem.corpus_file
    assert total == 134


def test_every_article_99_subitem_names_a_packaged_parent_clause():
    for edition_year in ARTICLE_99_SNAPSHOT_YEARS:
        parents = {item.item_id: item for item in list_article_99_items(edition_year)}
        for subitem in list_article_99_subitems(edition_year):
            parent = parents[subitem.parent_item_id]
            assert subitem.parent is parent
            assert subitem.rate == parent.rate
            assert subitem.right_to_deduct == parent.right_to_deduct
            # A leaf either repeats the clause-scope condition or omits it; it
            # never contradicts it. When it is empty, read ``subitem.parent``.
            assert subitem.conditions in (parent.conditions, ())


def test_article_99_subitem_inherits_its_parent_attribution_by_identity():
    """A leaf has no date of its own; it borrows the parent's dated segment."""
    resource = (
        resources.files("openfisca_morocco")
        .joinpath("data")
        .joinpath("tva_article99_catalog.json")
    )
    with resource.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    for edition in catalog["editions"]:
        for row in edition["subitems"]:
            # The packaged artifact must not store a second copy of the dates.
            assert "valid_from" not in row
            assert "valid_to" not in row
            assert "effective_attribution" not in row

    for subitem in _all_subitems():
        assert subitem.effective_attribution is subitem.parent.effective_attribution


def test_article_99_subitem_lookup_is_exact_and_edition_scoped():
    subitem = get_article_99_subitem(
        2007, "2007-art99-7pct-005-leaf-pharmaceutical-products"
    )
    assert subitem.quote == "les produits pharmaceutiques"
    assert subitem.parent_item_id == "2007-art99-7pct-005"
    assert subitem.product_key == "pharmaceutical-products"

    with pytest.raises(Article99ItemNotFoundError):
        get_article_99_subitem(2010, "2007-art99-7pct-005-leaf-pharmaceutical-products")
    with pytest.raises(Article99ItemNotFoundError):
        get_article_99_subitem(2007, "2007-art99-7pct-005")
    with pytest.raises(TypeError):
        get_article_99_subitem(2007, 5)
    with pytest.raises(ValueError):
        get_article_99_subitem(2007, "")
    with pytest.raises(UnsupportedArticle99EditionError):
        list_article_99_subitems(2004)


def test_article_99_subitem_is_frozen_and_distinct_from_its_parent():
    subitem = next(iter(_all_subitems()))
    assert subitem.item_id != subitem.parent_item_id
    with pytest.raises(FrozenInstanceError):
        subitem.quote = "rewritten"


@pytest.mark.skipif(
    not _HOLY_GRAPH.is_dir(), reason="Holy Graph corpus is not present locally"
)
def test_every_article_99_subitem_is_verbatim_from_the_corpus():
    dataset = _HOLY_GRAPH / "laws/ma_tax_law/data/consolidated/tva_article_lists.json"
    corpus = json.loads(dataset.read_text(encoding="utf-8"))
    source = {row["item_id"]: row for row in corpus["items"]}

    checked = 0
    for subitem in _all_subitems():
        origin = source[subitem.item_id]
        assert origin["quote"] == subitem.quote
        assert origin["status"] == subitem.status
        assert origin["rate"] == subitem.rate
        assert origin["parent_item_id"] == subitem.parent_item_id
        assert origin["itemization_role"] == subitem.itemization_role
        checked += 1
    assert checked == 134


@pytest.mark.skipif(
    not _HOLY_GRAPH.is_dir(), reason="Holy Graph corpus is not present locally"
)
def test_packaged_items_keep_the_exclusions_the_corpus_records():
    """Regression: 6 clauses lost their ``exclusion`` qualifier when packaged.

    The qualifier narrows the exemption (*à l'exclusion des autres aliments
    simples...*), so dropping it silently widened the clause. It is now
    projected verbatim from the corpus.
    """
    dataset = _HOLY_GRAPH / "laws/ma_tax_law/data/consolidated/tva_article_lists.json"
    corpus = json.loads(dataset.read_text(encoding="utf-8"))
    source = {
        (row["edition_year"], row["item_id"]): row
        for row in corpus["items"]
        if row.get("article") == 99
    }

    exclusions = 0
    for item in _all_items():
        origin = source[(item.edition_year, item.item_id)]
        assert origin["quote"] == item.quote
        assert origin["rate"] == item.rate
        assert [{"kind": c.kind, "quote": c.quote} for c in item.conditions] == (
            origin.get("conditions") or []
        )
        exclusions += sum(1 for c in item.conditions if c.kind == "exclusion")
    assert exclusions == 6
