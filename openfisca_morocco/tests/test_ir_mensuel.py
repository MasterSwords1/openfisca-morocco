"""Monthly IR withholding (retenue à la source) — CGI arts. 73-I and 74."""

import pytest
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def simulate(person):
    return SimulationBuilder().build_from_dict(TBS, {"persons": {"worker": person}})


def monthly(salary, dependents=0, contributions_salary=0, period="2025-01"):
    year = period[:4]
    return {
        "salaire_brut_global": {period: salary},
        "elements_exoneres": {period: 0},
        "salaire_brut": {period: contributions_salary},
        "nombre_personnes_a_charge": {year: dependents},
    }


def test_monthly_scale_2025():
    simulation = simulate(monthly(3000))
    assert simulation.calculate("frais_professionnels_mensuel", "2025-01")[
        0
    ] == pytest.approx(1050, abs=0.01)
    assert simulation.calculate("salaire_net_imposable_mensuel", "2025-01")[
        0
    ] == pytest.approx(1950, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(0, abs=0.01)

    simulation = simulate(monthly(6000))
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(56.67, abs=0.02)

    simulation = simulate(monthly(25000))
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(5887.50, abs=0.02)


def test_monthly_family_deduction_is_prorated_and_capped():
    simulation = simulate(monthly(6000, dependents=2))
    assert simulation.calculate("deduction_charges_famille_mensuelle", "2025-01")[
        0
    ] == pytest.approx(83.33, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(0, abs=0.01)

    simulation = simulate(monthly(25000, dependents=3))
    assert simulation.calculate("deduction_charges_famille_mensuelle", "2025-01")[
        0
    ] == pytest.approx(125, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(5762.50, abs=0.02)

    # Six dependents are the maximum, even when more are declared.
    simulation = simulate(monthly(25000, dependents=10))
    assert simulation.calculate("deduction_charges_famille_mensuelle", "2025-01")[
        0
    ] == pytest.approx(250, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(5637.50, abs=0.02)


def test_monthly_scale_2016_to_2022():
    simulation = simulate(monthly(6000, period="2016-01"))
    assert simulation.calculate("frais_professionnels_mensuel", "2016-01")[
        0
    ] == pytest.approx(1200, abs=0.01)
    assert simulation.calculate("salaire_net_imposable_mensuel", "2016-01")[
        0
    ] == pytest.approx(4800, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2016-01")[
        0
    ] == pytest.approx(293.33, abs=0.02)

    simulation = simulate(monthly(25000, period="2016-01"))
    assert simulation.calculate("frais_professionnels_mensuel", "2016-01")[
        0
    ] == pytest.approx(2500, abs=0.01)
    assert simulation.calculate("salaire_net_imposable_mensuel", "2016-01")[
        0
    ] == pytest.approx(22500, abs=0.01)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2016-01")[
        0
    ] == pytest.approx(6516.67, abs=0.02)


def test_monthly_expense_switch_and_scale_boundary():
    # 2025: above 6,500 DH the forfait switches from 35 % to 25 %; at
    # 6,666.67 DH the net taxable pay is exactly 5,000 DH.
    simulation = simulate(monthly(6666.67))
    assert simulation.calculate("frais_professionnels_mensuel", "2025-01")[
        0
    ] == pytest.approx(1666.67, abs=0.01)
    assert simulation.calculate("salaire_net_imposable_mensuel", "2025-01")[
        0
    ] == pytest.approx(5000, abs=0.01)
    assert simulation.calculate("ir_brut_mensuel", "2025-01")[0] == pytest.approx(
        166.67, abs=0.02
    )

    # 2023: the annual 78,000 DH switch is prorated to 6,500 DH.
    simulation = simulate(monthly(6500, period="2023-01"))
    assert simulation.calculate("frais_professionnels_mensuel", "2023-01")[
        0
    ] == pytest.approx(2275, abs=0.01)
    simulation = simulate(monthly(6500.01, period="2023-01"))
    assert simulation.calculate("frais_professionnels_mensuel", "2023-01")[
        0
    ] == pytest.approx(1625.00, abs=0.02)


def test_monthly_contributions_and_net_pay():
    person = monthly(25000, contributions_salary=25000)
    simulation = simulate(person)

    assert simulation.calculate("cotisations_sociales_salarie", "2025-01")[
        0
    ] == pytest.approx(833.80, abs=0.02)
    assert simulation.calculate("salaire_net_imposable_mensuel", "2025-01")[
        0
    ] == pytest.approx(21249.53, abs=0.02)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(5579.00, abs=0.02)
    assert simulation.calculate("salaire_net_a_payer", "2025-01")[0] == pytest.approx(
        18587.20, abs=0.02
    )


def test_annual_salary_input_is_divided_before_monthly_withholding():
    simulation = simulate(
        {
            "salaire_brut_global": {"2025": 120000},
            "nombre_personnes_a_charge": {"2025": 0},
        }
    )

    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == 10000
    assert simulation.calculate("salaire_net_imposable_mensuel", "2025-01")[
        0
    ] == pytest.approx(7500, abs=0.02)
    assert simulation.calculate("ir_prelevement_source_mensuel", "2025-01")[
        0
    ] == pytest.approx(750, abs=0.02)


def test_monthly_withholding_before_2016_raises():
    simulation = simulate(monthly(6000, period="2015-01"))
    with pytest.raises(ValueError, match="only modelled from 2016"):
        simulation.calculate("ir_prelevement_source_mensuel", "2015-01")


def test_monthly_withholding_does_not_change_the_annual_tax():
    person = monthly(10000)
    person["salaire_brut_global"] = {
        f"2025-{month:02d}": 10000 for month in range(1, 13)
    }
    simulation = simulate(person)

    simulation.calculate("ir_prelevement_source_mensuel", "2025-01")

    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == pytest.approx(
        9000, abs=0.02
    )
    # With constant pay, the twelve monthly withholdings reconcile with the
    # annual tax because every base is prorated linearly.
    assert simulation.calculate_add("ir_prelevement_source_mensuel", "2025")[
        0
    ] == pytest.approx(9000, abs=0.02)
