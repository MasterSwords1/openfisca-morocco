"""Réforme : appliquer le barème de l'IR antérieur à 2025.

Le barème 2025 a relevé le seuil d'exonération de 30 000 à 40 000 DH et réduit
les taux des tranches supérieures. Cette réforme réintroduit l'ancien barème
pour l'analyse distributionnelle :

    0 – 30 000 : 0 %       30 001 – 50 000 : 10 % (3 000)
    50 001 – 60 000 : 20 % (8 000)   60 001 – 80 000 : 30 % (14 000)
    80 001 – 180 000 : 34 % (17 200)  > 180 000 : 38 % (24 400)

Les montants entre parenthèses sont les sommes à déduire. La réforme remplace
les seuils et taux à partir de 2025-01-01, date à laquelle le barème 2025 est
encodé ; elle ne modifie ni l'assiette ni les déductions.
"""

from openfisca_core.parameters import ParameterAtInstant
from openfisca_core.reforms import Reform

ANCIEN_BAREME = (
    (0.0, 0.00),
    (30_000.0, 0.10),
    (50_000.0, 0.20),
    (60_000.0, 0.30),
    (80_000.0, 0.34),
    (180_000.0, 0.38),
)


def _fixer(parameter, value):
    parameter.values_list = [
        ParameterAtInstant(parameter.name, "2025-01-01", {"value": value})
    ]


def modifier_bareme(parameters):
    brackets = parameters.impot_revenu.bareme.brackets
    if len(brackets) != len(ANCIEN_BAREME):
        raise ValueError("The baseline scale does not have the expected six brackets.")
    for bracket, (threshold, rate) in zip(brackets, ANCIEN_BAREME):
        _fixer(bracket.threshold, threshold)
        _fixer(bracket.rate, rate)
    return parameters


class ReformeBaremeIR(Reform):
    """IR calculé avec le barème antérieur à la réforme de 2025."""

    name = "Barème IR antérieur à 2025"

    def apply(self):
        self.modify_parameters(modifier_bareme)
