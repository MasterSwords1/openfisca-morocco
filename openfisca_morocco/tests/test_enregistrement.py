"""Droits d'enregistrement sur les sociétés et gating temporel."""

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()


def _company(**inputs):
    situation = {
        "persons": {"Gerant": {}},
        "companies": {
            "Societe": {
                "membres": ["Gerant"],
                **{name: {2026: value} for name, value in inputs.items()},
            }
        },
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


def test_company_built_property():
    simulation = _company(
        type_acquisition_immobiliere_societe="immeuble_bati",
        valeur_bien_acquis_societe=2_000_000,
    )
    assert float(
        simulation.calculate("droits_enregistrement_societe", "2026")[0]
    ) == pytest.approx(80_000)
    assert float(
        simulation.calculate("frais_conservation_fonciere_societe", "2026")[0]
    ) == pytest.approx(30_100)


def test_company_certificate_is_optional():
    simulation = _company(
        type_acquisition_immobiliere_societe="immeuble_bati",
        valeur_bien_acquis_societe=2_000_000,
        demande_certificat_propriete_societe=True,
    )
    assert float(
        simulation.calculate("frais_acquisition_immobiliere_totaux_societe", "2026")[0]
    ) == pytest.approx(110_200)


def test_cash_capital_contribution_is_exempt():
    simulation = _company(apport_capital_numeraires=1_000_000)
    assert (
        float(
            simulation.calculate("droits_enregistrement_constitution_societe", "2026")[
                0
            ]
        )
        == 0
    )


def test_non_exempt_contribution_under_500k_pays_fixed_duty():
    simulation = _company(apport_capital_non_exonere=100_000)
    assert float(
        simulation.calculate("droits_enregistrement_constitution_societe", "2026")[0]
    ) == pytest.approx(1_000)


def test_non_exempt_contribution_above_500k_pays_half_percent():
    simulation = _company(apport_capital_non_exonere=1_000_000)
    assert float(
        simulation.calculate("droits_enregistrement_constitution_societe", "2026")[0]
    ) == pytest.approx(5_000)


def test_conservation_before_2026_raises():
    situation = {
        "persons": {"Gerant": {}},
        "companies": {
            "Societe": {
                "membres": ["Gerant"],
                "valeur_bien_acquis_societe": {2025: 1_000_000},
            }
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Conservation fees"):
        simulation.calculate("frais_conservation_fonciere_societe", "2025")


def test_fixed_duty_boundary_at_500_000():
    simulation = _company(apport_capital_non_exonere=500_000)
    assert float(
        simulation.calculate("droits_enregistrement_constitution_societe", "2026")[0]
    ) == pytest.approx(1_000)


def test_half_percent_above_the_fixed_duty_band():
    simulation = _company(apport_capital_non_exonere=600_000)
    assert float(
        simulation.calculate("droits_enregistrement_constitution_societe", "2026")[0]
    ) == pytest.approx(3_000)


def _household(**inputs):
    situation = {
        "persons": {"Parent": {}},
        "households": {
            "Menage": {
                "adults": ["Parent"],
                **{name: {2026: value} for name, value in inputs.items()},
            }
        },
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


def test_surcharge_threshold_boundary():
    at_threshold = _household(
        type_acquisition_immobiliere="immeuble_bati",
        valeur_bien_acquis=300_000,
        paiement_par_moyen_tracable=False,
    )
    above = _household(
        type_acquisition_immobiliere="immeuble_bati",
        valeur_bien_acquis=300_001,
        paiement_par_moyen_tracable=False,
    )
    assert float(
        at_threshold.calculate("droits_enregistrement", "2026")[0]
    ) == pytest.approx(12_000)
    assert float(above.calculate("droits_enregistrement", "2026")[0]) == pytest.approx(
        18_000.06
    )
