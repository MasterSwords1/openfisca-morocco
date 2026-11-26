"""Unit tests for CNSS Family Allowances (Allocations familiales).

Tests the statutory rules encoded from:
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 (articles 40 et 41)
- Décret n° 2-72-541, article 6 (âges limites)
- Décret n° 2-08-358, modifié par les décrets n° 2-19-750 et n° 2-23-715
  (montants)
- Corpus `morocco-holy-graph` dataset only as a historical cross-check; the
  amounts and ages follow Décrets 2-08-358 / 2-19-750 / 2-23-715 and 2-72-541
  art. 6.
"""

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

import openfisca_morocco

CHILD = {"birth": {"ETERNITY": "2015-01-01"}}


@pytest.fixture
def tbs():
    return openfisca_morocco.CountryTaxBenefitSystem()


def test_family_allowance_grid_parameters(tbs):
    params = tbs.parameters("2025-01").prestations_sociales.allocations_familiales.cnss
    assert params.plafond_enfants == 6
    assert params.montant_enfants_1_a_3 == 300.0
    assert params.montant_enfants_4_a_6 == 100.0


def test_family_allowances_progression(tbs):
    expected_scale = {
        0: 0.0,
        1: 300.0,
        2: 600.0,
        3: 900.0,
        4: 1000.0,
        5: 1100.0,
        6: 1200.0,
        7: 1200.0,
        10: 1200.0,
    }

    sb = SimulationBuilder()
    households_def = {}
    persons_def = {}

    for count in expected_scale:
        h_id = f"famille_{count}"
        adult_id = f"adult_{count}"
        persons_def[adult_id] = {}
        child_ids = [f"child_{count}_{i}" for i in range(count)]
        for cid in child_ids:
            persons_def[cid] = dict(CHILD)
        households_def[h_id] = {
            "adults": [adult_id],
            "children": child_ids,
        }

    sim = sb.build_from_entities(
        tbs,
        {
            "households": households_def,
            "persons": persons_def,
        },
    )

    hh = sim.household
    actual_amounts = hh("allocations_familiales", "2025-01")
    actual_counts = hh("nombre_enfants", "2025-01")

    for idx, count in enumerate(expected_scale.keys()):
        assert actual_counts[idx] == count
        assert actual_amounts[idx] == pytest.approx(expected_scale[count], abs=1e-5)


def test_family_allowances_direct_input_override(tbs):
    sb = SimulationBuilder()
    sim = sb.build_from_dict(
        tbs,
        {
            "persons": {"p1": {}},
            "households": {
                "f1": {"adults": ["p1"], "nombre_enfants": {"2025-01": 5}},
            },
        },
    )
    hh = sim.household
    assert hh("nombre_enfants", "2025-01")[0] == 5
    assert hh("allocations_familiales", "2025-01")[0] == pytest.approx(1100.0, abs=1e-5)


def test_family_allowances_salary_independence(tbs):
    """Statutory check: Under Dahir 1-72-184 Art. 40-41, family allowances are flat rate per child.

    The employer pays 6.40% contribution on gross salary, while the employee receives
    the statutory allowance regardless of whether their gross salary is 0, below ceiling (4,000 DH),
    at ceiling (6,000 DH), or high above ceiling (50,000 DH).
    """
    sb = SimulationBuilder()
    sim = sb.build_from_dict(
        tbs,
        {
            "persons": {
                "low": {"salaire_brut": {"2025-01": 3000}},
                "mid": {"salaire_brut": {"2025-01": 6000}},
                "high": {"salaire_brut": {"2025-01": 50000}},
                "c1": dict(CHILD),
                "c2": dict(CHILD),
                "c3": dict(CHILD),
            },
            "households": {
                "h_low": {"adults": ["low"], "children": ["c1"]},
                "h_mid": {"adults": ["mid"], "children": ["c2"]},
                "h_high": {"adults": ["high"], "children": ["c3"]},
            },
        },
    )
    hh = sim.household
    af = hh("allocations_familiales", "2025-01")
    assert af[0] == 300.0
    assert af[1] == 300.0
    assert af[2] == 300.0


def _benefit(tbs, child, period="2025-01"):
    simulation = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "adult": {"birth": {"ETERNITY": "1980-01-01"}},
                "child": child,
            },
            "households": {
                "family": {"adults": ["adult"], "children": ["child"]},
            },
        },
    )
    return float(simulation.calculate("allocations_familiales", period)[0])


def test_age_boundaries_and_schooling_branches(tbs):
    assert _benefit(tbs, {"birth": {"ETERNITY": "2013-06-01"}}) == 300  # 11
    assert _benefit(tbs, {"birth": {"ETERNITY": "2013-01-01"}}) == 0  # 12, no flag
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2013-01-01"},
                "enfant_scolarise_cnss": {"2025-01": True},
            },
        )
        == 300
    )
    assert _benefit(tbs, {"birth": {"ETERNITY": "2007-06-01"}}) == 0  # 17, no flag
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2007-06-01"},
                "enfant_apprenti_cnss": {"2025-01": True},
            },
        )
        == 300
    )
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2007-01-01"},
                "enfant_apprenti_cnss": {"2025-01": True},
            },
        )
        == 0
    )  # 18, apprenticeship ends before 18
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2007-01-01"},
                "enfant_scolarise_cnss": {"2025-01": True},
            },
        )
        == 300
    )  # 18, studies continue to 21
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2005-01-01"},
                "enfant_etudes_superieures_cnss": {"2025-01": True},
            },
        )
        == 300
    )  # 20
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2005-01-01"},
                "enfant_scolarise_cnss": {"2025-01": True},
            },
        )
        == 300
    )  # 20, scolarisé
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2004-01-01"},
                "enfant_scolarise_cnss": {"2025-01": True},
            },
        )
        == 0
    )  # 21, scolarisé, excluded
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2007-01-01"},
                "enfant_etudes_superieures_cnss": {"2025-01": True},
            },
        )
        == 300
    )  # 18, higher studies start at 18
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2008-01-01"},
                "enfant_etudes_superieures_cnss": {"2025-01": True},
            },
        )
        == 300
    )  # 17, studies (including higher) up to 21
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2004-01-01"},
                "enfant_etudes_superieures_cnss": {"2025-01": True},
            },
        )
        == 0
    )  # 21, higher studies end before 21


def test_higher_study_flag_is_a_study_variant_from_12(tbs):
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2013-01-01"},
                "enfant_etudes_superieures_cnss": {"2025-01": True},
            },
        )
        == 300
    )


def test_child_born_during_the_month_is_entitled_for_that_month(tbs):
    assert _benefit(tbs, {"birth": {"ETERNITY": "2025-01-15"}}) == 300
    assert _benefit(tbs, {"birth": {"ETERNITY": "2025-02-01"}}) == 0


def test_future_birth_is_not_eligible(tbs):
    assert _benefit(tbs, {"birth": {"ETERNITY": "2030-01-01"}}) == 0


def test_missing_birth_is_excluded_from_age_bands_but_not_from_disability(tbs):
    assert _benefit(tbs, {}) == 0
    assert (
        _benefit(
            tbs,
            {
                "enfant_handicape_cnss": {"2025-01": True},
                "enfant_handicape_sans_revenu_cnss": {"2025-01": True},
            },
        )
        == 300
    )


def test_leap_day_birth_follows_the_month_start_convention(tbs):
    child = {
        "birth": {"ETERNITY": "2004-02-29"},
        "enfant_scolarise_cnss": {
            "2025-01": True,
            "2025-02": True,
            "2025-03": True,
        },
    }
    assert _benefit(tbs, child, "2025-01") == 300  # still 20
    assert _benefit(tbs, child, "2025-02") == 300  # still 20 on 1 February
    assert _benefit(tbs, child, "2025-03") == 0  # 21 after the anniversary


def test_disabled_child_without_age_limit_only_without_income(tbs):
    base = {"birth": {"ETERNITY": "1990-01-01"}}
    assert (
        _benefit(
            tbs,
            {**base, "enfant_handicape_sans_revenu_cnss": {"2025-01": True}},
        )
        == 0
    )
    assert _benefit(tbs, {**base, "enfant_handicape_cnss": {"2025-01": True}}) == 0
    assert (
        _benefit(
            tbs,
            {
                **base,
                "enfant_handicape_cnss": {"2025-01": True},
                "enfant_handicape_sans_revenu_cnss": {"2025-01": True},
            },
        )
        == 300
    )


def test_child_over_21_without_disability_not_eligible(tbs):
    assert _benefit(tbs, {"birth": {"ETERNITY": "2002-06-01"}}) == 0


def test_disabled_adult_in_adult_role_is_not_a_child(tbs):
    simulation = SimulationBuilder().build_from_dict(
        tbs,
        {
            "persons": {
                "adult": {"birth": {"ETERNITY": "1980-01-01"}},
                "disabled_adult": {
                    "birth": {"ETERNITY": "1990-01-01"},
                    "enfant_handicape_cnss": {"2025-01": True},
                    "enfant_handicape_sans_revenu_cnss": {"2025-01": True},
                },
            },
            "households": {
                "family": {"adults": ["adult", "disabled_adult"]},
            },
        },
    )
    assert float(simulation.calculate("nombre_enfants", "2025-01")[0]) == 0


def test_retroactive_100_dh_from_january_2023(tbs):
    cases = [
        ("2022-12", 4, 936.0),
        ("2023-01", 4, 1000.0),
        ("2022-12", 6, 1008.0),
        ("2023-01", 6, 1200.0),
    ]
    for period, count, expected in cases:
        simulation = SimulationBuilder().build_from_dict(
            tbs,
            {
                "persons": {"adult": {}},
                "households": {
                    "family": {
                        "adults": ["adult"],
                        "nombre_enfants": {period: count},
                    }
                },
            },
        )
        assert float(
            simulation.calculate("allocations_familiales", period)[0]
        ) == pytest.approx(expected)


def test_disabled_child_12_to_17_eligible_without_schooling(tbs):
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2010-01-01"},
                "enfant_handicape_cnss": {"2025-01": True},
                "enfant_handicape_sans_revenu_cnss": {"2025-01": True},
            },
        )
        == 300
    )


def test_twelve_year_old_apprentice_eligible(tbs):
    assert (
        _benefit(
            tbs,
            {
                "birth": {"ETERNITY": "2013-01-01"},
                "enfant_apprenti_cnss": {"2025-01": True},
            },
        )
        == 300
    )


def test_child_born_on_last_day_of_month_eligible(tbs):
    assert _benefit(tbs, {"birth": {"ETERNITY": "2025-01-31"}}) == 300
