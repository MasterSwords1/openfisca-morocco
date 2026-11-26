"""Gating and edge cases for the non-salarial IR categories.

The rental, capital and foreign-income rules are encoded from 2026 only. A pre-2026 input must
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


def test_cpu_regime_before_2026_raises():
    simulation = simulate("2025", regime_professionnel="cpu")
    with pytest.raises(ValueError, match="simplified, CPU and auto-entrepreneur"):
        simulation.calculate("revenu_professionnel_imposable", "2025")


def test_article28_deduction_before_2026_raises():
    simulation = simulate("2025", dons_organismes=1_000)
    with pytest.raises(ValueError, match="Article 28"):
        simulation.calculate("deductions_revenu_global", "2025")


def test_property_gain_before_2026_raises():
    simulation = simulate("2025", prix_cession_immobilier=1_000_000)
    with pytest.raises(ValueError, match="Property gains"):
        simulation.calculate("plus_value_immobiliere_imposable", "2025")


def test_professional_turnover_before_2026_raises():
    simulation = simulate("2025", chiffre_affaires_professionnel=100_000)
    with pytest.raises(ValueError, match="Professional regimes"):
        simulation.calculate("impot_contribution_professionnelle_unique", "2025")


def test_foreign_income_before_2026_raises():
    for year in ("2018", "2025"):
        for foreign_income in (100_000, -5_000):
            simulation = simulate(year, revenus_etrangers_bruts=foreign_income)
            with pytest.raises(ValueError, match="Foreign income.*2026"):
                simulation.calculate("revenu_etranger_imposable", year)
            with pytest.raises(ValueError, match="Foreign income.*2026"):
                simulation.calculate("revenu_global_imposable", year)
            with pytest.raises(ValueError, match="Foreign income.*2026"):
                simulation.calculate("impot_sur_le_revenu", year)


def test_foreign_income_applies_in_2026_and_2027():
    for year in ("2026", "2027"):
        simulation = simulate(year, revenus_etrangers_bruts=100_000)
        assert simulation.calculate("revenu_etranger_imposable", year)[
            0
        ] == pytest.approx(100_000)
        assert simulation.calculate("impot_sur_le_revenu", year)[0] == pytest.approx(
            12_000
        )


def test_negative_foreign_income_is_clamped_in_2026():
    simulation = simulate("2026", revenus_etrangers_bruts=-5_000)
    assert simulation.calculate("revenu_etranger_imposable", "2026")[0] == 0
    assert simulation.calculate("impot_sur_le_revenu", "2026")[0] == 0


def test_foreign_income_gate_is_vectorized_over_all_persons():
    situation = {
        "persons": {
            "salary_only": {},
            "foreign_income": {"revenus_etrangers_bruts": {"2025": 100_000}},
        },
        "households": {"menage": {"adults": ["salary_only", "foreign_income"]}},
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Foreign income.*2026"):
        simulation.calculate("impot_sur_le_revenu", "2025")


def test_plus_values_leaf_before_2026_raises():
    for year in ("2018", "2025"):
        for variable, amount in (
            ("plus_values_actions_cotees", 10_000),
            ("plus_values_actions_cotees", -5_000),
            ("plus_values_titres_non_cotes", 10_000),
            ("plus_values_titres_non_cotes", -5_000),
        ):
            simulation = simulate(year, **{variable: amount})
            with pytest.raises(ValueError, match="Capital income"):
                simulation.calculate("impot_plus_values", year)


def test_plus_values_applies_in_2026():
    simulation = simulate("2026", plus_values_actions_cotees=10_000)
    assert simulation.calculate("impot_plus_values", "2026")[0] == pytest.approx(1_500)
    simulation = simulate("2026", plus_values_titres_non_cotes=10_000)
    assert simulation.calculate("impot_plus_values", "2026")[0] == pytest.approx(2_000)


def test_plus_values_applies_in_2027():
    simulation = simulate("2027", plus_values_actions_cotees=10_000)
    assert simulation.calculate("impot_plus_values", "2027")[0] == pytest.approx(1_500)
    simulation = simulate("2027", plus_values_titres_non_cotes=10_000)
    assert simulation.calculate("impot_plus_values", "2027")[0] == pytest.approx(2_000)


def test_negative_plus_values_are_clamped_in_2026():
    simulation = simulate("2026", plus_values_actions_cotees=-10_000)
    assert simulation.calculate("impot_plus_values", "2026")[0] == 0
    simulation = simulate("2026", plus_values_titres_non_cotes=-10_000)
    assert simulation.calculate("impot_plus_values", "2026")[0] == 0


def test_capital_aggregate_before_2026_raises_on_offsetting_plus_values():
    simulation = simulate(
        "2025",
        plus_values_actions_cotees=10_000,
        plus_values_titres_non_cotes=-10_000,
    )
    for variable in (
        "impot_plus_values",
        "impot_capitaux_mobiliers",
        "impot_sur_le_revenu_menage",
    ):
        with pytest.raises(ValueError, match="Capital income"):
            simulation.calculate(variable, "2025")


def test_zero_capital_income_before_2026_returns_zero():
    simulation = simulate("2025")
    assert simulation.calculate("impot_capitaux_mobiliers", "2025")[0] == 0
    assert simulation.calculate("impot_sur_le_revenu_menage", "2025")[0] == 0


def test_plus_values_gate_is_vectorized_over_all_persons():
    situation = {
        "persons": {
            "clean": {},
            "gains": {"plus_values_actions_cotees": {"2025": 10_000}},
        },
        "households": {"menage": {"adults": ["clean", "gains"]}},
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Capital income"):
        simulation.calculate("impot_plus_values", "2025")


def test_foreign_capital_offsetting_inputs_raise_before_2026():
    simulation = simulate(
        "2025",
        revenus_capitaux_etrangers_bruts=10_000,
        profits_capitaux_etrangers=-10_000,
    )
    with pytest.raises(ValueError, match="Foreign capital"):
        simulation.calculate("impot_capitaux_etrangers", "2025")


def test_property_gain_offsetting_inputs_raise_before_2026():
    simulation = simulate(
        "2025",
        prix_cession_immobilier=1_000_000,
        prix_acquisition_immobilier=-1_000_000,
    )
    with pytest.raises(ValueError, match="Property gains"):
        simulation.calculate("plus_value_immobiliere_imposable", "2025")
    with pytest.raises(ValueError, match="Property gains"):
        simulation.calculate("impot_plus_value_immobiliere", "2025")


def test_property_gain_auxiliary_inputs_raise_before_2026():
    for inputs in (
        {"total_cessions_immobilieres_annee": 500_000},
        {"habitation_principale_cedee": True},
        {"annees_detention_habitation": 10},
    ):
        simulation = simulate("2025", **inputs)
        with pytest.raises(ValueError, match="Property gains"):
            simulation.calculate("plus_value_immobiliere_imposable", "2025")


def test_article28_offsetting_inputs_raise_before_2026():
    simulation = simulate(
        "2025",
        dons_organismes=10_000,
        interets_pret_logement=-10_000,
    )
    with pytest.raises(ValueError, match="Article 28"):
        simulation.calculate("deductions_revenu_global", "2025")


def test_dividends_and_interest_offsetting_inputs_raise_before_2026():
    simulation = simulate("2025", dividendes_bruts=10_000, interets_bruts=-10_000)
    for variable in (
        "impot_dividendes",
        "impot_interets",
        "impot_capitaux_mobiliers",
    ):
        with pytest.raises(ValueError, match="Capital income"):
            simulation.calculate(variable, "2025")


def test_negative_dividends_and_interest_raise_before_2026():
    for variable in ("dividendes_bruts", "interets_bruts"):
        simulation = simulate("2025", **{variable: -5_000})
        with pytest.raises(ValueError, match="Capital income"):
            simulation.calculate("impot_capitaux_mobiliers", "2025")


def test_foreign_capital_single_and_negative_inputs_raise_before_2026():
    for variable in (
        "revenus_capitaux_etrangers_bruts",
        "profits_capitaux_etrangers",
    ):
        for amount in (10_000, -5_000):
            simulation = simulate("2025", **{variable: amount})
            with pytest.raises(ValueError, match="Foreign capital"):
                simulation.calculate("impot_capitaux_etrangers", "2025")


def test_foreign_capital_gate_is_vectorized_over_all_persons():
    situation = {
        "persons": {
            "clean": {},
            "foreign_capital": {"revenus_capitaux_etrangers_bruts": {"2025": 10_000}},
        },
        "households": {"menage": {"adults": ["clean", "foreign_capital"]}},
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Foreign capital"):
        simulation.calculate("impot_capitaux_etrangers", "2025")


def test_property_gain_negative_cession_raises_before_2026():
    simulation = simulate("2025", prix_cession_immobilier=-1_000_000)
    with pytest.raises(ValueError, match="Property gains"):
        simulation.calculate("plus_value_immobiliere_imposable", "2025")


def test_property_gain_gate_is_vectorized_over_all_persons():
    situation = {
        "persons": {
            "clean": {},
            "property": {"prix_cession_immobilier": {"2025": 1_000_000}},
        },
        "households": {"menage": {"adults": ["clean", "property"]}},
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Property gains"):
        simulation.calculate("plus_value_immobiliere_imposable", "2025")


def test_article28_primes_only_and_negative_inputs_raise_before_2026():
    for variable in (
        "dons_organismes",
        "interets_pret_logement",
        "primes_assurance_retraite",
    ):
        for amount in (10_000, -5_000):
            simulation = simulate("2025", **{variable: amount})
            with pytest.raises(ValueError, match="Article 28"):
                simulation.calculate("deductions_revenu_global", "2025")


def test_article28_gate_is_vectorized_over_all_persons():
    situation = {
        "persons": {
            "clean": {},
            "deduction": {"dons_organismes": {"2025": 10_000}},
        },
        "households": {"menage": {"adults": ["clean", "deduction"]}},
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Article 28"):
        simulation.calculate("deductions_revenu_global", "2025")


def test_property_gain_each_money_input_raises_before_2026():
    for variable in (
        "prix_cession_immobilier",
        "prix_acquisition_immobilier",
        "frais_cession_immobilier",
        "depenses_investissement_immobilier",
    ):
        for amount in (1_000_000, -1_000_000):
            simulation = simulate("2025", **{variable: amount})
            with pytest.raises(ValueError, match="Property gains"):
                simulation.calculate("plus_value_immobiliere_imposable", "2025")


def test_liberatory_rental_leaf_before_2026_raises():
    simulation = simulate(
        "2025",
        revenus_fonciers_bruts=100_000,
        option_foncier_liberatoire=True,
    )
    with pytest.raises(ValueError, match="Rental income"):
        simulation.calculate("impot_foncier_liberatoire", "2025")

    simulation = simulate("2025")
    assert simulation.calculate("impot_foncier_liberatoire", "2025")[0] == 0
