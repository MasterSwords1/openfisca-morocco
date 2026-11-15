"""Adversarial stress-test suite for Moroccan social security contributions (CNSS, AMO).

Exhaustively verifies:
1. Zero salary handling (clean zero, no div-by-zero, scalar and vectorized).
2. Boundary behavior around 6 000 MAD ceiling (5999.99, 6000.00, 6000.01, and extreme 1M MAD).
3. Population vectorization across diverse multi-person cohorts.
4. Backwards compatibility (pure salaire_brut_global, explicit cotisations_sociales_obligatoires override).
5. Partial-year and non-contiguous monthly salary provisions.
6. Type, entity, period, and unit integrity.
7. Statutory rate decomposition against Dahir 1-72-184, Loi 65-00, Loi 03-14, and Décret 2-02-175.
"""

import numpy as np
import pytest
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


# --- 1. Zero salary tests ---


def test_zero_salary_scalar():
    """Verify scalar zero gross salary cleanly produces zeros across all variables."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {"persons": {"Worker": {"salaire_brut": {"2025-01": 0.0}}}},
    )
    for var in [
        "cotisation_cnss_salarie",
        "cotisation_amo_salarie",
        "cotisations_sociales_salarie",
        "cotisation_cnss_employeur",
        "cotisation_amo_employeur",
        "cotisations_sociales_employeur",
        "cout_employeur",
    ]:
        val = sim.calculate(var, "2025-01")
        assert len(val) == 1
        assert float(val[0]) == 0.0


def test_zero_salary_vectorized():
    """Verify vectorized cohort of zero salaries evaluates to all zeros."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {
                f"Worker_{i}": {"salaire_brut": {"2025-01": 0.0}} for i in range(5)
            }
        },
    )
    for var in [
        "cotisation_cnss_salarie",
        "cotisation_amo_salarie",
        "cotisations_sociales_salarie",
        "cotisation_cnss_employeur",
        "cotisation_amo_employeur",
        "cotisations_sociales_employeur",
        "cout_employeur",
    ]:
        val = sim.calculate(var, "2025-01")
        assert len(val) == 5
        assert np.all(val == 0.0)


# --- 2. Boundary tests around 6 000 MAD ceiling ---


@pytest.mark.parametrize(
    ("salary", "is_above_ceiling"),
    [
        (5999.99, False),
        (6000.00, False),
        (6000.01, True),
        (100000.00, True),
        (1000000.00, True),
    ],
)
def test_ceiling_boundaries_exact_math(salary, is_above_ceiling):
    """Stress-test exact math at and around the 6 000 MAD CNSS ceiling."""
    sim = SimulationBuilder().build_from_dict(
        TBS,
        {"persons": {"Worker": {"salaire_brut": {"2025-01": salary}}}},
    )

    base_plafonnee = min(salary, 6000.0)

    # Statutory rates
    # Employee: CNSS capped 4.48%, AMO uncapped 2.26%
    expected_cnss_sal = base_plafonnee * 0.0448
    expected_amo_sal = salary * 0.0226
    expected_tot_sal = expected_cnss_sal + expected_amo_sal

    # Employer: CNSS capped 8.98% + CNSS uncapped 8.00% (6.4% PF + 1.6% TFP)
    # Employer: AMO uncapped 4.11% (2.26% base + 1.85% solidarite)
    expected_cnss_pat = base_plafonnee * 0.0898 + salary * 0.08
    expected_amo_pat = salary * 0.0411
    expected_tot_pat = expected_cnss_pat + expected_amo_pat
    expected_cout = salary + expected_tot_pat

    # Tolerances accounts for float32 precision
    tol = max(0.01, salary * 1e-4)

    cnss_sal = float(sim.calculate("cotisation_cnss_salarie", "2025-01")[0])
    amo_sal = float(sim.calculate("cotisation_amo_salarie", "2025-01")[0])
    tot_sal = float(sim.calculate("cotisations_sociales_salarie", "2025-01")[0])

    cnss_pat = float(sim.calculate("cotisation_cnss_employeur", "2025-01")[0])
    amo_pat = float(sim.calculate("cotisation_amo_employeur", "2025-01")[0])
    tot_pat = float(sim.calculate("cotisations_sociales_employeur", "2025-01")[0])
    cout = float(sim.calculate("cout_employeur", "2025-01")[0])

    assert pytest.approx(cnss_sal, abs=tol) == expected_cnss_sal
    assert pytest.approx(amo_sal, abs=tol) == expected_amo_sal
    assert pytest.approx(tot_sal, abs=tol) == expected_tot_sal
    assert pytest.approx(cnss_pat, abs=tol) == expected_cnss_pat
    assert pytest.approx(amo_pat, abs=tol) == expected_amo_pat
    assert pytest.approx(tot_pat, abs=tol) == expected_tot_pat
    assert pytest.approx(cout, abs=tol) == expected_cout

    if is_above_ceiling:
        # At or above ceiling, CNSS salariale MUST strictly equal 268.80 MAD
        assert pytest.approx(cnss_sal, abs=1e-2) == 268.80


def test_ceiling_differential_sensitivity():
    """Verify that delta of 0.02 MAD across the boundary affects only uncapped rates."""
    sim_sub = SimulationBuilder().build_from_dict(
        TBS, {"persons": {"W": {"salaire_brut": {"2025-01": 5999.99}}}}
    )
    sim_at = SimulationBuilder().build_from_dict(
        TBS, {"persons": {"W": {"salaire_brut": {"2025-01": 6000.00}}}}
    )
    sim_sup = SimulationBuilder().build_from_dict(
        TBS, {"persons": {"W": {"salaire_brut": {"2025-01": 6000.01}}}}
    )

    cnss_sub = float(sim_sub.calculate("cotisation_cnss_salarie", "2025-01")[0])
    cnss_at = float(sim_at.calculate("cotisation_cnss_salarie", "2025-01")[0])
    cnss_sup = float(sim_sup.calculate("cotisation_cnss_salarie", "2025-01")[0])

    # Moving from 5999.99 to 6000.00: CNSS salariale increases by 0.01 * 4.48%
    assert cnss_at > cnss_sub
    # Moving from 6000.00 to 6000.01: CNSS salariale must remain frozen at ceiling
    assert pytest.approx(cnss_sup, abs=1e-4) == cnss_at


# --- 3. Vectorization across multiple persons ---


def test_vectorization_heterogeneous_population():
    """Verify vectorized execution across heterogeneous salaries."""
    salaries = [0.0, 2500.0, 5999.99, 6000.0, 6000.01, 12000.0, 50000.0]
    situation = {
        "persons": {
            f"worker_{i}": {"salaire_brut": {"2025-01": s}}
            for i, s in enumerate(salaries)
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    cnss_sal = sim.calculate("cotisation_cnss_salarie", "2025-01")
    amo_sal = sim.calculate("cotisation_amo_salarie", "2025-01")
    tot_sal = sim.calculate("cotisations_sociales_salarie", "2025-01")
    cnss_pat = sim.calculate("cotisation_cnss_employeur", "2025-01")
    amo_pat = sim.calculate("cotisation_amo_employeur", "2025-01")
    tot_pat = sim.calculate("cotisations_sociales_employeur", "2025-01")
    cout = sim.calculate("cout_employeur", "2025-01")

    assert len(cnss_sal) == len(salaries)
    assert np.all(tot_sal == cnss_sal + amo_sal)
    assert np.all(tot_pat == cnss_pat + amo_pat)
    assert np.all(pytest.approx(cout, abs=1e-2) == np.array(salaries) + tot_pat)
    # All salaries >= 6000 must have capped CNSS salariale equal to 268.80
    for idx, s in enumerate(salaries):
        if s >= 6000.0:
            assert pytest.approx(float(cnss_sal[idx]), abs=1e-2) == 268.80


# --- 4. Backwards compatibility tests ---


def test_backwards_compatibility_legacy_salaire_brut_global_only():
    """An existing simulation providing only salaire_brut_global still evaluates cleanly."""
    situation = {
        "persons": {
            "LegacyWorker": {
                "salaire_brut_global": {"2025": 100000.0},
                "elements_exoneres": {"2025": 0.0},
                "nombre_personnes_a_charge": {"2025": 0},
            }
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    # cotisations_sociales_obligatoires should calculate to 0.0 from default salaire_brut=0
    cso = float(sim.calculate("cotisations_sociales_obligatoires", "2025")[0])
    assert cso == 0.0

    # IR evaluates identically to legacy behavior without cotisations
    ir = float(sim.calculate("impot_sur_le_revenu", "2025")[0])
    # 100k -> frais pro 25k -> net imposable 75k -> IR = 75k * 20% - 10k = 5000
    assert pytest.approx(ir, rel=1e-4) == 5000.0


def test_backwards_compatibility_explicit_cotisations_override():
    """Explicitly providing cotisations_sociales_obligatoires overrides the formula."""
    situation = {
        "persons": {
            "LegacyWorker": {
                "salaire_brut_global": {"2025": 200000.0},
                "cotisations_sociales_obligatoires": {"2025": 20000.0},
                "elements_exoneres": {"2025": 0.0},
                "nombre_personnes_a_charge": {"2025": 0},
            }
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    cso = float(sim.calculate("cotisations_sociales_obligatoires", "2025")[0])
    assert cso == 20000.0

    ir = float(sim.calculate("impot_sur_le_revenu", "2025")[0])
    assert pytest.approx(ir, rel=1e-4) == 27300.0


# --- 5. Partial year / missing months tests ---


def test_partial_year_three_months():
    """Providing only 3 months of salaire_brut cleanly sums those 3 months."""
    situation = {
        "persons": {
            "SeasonalWorker": {
                "salaire_brut": {
                    "2025-01": 4000.0,
                    "2025-02": 4000.0,
                    "2025-03": 4000.0,
                }
            }
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    # 4 000 MAD / month -> CNSS: 179.20, AMO: 90.40 -> total salarial: 269.60 / month
    # 3 active months -> 3 * 269.60 = 808.80
    cso = float(sim.calculate("cotisations_sociales_obligatoires", "2025")[0])
    assert pytest.approx(cso, rel=1e-4) == 808.80

    # Unprovided months evaluate to 0
    apr_cotis = float(sim.calculate("cotisations_sociales_salarie", "2025-04")[0])
    assert apr_cotis == 0.0


def test_partial_year_non_contiguous_months():
    """Providing non-contiguous months (e.g. Jan, Jul, Dec) sums correctly."""
    situation = {
        "persons": {
            "FreelanceWorker": {
                "salaire_brut": {
                    "2025-01": 6000.0,
                    "2025-07": 10000.0,
                    "2025-12": 15000.0,
                }
            }
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    # Month 1 (6 000 MAD): 404.40
    # Month 7 (10 000 MAD): 268.80 + 226.00 = 494.80
    # Month 12 (15 000 MAD): 268.80 + 339.00 = 607.80
    # Expected sum: 404.40 + 494.80 + 607.80 = 1507.00 MAD
    expected_sum = 404.40 + 494.80 + 607.80
    cso = float(sim.calculate("cotisations_sociales_obligatoires", "2025")[0])
    assert pytest.approx(cso, rel=1e-4) == expected_sum


# --- 6. Type integrity and metadata checks ---


def test_variables_metadata_and_types():
    """Ensure consistency of value_type, unit, entity, and definition_period."""
    from openfisca_core.periods import MONTH, YEAR

    from openfisca_morocco.entities import Person
    from openfisca_morocco.variables.cotisations_sociales import (
        cotisation_amo_employeur,
        cotisation_amo_salarie,
        cotisation_cnss_employeur,
        cotisation_cnss_salarie,
        cotisations_sociales_employeur,
        cotisations_sociales_salarie,
        cout_employeur,
        salaire_brut,
    )
    from openfisca_morocco.variables.impot_revenu import (
        cotisations_sociales_obligatoires,
    )

    monthly_vars = [
        salaire_brut,
        cotisation_cnss_salarie,
        cotisation_amo_salarie,
        cotisations_sociales_salarie,
        cotisation_cnss_employeur,
        cotisation_amo_employeur,
        cotisations_sociales_employeur,
        cout_employeur,
    ]

    for var in monthly_vars:
        assert var.value_type is float, f"{var.__name__} value_type is not float"
        assert var.entity is Person, f"{var.__name__} entity is not Person"
        assert var.definition_period is MONTH, (
            f"{var.__name__} definition_period is not MONTH"
        )
        assert var.unit == "currency-MAD", f"{var.__name__} unit is not currency-MAD"
        assert var.label, f"{var.__name__} missing label"
        assert var.reference, f"{var.__name__} missing reference"

    assert cotisations_sociales_obligatoires.value_type is float
    assert cotisations_sociales_obligatoires.entity is Person
    assert cotisations_sociales_obligatoires.definition_period is YEAR
    assert cotisations_sociales_obligatoires.unit == "currency-MAD"
