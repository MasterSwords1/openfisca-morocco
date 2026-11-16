"""Art. 28-III-A retirement-premium ceiling: salary-only, election and no salary.

The 50 %-of-net-salary branch cannot be exercised through a YAML simulation
without also modelling payroll contributions, so the cap rule is tested
directly.
"""

from types import SimpleNamespace

import numpy as np

from openfisca_morocco.variables.ir_deductions_globales import (
    plafond_assurance_retraite,
)

PARAMS = SimpleNamespace(taux_plafond_retraite=0.10, taux_plafond_retraite_salaire=0.50)


def _cap(salaire, base, autres):
    return float(
        plafond_assurance_retraite(
            np.array([salaire], dtype=float),
            np.array([base], dtype=float),
            np.array([autres]),
            PARAMS,
        )[0]
    )


def test_salary_only_uses_half_of_net_salary():
    assert _cap(90_000, 200_000, False) == 45_000


def test_salary_and_other_income_keeps_the_higher_cap():
    assert _cap(90_000, 200_000, True) == 45_000
    assert _cap(30_000, 1_000_000, True) == 100_000


def test_no_salary_uses_ten_percent_of_global_income():
    assert _cap(0, 200_000, True) == 20_000
