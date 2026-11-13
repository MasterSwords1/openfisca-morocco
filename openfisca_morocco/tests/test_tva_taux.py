"""Les taux de TVA déclarés doivent être ceux du corpus, date par date.

Ce test est la contrepartie, côté OpenFisca, de la garde de provenance du
corpus. Le corpus ``morocco-holy-graph`` détient un dataset vérifié
(``laws/ma_tax_law/data/tva_rate_history.json``, PR #81) dont chaque taux est
adossé à une citation littérale d'une loi de finances. Les tables ci-dessous
recopient ce dataset ; si un paramètre du package s'en écarte, ce test échoue.

Deux invariants sont vérifiés :

1. **Valeurs.** Les quatre taux généraux et les sept trajectoires transitoires
   valent, à chaque date, ce que le corpus dit qu'ils valent.
2. **Existence.** Les taux de 14 % et 7 % sont marqués abrogés à partir du
   1er janvier 2024, et aucun taux transitoire n'est inventé avant cette date.
   Un taux qui n'existe pas ne doit pas pouvoir être appliqué en silence.
"""

import pytest
from openfisca_core.errors import ParameterNotFoundError

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()

# Transcribed from tva_rate_history.json, `periods[].rates`.
# Les valeurs de `en_vigueur` viennent de l'abrogation de l'article 98 et de la
# réécriture de l'article 99 par la loi n° 55-23.
GENERAL_RATES = [
    # date, taux normal, 14 %, 10 %, 7 %, 14 % en vigueur, 7 % en vigueur
    ("2004-06-15", 0.20, 0.14, 0.10, 0.07, 1, 1),
    ("2006-12-31", 0.20, 0.14, 0.10, 0.07, 1, 1),
    ("2007-01-01", 0.20, 0.14, 0.10, 0.07, 1, 1),
    ("2023-12-31", 0.20, 0.14, 0.10, 0.07, 1, 1),
    ("2024-01-01", 0.20, 0.14, 0.10, 0.07, 0, 0),
    ("2025-12-31", 0.20, 0.14, 0.10, 0.07, 0, 0),
    ("2026-06-15", 0.20, 0.14, 0.10, 0.07, 0, 0),
]

# Transcribed from `transitional_schedules[].steps`.
TRANSITIONAL_RATES = {
    "electricite": {
        "2024-01-01": 0.16,
        "2025-01-01": 0.18,
        "2026-01-01": 0.20,
    },
    "compteur_electricite": {
        "2024-01-01": 0.11,
        "2025-01-01": 0.15,
        "2026-01-01": 0.20,
    },
    "electricite_renouvelable": {
        "2024-01-01": 0.12,
        "2025-01-01": 0.10,
    },
    "sucre": {
        "2024-01-01": 0.08,
        "2025-01-01": 0.09,
        "2026-01-01": 0.10,
    },
    "transport_hors_urbain_et_routier": {
        "2024-01-01": 0.16,
        "2025-01-01": 0.18,
        "2026-01-01": 0.20,
    },
    "transport_urbain_et_routier": {
        "2024-01-01": 0.13,
        "2025-01-01": 0.12,
        "2026-01-01": 0.10,
    },
    "courtier_assurances": {
        "2024-01-01": 0.12,
        "2025-01-01": 0.10,
    },
}

GENERAL_RATE_DATES = [row[0] for row in GENERAL_RATES]
TRANSITIONAL_CASES = [
    (operation, start, rate)
    for operation, steps in TRANSITIONAL_RATES.items()
    for start, rate in steps.items()
]


@pytest.mark.parametrize(
    "day,normal,reduit_14,reduit_10,reduit_7,quatorze_en_vigueur,sept_en_vigueur",
    GENERAL_RATES,
    ids=GENERAL_RATE_DATES,
)
def test_taux_generaux_correspondent_au_corpus(
    day,
    normal,
    reduit_14,
    reduit_10,
    reduit_7,
    quatorze_en_vigueur,
    sept_en_vigueur,
):
    params = TBS.get_parameters_at_instant(day).tva.taux
    assert params.normal.taux == normal
    assert params.reduit_14.taux == reduit_14
    assert params.reduit_10.taux == reduit_10
    assert params.reduit_7.taux == reduit_7
    assert params.reduit_14.en_vigueur == quatorze_en_vigueur
    assert params.reduit_7.en_vigueur == sept_en_vigueur


@pytest.mark.parametrize(
    "operation,start,rate",
    TRANSITIONAL_CASES,
    ids=[f"{operation}-{start}" for operation, start, _ in TRANSITIONAL_CASES],
)
def test_taux_transitoires_correspondent_au_corpus(operation, start, rate):
    steps = TBS.get_parameters_at_instant(start).tva.transitoires
    assert getattr(steps, operation).taux == rate


def test_les_taux_transitoires_ne_sont_pas_anterieurs_a_2024():
    """Aucun taux transitoire n'existe avant le 1er janvier 2024.

    Les paramètres ne doivent donc pas fabriquer de valeur antérieure : une
    entreprise qui déclare une opération transitoire en 2023 relève des taux
    généraux de l'article 99, et le calcul doit renvoyer zéro, pas un taux
    inventé.
    """
    for operation in TRANSITIONAL_RATES:
        with pytest.raises(ParameterNotFoundError):
            _ = getattr(
                TBS.get_parameters_at_instant("2023-12-31").tva.transitoires, operation
            ).taux


def test_les_taux_generaux_sont_ceux_du_corpus_et_rien_d_autre():
    """Les taux déclarés restent dans l'ensemble fermé que le corpus atteste."""
    attested = {0.20, 0.14, 0.10, 0.07}
    for day in GENERAL_RATE_DATES:
        params = TBS.get_parameters_at_instant(day).tva.taux
        declared = {
            params.normal.taux,
            params.reduit_14.taux,
            params.reduit_10.taux,
            params.reduit_7.taux,
        }
        assert declared == attested, f"{day}: {declared} n'est pas l'ensemble attesté"


def test_les_taux_transitoires_convergent_vers_un_taux_general():
    """Le dernier palier d'une trajectoire est un taux général, pas un taux propre."""
    general = {rate for row in GENERAL_RATES for rate in row[1:5]}
    for operation, steps in TRANSITIONAL_RATES.items():
        last_start = max(steps)
        assert steps[last_start] in general, (
            f"{operation}: le dernier palier {steps[last_start]} n'est pas un taux général"
        )
