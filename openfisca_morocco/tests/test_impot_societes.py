"""Boundaries and API paths for the IS / cotisation minimale module."""

import pytest
from openfisca_core.errors.parameter_not_found_error import ParameterNotFoundError
from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()


def _company(year=2026, **inputs):
    situation = {
        "persons": {"Gerant": {}},
        "companies": {
            "Societe": {
                "membres": ["Gerant"],
                **{name: {year: value} for name, value in inputs.items()},
            }
        },
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


def test_threshold_is_inclusive_at_100_million():
    below = _company(benefice_fiscal=99_000_000, chiffre_affaires_annuel=1_000_000)
    at = _company(benefice_fiscal=100_000_000, chiffre_affaires_annuel=1_000_000)
    assert below.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.20)
    assert at.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.35)


def test_three_year_condition_applies_below_the_threshold():
    simulation = _company(
        benefice_fiscal=99_000_000,
        chiffre_affaires_annuel=1_000_000,
        benefice_sous_seuil_trois_ans=False,
    )
    assert simulation.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.35)


def test_35_percent_exclusion_returns_to_20_percent():
    simulation = _company(
        benefice_fiscal=100_000_000,
        chiffre_affaires_annuel=1_000_000,
        exclusion_taux_35=True,
    )
    assert simulation.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.20)


def test_credit_above_tax_floors_net_payable_at_zero():
    simulation = _company(
        benefice_fiscal=500_000,
        chiffre_affaires_annuel=2_000_000,
        credit_impot=200_000,
    )
    assert simulation.calculate("is_net_a_payer", "2026")[0] == 0


def test_reduced_rate_turnover_is_clipped_to_total_turnover():
    simulation = _company(
        benefice_fiscal=0,
        chiffre_affaires_annuel=10_000_000,
        chiffre_affaires_produits_taux_reduit=20_000_000,
    )
    # 10,000,000 * 0.15 % = 15,000, above the 3,000 floor.
    assert simulation.calculate("cotisation_minimale", "2026")[0] == pytest.approx(
        15_000
    )


def test_negative_turnover_does_not_reduce_the_minimum():
    simulation = _company(
        benefice_fiscal=0,
        chiffre_affaires_annuel=-1_000_000,
        produits_accessoires_financiers=-500_000,
    )
    assert simulation.calculate("base_cotisation_minimale", "2026")[0] == 0
    assert simulation.calculate("cotisation_minimale", "2026")[0] == 3_000


def test_rates_are_vectorized_across_companies():
    situation = {
        "persons": {"Gerant1": {}, "Gerant2": {}},
        "companies": {
            "Pme": {
                "membres": ["Gerant1"],
                "benefice_fiscal": {2026: 500_000},
                "chiffre_affaires_annuel": {2026: 2_000_000},
            },
            "Banque": {
                "membres": ["Gerant2"],
                "benefice_fiscal": {2026: 50_000_000},
                "chiffre_affaires_annuel": {2026: 100_000_000},
                "est_etablissement_financier": {2026: True},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    assert list(simulation.calculate("taux_is_applique", "2026")) == pytest.approx(
        [0.20, 0.40]
    )
    assert list(simulation.calculate("is_theorique", "2026")) == pytest.approx(
        [100_000, 20_000_000]
    )


def test_is_before_2026_raises():
    simulation = _company(
        year=2025,
        benefice_fiscal=500_000,
        chiffre_affaires_annuel=2_000_000,
    )
    with pytest.raises(ParameterNotFoundError):
        simulation.calculate("is_theorique", "2025")


def test_negative_credit_cannot_increase_the_tax():
    simulation = _company(
        benefice_fiscal=500_000,
        chiffre_affaires_annuel=2_000_000,
        credit_impot=-20_000,
    )
    assert simulation.calculate("is_net_a_payer", "2026")[0] == 100_000


def test_near_threshold_can_be_declared_below_100_million():
    # float32 storage rounds 99,999,999 to 100,000,000; the caller can
    # override the derived flag to keep the 20 % band.
    default = _company(
        benefice_fiscal=99_999_999,
        chiffre_affaires_annuel=1_000_000,
    )
    assert default.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.35)
    declared = _company(
        benefice_fiscal=99_999_999,
        chiffre_affaires_annuel=1_000_000,
        benefice_atteint_100m=False,
    )
    assert declared.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.20)


def test_financial_rate_takes_priority_above_100_million():
    simulation = _company(
        benefice_fiscal=150_000_000,
        chiffre_affaires_annuel=1_000_000_000,
        est_etablissement_financier=True,
    )
    assert simulation.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.40)
    assert simulation.calculate("is_theorique", "2026")[0] == pytest.approx(60_000_000)


def test_exclusion_does_not_override_the_financial_rate():
    simulation = _company(
        benefice_fiscal=150_000_000,
        chiffre_affaires_annuel=1_000_000_000,
        est_etablissement_financier=True,
        exclusion_taux_35=True,
    )
    assert simulation.calculate("taux_is_applique", "2026")[0] == pytest.approx(0.40)


def test_cotisation_minimale_can_exceed_a_positive_is():
    simulation = _company(
        benefice_fiscal=1_000_000,
        chiffre_affaires_annuel=1_000_000_000,
    )
    assert simulation.calculate("is_theorique", "2026")[0] == pytest.approx(200_000)
    assert simulation.calculate("cotisation_minimale", "2026")[0] == pytest.approx(
        2_500_000
    )
    assert simulation.calculate("is_du_brut", "2026")[0] == pytest.approx(2_500_000)


def test_negative_reduced_rate_turnover_is_clipped_to_zero():
    simulation = _company(
        benefice_fiscal=0,
        chiffre_affaires_annuel=10_000_000,
        chiffre_affaires_produits_taux_reduit=-1_000_000,
    )
    assert simulation.calculate("cotisation_minimale", "2026")[0] == pytest.approx(
        25_000
    )


def test_cm_base_clamps_negative_components_separately():
    simulation = _company(
        benefice_fiscal=0,
        chiffre_affaires_annuel=-1_000_000,
        produits_accessoires_financiers=2_000_000,
    )
    assert simulation.calculate("base_cotisation_minimale", "2026")[0] == pytest.approx(
        2_000_000
    )
    assert simulation.calculate("cotisation_minimale", "2026")[0] == pytest.approx(
        5_000
    )


def test_reduced_turnover_is_clipped_to_turnover_not_to_the_cm_base():
    simulation = _company(
        benefice_fiscal=0,
        chiffre_affaires_annuel=10_000_000,
        produits_accessoires_financiers=5_000_000,
        chiffre_affaires_produits_taux_reduit=12_000_000,
    )
    # 10M at 0.15 % + 5M at 0.25 % = 15,000 + 12,500.
    assert simulation.calculate("cotisation_minimale", "2026")[0] == pytest.approx(
        27_500
    )


def test_credit_reduces_the_gross_including_the_cm():
    simulation = _company(
        benefice_fiscal=500_000,
        chiffre_affaires_annuel=1_000_000_000,
        credit_impot=1_000_000,
    )
    assert simulation.calculate("is_du_brut", "2026")[0] == pytest.approx(2_500_000)
    assert simulation.calculate("is_net_a_payer", "2026")[0] == pytest.approx(1_500_000)
