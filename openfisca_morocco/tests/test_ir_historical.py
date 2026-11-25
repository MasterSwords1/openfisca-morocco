"""Historical IR parameters: effective dates, bases and the pre-2010 gate."""

import pytest
from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()


def _params(year):
    return SYSTEM.parameters(f"{year}-01-01").impot_revenu


def _simulate(year, gross, dependents=0, cotisations=0):
    situation = {
        "persons": {
            "Salarie": {
                "salaire_brut_global": {year: gross},
                "cotisations_sociales_obligatoires": {year: cotisations},
                "nombre_personnes_a_charge": {year: dependents},
            }
        },
        "households": {"Menage": {"adults": ["Salarie"]}},
    }
    return SimulationBuilder().build_from_dict(SYSTEM, situation)


def test_2010_scale_and_deductions():
    params = _params(2010)
    assert params.bareme.thresholds == [0, 30_000, 50_000, 60_000, 80_000, 180_000]
    assert params.bareme.rates == [0, 0.10, 0.20, 0.30, 0.34, 0.38]
    assert params.frais_professionnels.taux_2010_2022 == pytest.approx(0.20)
    assert params.frais_professionnels.plafond == pytest.approx(30_000)
    assert params.deduction_charges_famille.montant_par_personne == 360
    assert params.deduction_charges_famille.nombre_maximum_personnes == 6


def test_2023_professional_expense_switch():
    params = _params(2023).frais_professionnels
    assert params.taux_basse_remuneration == pytest.approx(0.35)
    assert params.taux_haute_remuneration == pytest.approx(0.25)
    assert params.seuil_taux_basse_remuneration == pytest.approx(78_000)
    assert params.plafond == pytest.approx(35_000)


def test_2025_scale_and_family_amounts():
    params = _params(2025)
    assert params.bareme.thresholds == [0, 40_000, 60_000, 80_000, 100_000, 180_000]
    assert params.bareme.rates == [0, 0.10, 0.20, 0.30, 0.34, 0.37]
    assert params.deduction_charges_famille.montant_par_personne == 500
    assert _params(2026).deduction_charges_famille.montant_par_personne == 600


def test_forfait_base_is_gross_before_social_contributions():
    # Art. 59-I applies the rate to gross taxable pay; social contributions are
    # deducted separately (art. 59-II).
    simulation = _simulate(2018, 120_000, cotisations=6_000)
    assert float(simulation.calculate("frais_professionnels", "2018")[0]) == 24_000
    assert float(simulation.calculate("salaire_net_imposable", "2018")[0]) == 90_000
    assert float(simulation.calculate("impot_sur_le_revenu", "2018")[0]) == 13_400

    simulation = _simulate(2025, 120_000, cotisations=5_937.60)
    assert float(simulation.calculate("frais_professionnels", "2025")[0]) == 30_000
    assert float(simulation.calculate("salaire_net_imposable", "2025")[0]) == (
        pytest.approx(84_062.40)
    )
    assert float(simulation.calculate("impot_sur_le_revenu", "2025")[0]) == (
        pytest.approx(7_218.72)
    )


def test_2010_salary_runs_with_supplied_contributions():
    simulation = _simulate(2010, 60_000)
    assert float(simulation.calculate("frais_professionnels", "2010")[0]) == 12_000
    assert float(simulation.calculate("impot_sur_le_revenu", "2010")[0]) == 1_800


def test_ir_before_2010_raises():
    simulation = _simulate(2009, 100_000)
    with pytest.raises(ValueError, match="2010"):
        simulation.calculate("frais_professionnels", "2009")
    with pytest.raises(ValueError, match="2010"):
        simulation.calculate("impot_sur_le_revenu", "2009")
