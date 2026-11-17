"""Les deux réformes d'exemple s'exécutent et changent l'impôt attendu."""

import pytest
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem
from openfisca_morocco.reforms import ReformeBaremeIR, ReformeTVA

BASELINE = CountryTaxBenefitSystem()


def ir(system, income):
    situation = {
        "persons": {"Contribuable": {"revenu_professionnel_net": {2026: income}}},
        "households": {"Menage": {"adults": ["Contribuable"]}},
    }
    simulation = SimulationBuilder().build_from_dict(system, situation)
    return float(simulation.calculate("impot_sur_le_revenu", "2026")[0])


def tva(system, period="2026-06"):
    situation = {
        "persons": {"Gerant": {}},
        "companies": {
            "Entreprise": {
                "membres": ["Gerant"],
                "chiffre_affaires_taux_normal": {period: 1_000_000},
            }
        },
    }
    simulation = SimulationBuilder().build_from_dict(system, situation)
    return float(simulation.calculate("tva_collectee_taux_normal", period)[0])


@pytest.mark.parametrize(
    ("income", "baseline", "reformed"),
    [
        (50_000, 1_000, 2_000),
        (100_000, 12_000, 16_800),
        (200_000, 46_600, 51_600),
    ],
)
def test_reforme_bareme_ir(income, baseline, reformed):
    reform = ReformeBaremeIR(BASELINE)
    assert ir(BASELINE, income) == pytest.approx(baseline)
    assert ir(reform, income) == pytest.approx(reformed)


def test_reforme_bareme_ir_applies_in_2025():
    reform = ReformeBaremeIR(BASELINE)
    assert ir(reform, 50_000) == pytest.approx(2_000)


def test_reforme_tva():
    reform = ReformeTVA(BASELINE)
    assert tva(BASELINE) == pytest.approx(200_000)
    assert tva(reform) == pytest.approx(180_000)
    assert tva(reform, "2025-06") == pytest.approx(180_000)


def test_reforme_tva_preserves_pre_2025_history():
    reform = ReformeTVA(BASELINE)
    assert tva(reform, "2024-06") == pytest.approx(200_000)
