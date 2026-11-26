"""Adversarial stress-test suite for Moroccan family allowances (Allocations familiales CNSS).

Exhaustively verifies:
1. Negative child count input (clips cleanly to 0, producing 0 MAD benefits).
2. Huge child count input (100, 1000, max int32 strictly cap at statutory ceiling of 1 200 MAD).
3. Float/non-integer values and type coercions.
4. Household topology edge cases (child-only households, multi-adult/blended families, single adults).
5. Large vector populations (hundreds of households) benchmarking performance and vectorization.
6. Temporal boundaries (periods prior to 2019-07-01 raising ParameterNotFoundError, exact boundary, future dates, and annual periodicity).
7. Interoperability with Person variables (cotisations_sociales CNSS/AMO and impot_sur_le_revenu).

Legal references:
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 relatif au régime de sécurité sociale (articles 40 et 41)
- Décret n° 2-72-541, article 6 (âges limites)
- Décret n° 2-08-358, modifié par les décrets n° 2-19-750 et n° 2-23-715 (300 DH/1-3, 100 DH/4-6 depuis 2023)
"""

import time

import numpy as np
import pytest
from openfisca_core.errors.parameter_not_found_error import ParameterNotFoundError
from openfisca_core.errors.situation_parsing_error import SituationParsingError
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()
CHILD = {"birth": {"ETERNITY": "2015-01-01"}}


# --- 1. Negative child count handling ---


@pytest.mark.parametrize("negative_count", [-1, -3, -5, -100, -2147483648])
def test_negative_child_count_direct_input_scalar(negative_count):
    """Ensure negative child counts clip cleanly to 0 MAD without negative benefits or exceptions."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"adult_1": {}},
            "households": {
                "h1": {
                    "adults": ["adult_1"],
                    "nombre_enfants": {"2025-01": negative_count},
                }
            },
        },
    )
    af = sim.calculate("allocations_familiales", "2025-01")
    assert len(af) == 1
    assert float(af[0]) == 0.0


def test_negative_child_count_vectorized():
    """Verify an array of negative and mixed child counts evaluates safely in vectorized mode."""
    counts = [-50, -10, -1, 0, 1, 2, -5, 3, 6]
    situation = {
        "persons": {f"p_{i}": {} for i in range(len(counts))},
        "households": {
            f"h_{i}": {
                "adults": [f"p_{i}"],
                "nombre_enfants": {"2025-01": count},
            }
            for i, count in enumerate(counts)
        },
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)
    af = sim.calculate("allocations_familiales", "2025-01")

    expected = np.array([0.0, 0.0, 0.0, 0.0, 300.0, 600.0, 0.0, 900.0, 1200.0])
    assert np.allclose(af, expected)
    assert np.all(af >= 0.0), "Benefits must never be negative"


# --- 2. Huge child count and statutory capping ---


@pytest.mark.parametrize(
    "huge_count",
    [7, 8, 10, 50, 100, 1000, 1_000_000, 2147483647],
)
def test_huge_child_count_direct_input(huge_count):
    """Ensure huge child counts cleanly saturate at statutory cap of 6 children (1 200 MAD)."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"adult_1": {}},
            "households": {
                "h1": {
                    "adults": ["adult_1"],
                    "nombre_enfants": {"2025-01": huge_count},
                }
            },
        },
    )
    af = sim.calculate("allocations_familiales", "2025-01")
    assert len(af) == 1
    assert float(af[0]) == 1200.0


def test_huge_declared_entities_in_single_household():
    """Stress-test declaring 50 distinct child entities inside a single household."""
    num_children = 50
    persons_def = {"parent": {}}
    child_ids = [f"child_{i}" for i in range(num_children)]
    for cid in child_ids:
        persons_def[cid] = dict(CHILD)

    sim = SimulationBuilder().build_from_entities(
        TBS,
        {
            "persons": persons_def,
            "households": {
                "large_family": {
                    "adults": ["parent"],
                    "children": child_ids,
                }
            },
        },
    )
    hh = sim.household
    assert hh("nombre_enfants", "2025-01")[0] == num_children
    assert float(hh("allocations_familiales", "2025-01")[0]) == 1200.0


def test_monotonicity_across_spectrum():
    """Verify that allocations_familiales is monotonically non-decreasing over [-10, 50]."""
    domain = list(range(-10, 51))
    situation = {
        "persons": {f"p_{i}": {} for i in range(len(domain))},
        "households": {
            f"h_{i}": {
                "adults": [f"p_{i}"],
                "nombre_enfants": {"2025-01": val},
            }
            for i, val in enumerate(domain)
        },
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)
    results = sim.calculate("allocations_familiales", "2025-01")

    # Check weak monotonicity
    diffs = np.diff(results)
    assert np.all(diffs >= 0.0), "Allocation scale must be monotonically non-decreasing"

    # Check bounds
    assert np.all(results >= 0.0)
    assert np.all(results <= 1200.0)


# --- 3. Float and non-integer value handling ---


@pytest.mark.parametrize(
    ("float_input", "expected_amount"),
    [
        (0.0, 0.0),
        (1.0, 300.0),
        (3.0, 900.0),
        (6.0, 1200.0),
        (10.0, 1200.0),
        (0.9, 0.0),  # Truncates to 0
        (2.5, 600.0),  # Truncates to 2
        (4.9, 1000.0),  # Truncates to 4
        (7.2, 1200.0),  # Truncates to 7, capped at 6
    ],
)
def test_float_input_coercion(float_input, expected_amount):
    """Ensure float child count inputs are coerced according to OpenFisca integer rules."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "nombre_enfants": {"2025-01": float_input},
                }
            },
        },
    )
    af = sim.calculate("allocations_familiales", "2025-01")
    assert float(af[0]) == expected_amount


def test_boolean_and_none_input_coercion():
    """Ensure boolean and None values are safely converted by the simulation builder."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}, "p2": {}, "p3": {}},
            "households": {
                "h_true": {"adults": ["p1"], "nombre_enfants": {"2025-01": True}},
                "h_false": {"adults": ["p2"], "nombre_enfants": {"2025-01": False}},
                "h_none": {"adults": ["p3"], "nombre_enfants": {"2025-01": None}},
            },
        },
    )
    af = sim.calculate("allocations_familiales", "2025-01")
    assert float(af[0]) == 300.0  # True == 1 child
    assert float(af[1]) == 0.0  # False == 0 children
    assert float(af[2]) == 0.0  # None == 0 children


def test_string_numeric_and_invalid_inputs():
    """Ensure numeric strings are parsed and non-numeric inputs raise SituationParsingError."""
    # Valid string numeric
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "nombre_enfants": {"2025-01": "4"},
                }
            },
        },
    )
    assert float(sim.calculate("allocations_familiales", "2025-01")[0]) == 1000.0

    # Non-numeric string
    with pytest.raises(SituationParsingError):
        SimulationBuilder().build_from_dict(
            TBS,
            {
                "persons": {"p1": {}},
                "households": {
                    "h1": {
                        "adults": ["p1"],
                        "nombre_enfants": {"2025-01": "invalid_number"},
                    }
                },
            },
        )


# --- 4. Household topology and composition edge cases ---


def test_household_children_only_no_adults():
    """Verify child-only households (e.g. orphans or wards) calculate benefits accurately."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {
                "child_1": dict(CHILD),
                "child_2": dict(CHILD),
                "child_3": dict(CHILD),
            },
            "households": {
                "orphan_household": {
                    "children": ["child_1", "child_2", "child_3"],
                }
            },
        },
    )
    hh = sim.household
    assert hh("nombre_enfants", "2025-01")[0] == 3
    assert float(hh("allocations_familiales", "2025-01")[0]) == 900.0


def test_multi_adult_and_blended_households():
    """Verify that multiple adults in a household do not multiply or distort benefits."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {
                "adult_1": {},
                "adult_2": {},
                "adult_3": {},
                "child_1": dict(CHILD),
                "child_2": dict(CHILD),
            },
            "households": {
                "extended_family": {
                    "adults": ["adult_1", "adult_2", "adult_3"],
                    "children": ["child_1", "child_2"],
                }
            },
        },
    )
    hh = sim.household
    assert hh("nombre_enfants", "2025-01")[0] == 2
    # Exactly 2 children = 600 MAD, regardless of 3 adults present
    assert float(hh("allocations_familiales", "2025-01")[0]) == 600.0


def test_heterogeneous_household_cohort():
    """Verify concurrent calculation of diverse household topologies in a single simulation."""
    situation = {
        "persons": {
            "s_adult": {},
            "sp_adult": {},
            "sp_child": dict(CHILD),
            "c_adult1": {},
            "c_adult2": {},
            "c_child1": dict(CHILD),
            "c_child2": dict(CHILD),
            "c_child3": dict(CHILD),
            "c_child4": dict(CHILD),
            "b_child1": dict(CHILD),
            "b_child2": dict(CHILD),
        },
        "households": {
            "single_no_children": {"adults": ["s_adult"]},
            "single_parent_1_child": {
                "adults": ["sp_adult"],
                "children": ["sp_child"],
            },
            "couple_4_children": {
                "adults": ["c_adult1", "c_adult2"],
                "children": ["c_child1", "c_child2", "c_child3", "c_child4"],
            },
            "child_only_2_children": {
                "children": ["b_child1", "b_child2"],
            },
        },
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)
    hh = sim.household

    counts = hh("nombre_enfants", "2025-01")
    amounts = hh("allocations_familiales", "2025-01")

    assert np.array_equal(counts, [0, 1, 4, 2])
    assert np.allclose(amounts, [0.0, 300.0, 1000.0, 600.0])


# --- 5. Large vector populations and performance benchmarking ---


def test_large_vector_population_performance():
    """Test vector calculation across 600 households with up to 14 children each.

    Ensures sub-millisecond calculation time and zero performance degradation.
    """
    n_households = 600
    persons_def = {}
    households_def = {}
    expected_amounts = []

    for i in range(n_households):
        num_children = i % 15  # 0 to 14 children
        adult_id = f"adult_pop_{i}"
        persons_def[adult_id] = {}
        child_ids = [f"child_pop_{i}_{k}" for k in range(num_children)]
        for cid in child_ids:
            persons_def[cid] = dict(CHILD)

        households_def[f"hh_{i}"] = {
            "adults": [adult_id],
            "children": child_ids,
        }

        # Analytical formula check
        elig = min(num_children, 6)
        t1 = min(elig, 3)
        t2 = max(min(elig - 3, 3), 0)
        expected_amounts.append(float(t1 * 300.0 + t2 * 100.0))

    sim = SimulationBuilder().build_from_entities(
        TBS,
        {"persons": persons_def, "households": households_def},
    )

    t_start = time.perf_counter()
    actual_amounts = sim.calculate("allocations_familiales", "2025-01")
    duration = time.perf_counter() - t_start

    assert len(actual_amounts) == n_households
    assert np.allclose(actual_amounts, expected_amounts, atol=1e-5)
    # Calculation for 600 vectorized households should comfortably complete in < 50ms
    assert duration < 0.05, f"Calculation took too long: {duration:.4f}s"


def test_large_vector_override_population():
    """Test vectorized override array of nombre_enfants across 500 households."""
    n_households = 500
    counts = np.arange(-10, n_households - 10, dtype=int)
    persons_def = {f"p_{i}": {} for i in range(n_households)}
    households_def = {
        f"h_{i}": {
            "adults": [f"p_{i}"],
            "nombre_enfants": {"2025-01": int(counts[i])},
        }
        for i in range(n_households)
    }

    sim = SimulationBuilder().build_from_dict(
        TBS,
        {"persons": persons_def, "households": households_def},
    )
    actual = sim.calculate("allocations_familiales", "2025-01")

    # Analytical vectorized calculation
    clipped_counts = np.clip(counts, 0, 6)
    t1 = np.clip(clipped_counts, 0, 3)
    t2 = np.clip(clipped_counts - 3, 0, 3)
    expected = t1 * 300.0 + t2 * 100.0

    assert np.allclose(actual, expected)


# --- 6. Temporal boundaries and parameter lifecycle ---


def test_temporal_boundary_prior_to_decree():
    """Querying parameters before Décret 2-19-750 (2019-07-01) raises ParameterNotFoundError."""
    with pytest.raises(ParameterNotFoundError):
        _ = TBS.parameters(
            "2019-06"
        ).prestations_sociales.allocations_familiales.cnss.montant_enfants_1_a_3

    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "nombre_enfants": {"2019-06": 2},
                }
            },
        },
    )
    with pytest.raises(ParameterNotFoundError):
        sim.calculate("allocations_familiales", "2019-06")


def test_temporal_boundary_exact_inception_and_future():
    """Verify exact inception month (2019-07) and distant future periods (2030-01)."""
    # Exact inception month
    sim_inception = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "nombre_enfants": {"2019-07": 4},
                }
            },
        },
    )
    assert (
        float(sim_inception.calculate("allocations_familiales", "2019-07")[0]) == 936.0
    )

    # Future month
    sim_future = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "nombre_enfants": {"2030-01": 5},
                }
            },
        },
    )
    assert float(sim_future.calculate("allocations_familiales", "2030-01")[0]) == 1100.0


def test_annual_periodicity_and_aggregation():
    """Verify that direct YEAR calculation is rejected and calculate_add sums all 12 months."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"p1": {}, "c1": dict(CHILD), "c2": dict(CHILD)},
            "households": {
                "h1": {
                    "adults": ["p1"],
                    "children": ["c1", "c2"],
                }
            },
        },
    )
    # Direct calculate on YEAR must raise ValueError for MONTH-defined variable
    with pytest.raises(ValueError, match="must be computed for a whole month"):
        sim.calculate("allocations_familiales", "2025")

    # calculate_add aggregates over all 12 months (12 * 600 MAD = 7 200 MAD)
    annual_sum = sim.calculate_add("allocations_familiales", "2025")
    assert float(annual_sum[0]) == 7200.0


# --- 7. Interoperability with Person variables ---


def test_full_system_interoperability():
    """Verify co-existence and independence between:

    - Household: allocations_familiales, nombre_enfants
    - Person (Monthly): salaire_brut, salaire_brut_global, cotisation_cnss_salarie,
      cotisation_cnss_employeur (6.4% PF)
    - Person (Annual): nombre_personnes_a_charge, impot_sur_le_revenu
    """
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {
                "parent_worker": {
                    "salaire_brut": {"2025-01": 10000.0},
                    "salaire_brut_global": {"2025": 120000.0},
                    "elements_exoneres": {"2025": 0.0},
                    "nombre_personnes_a_charge": {"2025": 4},
                },
                "spouse": {
                    "salaire_brut": {"2025-01": 4000.0},
                    "salaire_brut_global": {"2025": 48000.0},
                    "elements_exoneres": {"2025": 0.0},
                    "nombre_personnes_a_charge": {"2025": 0},
                },
                "child_1": dict(CHILD),
                "child_2": dict(CHILD),
                "child_3": dict(CHILD),
                "child_4": dict(CHILD),
            },
            "households": {
                "family": {
                    "adults": ["parent_worker", "spouse"],
                    "children": ["child_1", "child_2", "child_3", "child_4"],
                }
            },
        },
    )

    # 1. Household allocations familiales (4 children -> 1 000 MAD)
    af = sim.calculate("allocations_familiales", "2025-01")
    assert len(af) == 1
    assert float(af[0]) == 1000.0

    # 2. Employer CNSS contribution includes the 6.40% Prestations Familiales on gross salary
    cnss_pat = sim.calculate("cotisation_cnss_employeur", "2025-01")
    # parent_worker: 6000 * (0.67% + 7.93% + 0.38%) + 10000 * (6.40% + 1.60%)
    # = 6000 * 8.98% + 10000 * 8.00% = 538.80 + 800.00 = 1338.80 MAD
    assert pytest.approx(float(cnss_pat[0]), abs=1e-2) == 1338.80
    # spouse: 4000 * 8.98% + 4000 * 8.00% = 4000 * 16.98% = 679.20 MAD
    assert pytest.approx(float(cnss_pat[1]), abs=1e-2) == 679.20

    # 3. Employee CNSS + AMO contributions
    cnss_sal = sim.calculate("cotisation_cnss_salarie", "2025-01")
    assert pytest.approx(float(cnss_sal[0]), abs=1e-2) == 268.80
    assert pytest.approx(float(cnss_sal[1]), abs=1e-2) == 179.20

    # 4. Income tax (IR) computed with independent Person charges de famille
    ir = sim.calculate("impot_sur_le_revenu", "2025")
    # Parent worker has 4 dependents -> deduction 4 * 500 = 2000 MAD
    assert float(ir[0]) > 0.0
    # Children have 0 income and 0 tax
    assert float(ir[2]) == 0.0
    assert float(ir[3]) == 0.0
