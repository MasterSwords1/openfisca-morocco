"""Tests unitaires et d'intégration des cotisations sociales marocaines (CNSS, AMO).

Vérifie :
1. Les calculs mensuels des cotisations salariales et patronales à différents niveaux de salaire
   (en deçà, au niveau et au-delà du plafond CNSS de 6 000 MAD).
2. La conformité exacte avec l'oracle du corpus `morocco-holy-graph`
   (`laws/ma_social_protection/calculator.py`).
3. L'intégration de la formule de `cotisations_sociales_obligatoires` dans le calcul annuel de l'IR.
"""

import pytest
from openfisca_core.errors.parameter_not_found_error import ParameterNotFoundError
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def simuler_salarie(salaire_mensuel: float, period: str = "2025-01"):
    situation = {
        "persons": {
            "Salarie": {
                "salaire_brut": {period: salaire_mensuel},
            }
        }
    }
    return SimulationBuilder().build_from_dict(TBS, situation)


@pytest.mark.parametrize(
    (
        "salaire",
        "expected_cnss_sal",
        "expected_amo_sal",
        "expected_tot_sal",
        "expected_cnss_pat",
        "expected_amo_pat",
        "expected_tot_pat",
        "expected_cout",
    ),
    [
        (3000.0, 134.4, 67.8, 202.2, 509.4, 123.3, 632.7, 3632.7),
        (4000.0, 179.2, 90.4, 269.6, 679.2, 164.4, 843.6, 4843.6),
        (6000.0, 268.8, 135.6, 404.4, 1018.8, 246.6, 1265.4, 7265.4),
        (10000.0, 268.8, 226.0, 494.8, 1338.8, 411.0, 1749.8, 11749.8),
        (15000.0, 268.8, 339.0, 607.8, 1738.8, 616.5, 2355.3, 17355.3),
        (20000.0, 268.8, 452.0, 720.8, 2138.8, 822.0, 2960.8, 22960.8),
    ],
)
def test_cotisations_sociales_mensuelles(
    salaire,
    expected_cnss_sal,
    expected_amo_sal,
    expected_tot_sal,
    expected_cnss_pat,
    expected_amo_pat,
    expected_tot_pat,
    expected_cout,
):
    sim = simuler_salarie(salaire, "2025-01")

    assert (
        pytest.approx(
            float(sim.calculate("cotisation_cnss_salarie", "2025-01")[0]), rel=1e-4
        )
        == expected_cnss_sal
    )
    assert (
        pytest.approx(
            float(sim.calculate("cotisation_amo_salarie", "2025-01")[0]), rel=1e-4
        )
        == expected_amo_sal
    )
    assert (
        pytest.approx(
            float(sim.calculate("cotisations_sociales_salarie", "2025-01")[0]), rel=1e-4
        )
        == expected_tot_sal
    )
    assert (
        pytest.approx(
            float(sim.calculate("cotisation_cnss_employeur", "2025-01")[0]), rel=1e-4
        )
        == expected_cnss_pat
    )
    assert (
        pytest.approx(
            float(sim.calculate("cotisation_amo_employeur", "2025-01")[0]), rel=1e-4
        )
        == expected_amo_pat
    )
    assert (
        pytest.approx(
            float(sim.calculate("cotisations_sociales_employeur", "2025-01")[0]),
            rel=1e-4,
        )
        == expected_tot_pat
    )
    assert (
        pytest.approx(float(sim.calculate("cout_employeur", "2025-01")[0]), rel=1e-4)
        == expected_cout
    )


def test_cotisations_sociales_obligatoires_calculees_annuellement_dans_ir():
    """Vérifie que cotisations_sociales_obligatoires se calcule par formule

    en sommant les 12 mois de cotisations salariales obligatoires (CNSS + AMO),
    et s'injecte directement dans le pipeline IR (frais professionnels et impôt net).
    """
    # Salarié rémunéré à 10 000 MAD brut par mois (120 000 MAD brut annuel)
    monthly_salaries = {f"2025-{m:02d}": 10000.0 for m in range(1, 13)}

    situation = {
        "persons": {
            "Ahmed": {
                "salaire_brut": monthly_salaries,
                "salaire_brut_global": {"2025": 120000.0},
                "elements_exoneres": {"2025": 0.0},
                "nombre_personnes_a_charge": {"2025": 0},
            }
        }
    }
    sim = SimulationBuilder().build_from_dict(TBS, situation)

    # Cotisation mensuelle salariale pour 10 000 MAD :
    # CNSS : min(10000, 6000) × 4,48 % = 268,80 MAD
    # AMO : 10000 × 2,26 % = 226,00 MAD
    # Total mensuel : 494,80 MAD
    # Total annuel sur 12 mois : 494,80 × 12 = 5 937,60 MAD
    cotisations_annuelles = float(
        sim.calculate("cotisations_sociales_obligatoires", "2025")[0]
    )
    assert pytest.approx(cotisations_annuelles, rel=1e-4) == 5937.60

    # Base des frais professionnels : brut imposable (120 000), avant cotisations
    # (art. 59-I ; les cotisations sont déduites séparément, art. 59-II).
    # Taux applicable : brut imposable > 78 000 DH -> taux 25 % (plafonné à 35 000 DH)
    # Frais pro : 120 000 × 25 % = 30 000 MAD
    frais_pro = float(sim.calculate("frais_professionnels", "2025")[0])
    assert pytest.approx(frais_pro, rel=1e-4) == 30000.00

    # Salaire net imposable : 120 000 - 5 937,60 - 30 000 = 84 062,40 MAD
    net_imposable = float(sim.calculate("salaire_net_imposable", "2025")[0])
    assert pytest.approx(net_imposable, rel=1e-4) == 84062.40

    # Barème LF 2025 sur tranche 80 001 - 100 000 DH (taux 30 %, somme à déduire 18 000 DH) :
    # IR brut = 84 062,40 × 30 % - 18 000 = 25 218,72 - 18 000 = 7 218,72 MAD
    ir_net = float(sim.calculate("impot_sur_le_revenu", "2025")[0])
    assert pytest.approx(ir_net, rel=1e-4) == 7218.72


def test_cnss_chains_start_in_2016_01():
    simulation = simuler_salarie(10_000, "2016-01")
    assert simulation.calculate("cotisations_sociales_salarie", "2016-01")[
        0
    ] == pytest.approx(494.80)
    assert simulation.calculate("cotisations_sociales_employeur", "2016-01")[
        0
    ] == pytest.approx(1749.80)
    assert simulation.calculate("cout_employeur", "2016-01")[0] == pytest.approx(
        11749.80
    )

    simulation = simuler_salarie(10_000, "2015-12")
    with pytest.raises(ParameterNotFoundError, match="amo"):
        simulation.calculate("cotisations_sociales_employeur", "2015-12")

    for period in ("2019-06", "2019-07"):
        simulation = simuler_salarie(10_000, period)
        assert simulation.calculate("cotisations_sociales_employeur", period)[
            0
        ] == pytest.approx(1749.80)


def test_employer_family_allowance_rate_starts_in_2009():
    assert (
        TBS.parameters(
            "2009-01-01"
        ).prestations_sociales.cotisations.cnss.prestations_familiales.employeur
        == pytest.approx(0.064)
    )
    with pytest.raises(ParameterNotFoundError):
        _ = TBS.parameters(
            "2008-12-01"
        ).prestations_sociales.cotisations.cnss.prestations_familiales.employeur


def test_cnss_employer_only_is_computable_before_amo():
    for period in ("2014-12", "2015-12"):
        simulation = simuler_salarie(10_000, period)
        assert simulation.calculate("cotisation_cnss_employeur", period)[
            0
        ] == pytest.approx(1338.80)
        with pytest.raises(ParameterNotFoundError, match="amo"):
            simulation.calculate("cotisations_sociales_employeur", period)


def test_employee_amo_chain_starts_in_2016_01():
    simulation = simuler_salarie(10_000, "2015-12")
    with pytest.raises(ParameterNotFoundError, match="amo"):
        simulation.calculate("cotisations_sociales_salarie", "2015-12")
    simulation = simuler_salarie(10_000, "2016-01")
    assert simulation.calculate("cotisations_sociales_salarie", "2016-01")[
        0
    ] == pytest.approx(494.80)


def test_ipe_employee_chain_starts_in_2014_12():
    simulation = simuler_salarie(10_000, "2014-11")
    with pytest.raises(ParameterNotFoundError, match="indemnite_perte_emploi"):
        simulation.calculate("cotisation_cnss_salarie", "2014-11")
    simulation = simuler_salarie(10_000, "2014-12")
    assert simulation.calculate("cotisation_cnss_salarie", "2014-12")[0] > 0
