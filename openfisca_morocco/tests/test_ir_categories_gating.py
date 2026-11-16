"""Gating and edge cases for the non-salarial IR categories.

The rental and capital rules are encoded from 2026 only. A pre-2026 input must
raise rather than be silently ignored; professional net income, whose net-réel
regime predates 2026, is accepted whenever the barème exists.
"""

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()


def simulate(period, **person_inputs):
    situation = {
        "persons": {"contribuable": person_inputs},
        "households": {"menage": {"adults": ["contribuable"]}},
    }
    builder = SimulationBuilder()
    builder.set_default_period(period)
    return builder.build_from_dict(SYSTEM, situation)


def test_rental_income_before_2026_raises():
    simulation = simulate("2025", revenus_fonciers_bruts=100_000)
    with pytest.raises(ValueError, match="Rental income"):
        simulation.calculate("revenu_foncier_net", "2025")


def test_capital_income_before_2026_raises():
    simulation = simulate("2025", dividendes_bruts=10_000)
    with pytest.raises(ValueError, match="Capital income"):
        simulation.calculate("impot_capitaux_mobiliers", "2025")


def test_professional_income_applies_in_2025():
    simulation = simulate("2025", revenu_professionnel_net=100_000)
    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == pytest.approx(
        12_000
    )


def test_rental_income_applies_in_2026():
    simulation = simulate("2026", revenus_fonciers_bruts=100_000)
    assert simulation.calculate("revenu_foncier_net", "2026")[0] == pytest.approx(
        60_000
    )


def test_leaf_capital_variable_before_2026_raises():
    simulation = simulate("2025", interets_bruts=10_000)
    with pytest.raises(ValueError, match="Capital income"):
        simulation.calculate("impot_interets", "2025")


def test_leaf_rental_variable_before_2026_raises():
    simulation = simulate("2025", revenus_fonciers_bruts=10_000)
    with pytest.raises(ValueError, match="Rental income"):
        simulation.calculate("retenue_fonciere", "2025")
