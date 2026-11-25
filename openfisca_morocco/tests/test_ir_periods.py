"""Monthly payroll inputs must feed one annual IR calculation (issue #9)."""

import pytest
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def simulate(person):
    return SimulationBuilder().build_from_dict(TBS, {"persons": {"worker": person}})


@pytest.mark.parametrize("annual_inputs", [False, True])
def test_monthly_and_legacy_annual_inputs_produce_the_same_ir(annual_inputs):
    def payroll(amount):
        if annual_inputs:
            return {"2025": amount * 12}
        return {f"2025-{month:02d}": amount for month in range(1, 13)}

    simulation = simulate(
        {
            "salaire_brut_global": payroll(10000),
            "elements_exoneres": payroll(1000),
            "cotisations_sociales_obligatoires": {"2025": 6000},
            "nombre_personnes_a_charge": {"2025": 2},
        }
    )

    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == 10000
    assert simulation.calculate("elements_exoneres", "2025-12")[0] == 1000
    assert simulation.calculate_add("salaire_brut_global", "2025")[0] == 120000
    assert simulation.calculate("salaire_brut_imposable", "2025")[0] == 108000
    assert simulation.calculate("frais_professionnels", "2025")[0] == 27000
    assert simulation.calculate("salaire_net_imposable", "2025")[0] == 75000
    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == pytest.approx(
        4000, abs=0.02
    )


def test_varying_monthly_pay_uses_monthly_cnss_ceiling_and_annual_ir_scale():
    salaries = {
        f"2025-{month:02d}": 6000 if month <= 6 else 12000 for month in range(1, 13)
    }
    exemptions = {
        f"2025-{month:02d}": 500 if month <= 6 else 1000 for month in range(1, 13)
    }
    simulation = simulate(
        {
            "salaire_brut": salaries,
            "salaire_brut_global": salaries,
            "elements_exoneres": exemptions,
            "nombre_personnes_a_charge": {"2025": 2},
        }
    )

    # CNSS is capped separately each month; AMO is not capped.
    assert simulation.calculate("cotisations_sociales_salarie", "2025-01")[
        0
    ] == pytest.approx(404.4, abs=0.01)
    assert simulation.calculate("cotisations_sociales_salarie", "2025-07")[
        0
    ] == pytest.approx(540, abs=0.01)
    assert simulation.calculate("cotisations_sociales_obligatoires", "2025")[
        0
    ] == pytest.approx(5666.4, abs=0.02)
    assert simulation.calculate("salaire_brut_imposable", "2025")[0] == 99000
    # 99 000 * 25% = 24 750; net = 99 000 - 5 666.4 - 24 750 = 68 583.6;
    # IR = 20% * net - 10 000 - 1 000 = 2 716.72.
    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == pytest.approx(
        2716.72, abs=0.02
    )


def test_a_single_month_is_not_repeated_or_carried_into_another_year():
    simulation = simulate({"salaire_brut_global": {"2025-12": 100000}})

    assert simulation.calculate("salaire_brut_global", "2025-11")[0] == 0
    assert simulation.calculate("salaire_brut_imposable", "2025")[0] == 100000
    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == 5000
    assert simulation.calculate("salaire_brut_imposable", "2026")[0] == 0
    assert simulation.calculate("impot_sur_le_revenu", "2026")[0] == 0


def test_annual_contribution_salary_is_divided_before_applying_the_monthly_cap():
    simulation = simulate(
        {
            "salaire_brut": {"2025": 120000},
            "salaire_brut_global": {"2025": 120000},
        }
    )

    assert simulation.calculate("salaire_brut", "2025-12")[0] == 10000
    assert simulation.calculate("cotisations_sociales_obligatoires", "2025")[
        0
    ] == pytest.approx(5937.6, abs=0.02)
    assert simulation.calculate("impot_sur_le_revenu", "2025")[0] == pytest.approx(
        7218.72, abs=0.02
    )


def test_monthly_detail_and_annual_total_preserve_the_total():
    simulation = simulate(
        {
            "salaire_brut_global": {"2025": 120000, "2025-12": 21000},
            "elements_exoneres": {"2025": 12000, "2025-12": 2100},
        }
    )

    # December is explicit; the remaining annual total is divided over 11 months.
    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == 9000
    assert simulation.calculate("salaire_brut_global", "2025-12")[0] == 21000
    assert simulation.calculate("elements_exoneres", "2025-01")[0] == 900
    assert simulation.calculate("salaire_brut_imposable", "2025")[0] == 108000


@pytest.mark.parametrize("annual_salary", [100000, 200000, 500000])
def test_annual_salary_split_does_not_accumulate_rounding_error(annual_salary):
    simulation = simulate({"salaire_brut_global": {"2025": annual_salary}})

    # These annual amounts cannot be divided into twelve exact float32 values.
    assert simulation.calculate("salaire_brut_imposable", "2025")[0] == annual_salary
