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


def _household_at(year, **inputs):
    situation = {
        "persons": {"Parent": {}},
        "households": {
            "Menage": {
                "adults": ["Parent"],
                **{name: {year: value} for name, value in inputs.items()},
            }
        },
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


def _company_at(year, **inputs):
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


@pytest.mark.parametrize(
    ("output", "input_name", "value"),
    [
        ("droits_enregistrement", "valeur_bien_acquis", 1_000_000),
        (
            "droits_enregistrement",
            "type_acquisition_immobiliere",
            "immeuble_bati",
        ),
        ("droits_enregistrement", "paiement_par_moyen_tracable", False),
        ("droits_enregistrement", "demande_certificat_propriete", True),
        ("frais_conservation_fonciere", "valeur_bien_acquis", 1_000_000),
        (
            "frais_conservation_fonciere",
            "type_acquisition_immobiliere",
            "immeuble_bati",
        ),
        ("frais_conservation_fonciere", "paiement_par_moyen_tracable", False),
        ("frais_conservation_fonciere", "demande_certificat_propriete", True),
    ],
)
def test_household_single_input_before_2026_raises(output, input_name, value):
    simulation = _household_at(2025, **{input_name: value})
    with pytest.raises(ValueError, match="Registration duties|Conservation fees"):
        simulation.calculate(output, "2025")


@pytest.mark.parametrize(
    ("output", "input_name", "value"),
    [
        ("droits_enregistrement_societe", "valeur_bien_acquis_societe", 1_000_000),
        (
            "droits_enregistrement_societe",
            "type_acquisition_immobiliere_societe",
            "immeuble_bati",
        ),
        (
            "droits_enregistrement_societe",
            "paiement_par_moyen_tracable_societe",
            False,
        ),
        (
            "droits_enregistrement_societe",
            "demande_certificat_propriete_societe",
            True,
        ),
        (
            "frais_conservation_fonciere_societe",
            "valeur_bien_acquis_societe",
            1_000_000,
        ),
        (
            "frais_conservation_fonciere_societe",
            "type_acquisition_immobiliere_societe",
            "immeuble_bati",
        ),
        (
            "frais_conservation_fonciere_societe",
            "paiement_par_moyen_tracable_societe",
            False,
        ),
        (
            "frais_conservation_fonciere_societe",
            "demande_certificat_propriete_societe",
            True,
        ),
        (
            "droits_enregistrement_constitution_societe",
            "apport_capital_non_exonere",
            1_000_000,
        ),
        (
            "droits_enregistrement_constitution_societe",
            "apport_capital_numeraires",
            1_000_000,
        ),
    ],
)
def test_company_single_input_before_2026_raises(output, input_name, value):
    simulation = _company_at(2025, **{input_name: value})
    with pytest.raises(ValueError, match="Registration duties|Conservation fees"):
        simulation.calculate(output, "2025")


def test_household_default_before_2026_returns_zero():
    simulation = _household_at(2025)
    assert float(simulation.calculate("droits_enregistrement", "2025")[0]) == 0
    assert float(simulation.calculate("frais_conservation_fonciere", "2025")[0]) == 0


def test_company_default_before_2026_returns_zero():
    simulation = _company_at(2025)
    for variable in (
        "droits_enregistrement_societe",
        "frais_conservation_fonciere_societe",
        "droits_enregistrement_constitution_societe",
    ):
        assert float(simulation.calculate(variable, "2025")[0]) == 0


def test_household_registration_guard_is_vectorized_over_entities():
    situation = {
        "persons": {"Clean": {}, "Dirty": {}},
        "households": {
            "clean": {"adults": ["Clean"]},
            "dirty": {
                "adults": ["Dirty"],
                "valeur_bien_acquis": {2025: 1_000_000},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Registration duties"):
        simulation.calculate("droits_enregistrement", "2025")


def test_company_registration_and_capital_guards_are_vectorized():
    situation = {
        "persons": {"Gerant1": {}, "Gerant2": {}},
        "companies": {
            "clean": {"membres": ["Gerant1"]},
            "dirty": {
                "membres": ["Gerant2"],
                "type_acquisition_immobiliere_societe": {2025: "immeuble_bati"},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Registration duties"):
        simulation.calculate("droits_enregistrement_societe", "2025")

    situation = {
        "persons": {"Gerant1": {}, "Gerant2": {}},
        "companies": {
            "clean": {"membres": ["Gerant1"]},
            "cash": {
                "membres": ["Gerant2"],
                "apport_capital_numeraires": {2025: 1_000_000},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Registration duties"):
        simulation.calculate("droits_enregistrement_constitution_societe", "2025")


def test_conservation_guards_are_vectorized_over_entities():
    situation = {
        "persons": {"Clean": {}, "Dirty": {}},
        "households": {
            "clean": {"adults": ["Clean"]},
            "dirty": {
                "adults": ["Dirty"],
                "valeur_bien_acquis": {2025: 1_000_000},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Conservation fees"):
        simulation.calculate("frais_conservation_fonciere", "2025")

    situation = {
        "persons": {"Gerant1": {}, "Gerant2": {}},
        "companies": {
            "clean": {"membres": ["Gerant1"]},
            "dirty": {
                "membres": ["Gerant2"],
                "type_acquisition_immobiliere_societe": {2025: "immeuble_bati"},
            },
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    with pytest.raises(ValueError, match="Conservation fees"):
        simulation.calculate("frais_conservation_fonciere_societe", "2025")


@pytest.mark.parametrize(
    ("output", "input_name", "value"),
    [
        ("droits_enregistrement", "valeur_bien_acquis", -1),
        ("frais_conservation_fonciere", "valeur_bien_acquis", -1),
        ("droits_enregistrement_societe", "valeur_bien_acquis_societe", -1),
        ("frais_conservation_fonciere_societe", "valeur_bien_acquis_societe", -1),
        (
            "droits_enregistrement_constitution_societe",
            "apport_capital_non_exonere",
            -1,
        ),
        (
            "droits_enregistrement_constitution_societe",
            "apport_capital_numeraires",
            -1,
        ),
    ],
)
def test_negative_pre_2026_inputs_raise(output, input_name, value):
    if output.endswith("_societe"):
        simulation = _company_at(2025, **{input_name: value})
    else:
        simulation = _household_at(2025, **{input_name: value})
    with pytest.raises(ValueError, match="Registration duties|Conservation fees"):
        simulation.calculate(output, "2025")


def _household_with_date(date_str, **inputs):
    situation = {
        "persons": {"Parent": {}},
        "households": {
            "Menage": {
                "adults": ["Parent"],
                "date_acte_enregistrement": {"ETERNITY": date_str},
                **{name: {2026: value} for name, value in inputs.items()},
            }
        },
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


@pytest.mark.parametrize(
    ("date_str", "expected"),
    [("2026-06-30", 40_000), ("2026-07-01", 60_000)],
)
def test_two_percent_surcharge_starts_on_1_july_2026(date_str, expected):
    simulation = _household_with_date(
        date_str,
        type_acquisition_immobiliere="immeuble_bati",
        valeur_bien_acquis=1_000_000,
        paiement_par_moyen_tracable=False,
    )
    assert simulation.calculate("droits_enregistrement", "2026")[0] == pytest.approx(
        expected
    )


def test_fonds_de_commerce_has_no_300k_threshold_for_the_surcharge():
    simulation = _household_with_date(
        "2026-07-01",
        type_acquisition_immobiliere="fonds_commerce",
        valeur_bien_acquis=200_000,
        paiement_par_moyen_tracable=False,
    )
    assert simulation.calculate("droits_enregistrement", "2026")[0] == pytest.approx(
        16_000
    )

    simulation = _household_with_date(
        "2026-07-01",
        type_acquisition_immobiliere="fonds_commerce",
        valeur_bien_acquis=200_000,
        paiement_par_moyen_tracable=True,
    )
    assert simulation.calculate("droits_enregistrement", "2026")[0] == pytest.approx(
        12_000
    )


def test_built_property_under_300k_is_not_surcharged():
    simulation = _household_with_date(
        "2026-07-01",
        type_acquisition_immobiliere="immeuble_bati",
        valeur_bien_acquis=200_000,
        paiement_par_moyen_tracable=False,
    )
    assert simulation.calculate("droits_enregistrement", "2026")[0] == pytest.approx(
        8_000
    )
