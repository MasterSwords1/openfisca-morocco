"""Unit tests for CNSS Family Allowances (Allocations familiales).

Tests the statutory rules encoded from:
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 (articles 38 à 41)
- Décret n° 2-19-461 du 19 juillet 2019
- Corpus `morocco-holy-graph` dataset `laws/ma_social_protection/data/family_allowances_grid.json`
"""

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

import openfisca_morocco
from openfisca_morocco.entities import Household


@pytest.fixture
def tbs():
    return openfisca_morocco.CountryTaxBenefitSystem()


def test_family_allowance_grid_parameters(tbs):
    params = tbs.parameters("2025-01").prestations_sociales.allocations_familiales.cnss
    assert params.plafond_enfants == 6
    assert params.montant_enfants_1_a_3 == 300.0
    assert params.montant_enfants_4_a_6 == 36.0


def test_family_allowances_progression(tbs):
    expected_scale = {
        0: 0.0,
        1: 300.0,
        2: 600.0,
        3: 900.0,
        4: 936.0,
        5: 972.0,
        6: 1008.0,
        7: 1008.0,
        10: 1008.0,
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
            persons_def[cid] = {}
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
    assert hh("allocations_familiales", "2025-01")[0] == pytest.approx(972.0, abs=1e-5)


def test_family_allowances_salary_independence(tbs):
    """Statutory check: Under Dahir 1-72-184 Art. 38-41, family allowances are flat rate per child.

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
                "c1": {},
                "c2": {},
                "c3": {},
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
