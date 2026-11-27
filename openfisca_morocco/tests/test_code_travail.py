"""Code du travail — prime d'ancienneté, indemnité de licenciement et SMIG."""

import pytest
from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def simulate(person, period="2025-01"):
    return SimulationBuilder().build_from_dict(TBS, {"persons": {"worker": person}})


@pytest.mark.parametrize(
    ("anciennete", "taux"),
    [
        (1.99, 0.0),
        (2, 0.05),
        (4.99, 0.05),
        (5, 0.10),
        (11.99, 0.10),
        (12, 0.15),
        (19.99, 0.15),
        (20, 0.20),
        (24.99, 0.20),
        (25, 0.25),
    ],
)
def test_seniority_bonus_rate_at_each_threshold(anciennete, taux):
    simulation = simulate(
        {
            "salaire_de_base": {"2025-01": 6000},
            "anciennete_annees": {"2025-01": anciennete},
        }
    )

    assert simulation.calculate("prime_anciennete_legale", "2025-01")[
        0
    ] == pytest.approx(6000 * taux, abs=0.01)


@pytest.mark.parametrize(
    ("anciennete", "heures"),
    [
        (0.49, 0),
        (0.5, 96),
        (5, 480),
        (6, 624),
        (10, 1200),
        (11, 1392),
        (15, 2160),
        (16, 2400),
        (21, 3600),
        (26, 4800),
    ],
)
def test_severance_hours_per_bracket(anciennete, heures):
    # Set the gross salary directly so the seniority bonus does not change the
    # hourly reference; this isolates the article 53 hour schedule.
    simulation = simulate(
        {
            "salaire_brut_global": {"2025-01": 6000},
            "anciennete_annees": {"2025-01": anciennete},
            "licenciement_sans_faute": {"2025-01": True},
        }
    )

    hourly = 6000 / 191
    assert simulation.calculate("indemnite_licenciement_legale", "2025-01")[
        0
    ] == pytest.approx(heures * hourly, abs=0.05)


def test_severance_requires_six_months_and_a_non_fault_dismissal():
    for anciennete, sans_faute, expected in [
        (0.49, True, 0),
        (0.5, True, 96 * 6000 / 191),
        (6, False, 0),
    ]:
        simulation = simulate(
            {
                "salaire_brut_global": {"2025-01": 6000},
                "anciennete_annees": {"2025-01": anciennete},
                "licenciement_sans_faute": {"2025-01": sans_faute},
            }
        )
        assert simulation.calculate("indemnite_licenciement_legale", "2025-01")[
            0
        ] == pytest.approx(expected, abs=0.05)


def test_severance_is_floored_at_the_smig():
    simulation = simulate(
        {
            "salaire_brut_global": {"2025-01": 2000},
            "anciennete_annees": {"2025-01": 1},
            "licenciement_sans_faute": {"2025-01": True},
        }
    )
    assert simulation.calculate("indemnite_licenciement_legale", "2025-01")[
        0
    ] == pytest.approx(96 * 17.10, abs=0.05)

    simulation = simulate(
        {
            "salaire_brut_global": {"2026-01": 3000},
            "anciennete_annees": {"2026-01": 1},
            "licenciement_sans_faute": {"2026-01": True},
        }
    )
    assert simulation.calculate("indemnite_licenciement_legale", "2026-01")[
        0
    ] == pytest.approx(96 * 17.92, abs=0.05)


def test_smig_compliance_threshold():
    for period, salary, expected in [
        ("2025-01", 3266.10, True),
        ("2025-01", 3266.09, False),
        ("2026-01", 3422.72, True),
        ("2026-01", 3422.71, False),
    ]:
        simulation = simulate(
            {"salaire_brut_global": {period: salary}},
            period=period,
        )
        assert (
            bool(simulation.calculate("salaire_conforme_smig", period)[0]) is expected
        )


def test_smig_compliance_with_annual_inputs():
    # Annual inputs are divided by twelve and stored as float32; at the exact
    # centime the division can land a fraction below the SMIG. The compliance
    # check must still return the published verdict.
    for year, monthly, expected in [
        ("2025", 3266.10, True),
        ("2025", 3266.09, False),
        ("2026", 3422.72, True),
        ("2026", 3422.71, False),
    ]:
        simulation = simulate({"salaire_brut_global": {year: monthly * 12}})
        assert (
            bool(simulation.calculate("salaire_conforme_smig", f"{year}-01")[0])
            is expected
        )

    simulation = simulate({"salaire_de_base": {"2025": 3266.10 * 12}})
    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == pytest.approx(
        3266.10, abs=0.001
    )
    assert bool(simulation.calculate("salaire_conforme_smig", "2025-01")[0]) is True


def test_gross_salary_includes_the_legal_seniority_bonus():
    simulation = simulate(
        {
            "salaire_de_base": {"2025-01": 6000},
            "anciennete_annees": {"2025-01": 3},
        }
    )
    assert simulation.calculate("prime_anciennete_legale", "2025-01")[
        0
    ] == pytest.approx(300, abs=0.01)
    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == pytest.approx(
        6300, abs=0.01
    )


def test_direct_gross_salary_input_bypasses_the_bonus_formula():
    # Documented override: an explicit salaire_brut_global wins over the
    # formula, so the caller must include the bonus in that input.
    simulation = simulate(
        {
            "salaire_de_base": {"2025-01": 6000},
            "salaire_brut_global": {"2025-01": 6000},
            "anciennete_annees": {"2025-01": 3},
        }
    )
    assert simulation.calculate("prime_anciennete_legale", "2025-01")[
        0
    ] == pytest.approx(300, abs=0.01)
    assert simulation.calculate("salaire_brut_global", "2025-01")[0] == pytest.approx(
        6000, abs=0.01
    )


def test_annual_base_salary_is_divided_before_the_bonus():
    simulation = simulate(
        {
            "salaire_de_base": {"2025": 72000},
            "anciennete_annees": {"2025-01": 3},
        }
    )
    assert simulation.calculate("salaire_de_base", "2025-01")[0] == pytest.approx(
        6000, abs=0.01
    )
    assert simulation.calculate("prime_anciennete_legale", "2025-01")[
        0
    ] == pytest.approx(300, abs=0.01)


def test_labor_code_before_july_2004_raises():
    simulation = simulate(
        {
            "salaire_de_base": {"2004-06": 6000},
            "anciennete_annees": {"2004-06": 3},
        }
    )
    with pytest.raises(ValueError, match="only modelled from July 2004"):
        simulation.calculate("prime_anciennete_legale", "2004-06")


@pytest.mark.parametrize(
    "period", ["2004-07", "2015-07", "2022-09", "2025-01", "2026-01"]
)
def test_monthly_smig_is_the_hourly_rate_times_191(period):
    params = TBS.parameters(period).code_travail.smig
    assert params.smig_mensuel == pytest.approx(
        round(params.smig_horaire * params.heures_mensuelles, 2), abs=0.01
    )
