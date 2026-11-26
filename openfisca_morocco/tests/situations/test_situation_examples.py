"""Every bundled situation example is simulated and checked.

The JSON files under `situation_examples/` are what the Web API demo serves, so
they must produce meaningful Moroccan values. The expectations mirror the
YAML cases in this directory.
"""

import json
from pathlib import Path

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "situation_examples"
SYSTEM = CountryTaxBenefitSystem()


def _simulate(name):
    return SimulationBuilder().build_from_dict(
        SYSTEM, json.loads((EXAMPLES / name).read_text())
    )


def _value(simulation, variable, period):
    return float(simulation.calculate(variable, period)[0])


def test_salarie_template_example_unchanged():
    simulation = _simulate("salarie.json")
    assert _value(simulation, "impot_sur_le_revenu", "2025") == pytest.approx(
        25_800, abs=0.01
    )
    assert _value(simulation, "deduction_charges_famille", "2025") == 1_500


def test_salarie_below_exemption():
    simulation = _simulate("salarie_exonere.json")
    assert _value(simulation, "impot_sur_le_revenu", "2026") == 0
    assert _value(
        simulation, "cotisations_sociales_salarie", "2026-06"
    ) == pytest.approx(202.2, abs=0.01)


def test_salarie_above_exemption():
    simulation = _simulate("salarie_impose.json")
    assert _value(simulation, "impot_sur_le_revenu", "2026") == pytest.approx(
        6_618.72, abs=0.01
    )
    assert _value(simulation, "deduction_charges_famille", "2026") == 600


def test_couple_with_children():
    simulation = _simulate("couple_avec_enfants.json")
    incomes = simulation.calculate("impot_sur_le_revenu", "2026")
    assert float(incomes[0]) == pytest.approx(1_520.96, abs=0.01)
    assert float(incomes[1]) == pytest.approx(194.72, abs=0.01)
    assert _value(simulation, "deduction_charges_famille", "2026") == 1_800
    assert _value(simulation, "allocations_familiales", "2026-06") == 600
    assert float(simulation.calculate_add("allocations_familiales", "2026")[0]) == 7_200


def test_high_earner():
    simulation = _simulate("haut_revenu.json")
    assert _value(simulation, "impot_sur_le_revenu", "2026") == pytest.approx(
        217_635.88, abs=0.01
    )


def test_employer_cost_example():
    simulation = _simulate("cout_employeur.json")
    assert _value(simulation, "impot_sur_le_revenu", "2026") == pytest.approx(
        24_820.18, abs=0.01
    )
    assert _value(simulation, "cout_employeur", "2026-06") == pytest.approx(
        17_355.3, abs=0.01
    )
    assert _value(simulation, "cout_employeur", "2026-06") > _value(
        simulation, "salaire_brut", "2026-06"
    )


def test_asd_example():
    simulation = _simulate("menage_asd.json")
    assert _value(simulation, "aide_sociale_directe", "2026-06") == 900
    assert _value(simulation, "allocations_familiales", "2026-06") == 900
    assert (
        float(simulation.calculate_add("allocations_familiales", "2026")[0]) == 10_800
    )
