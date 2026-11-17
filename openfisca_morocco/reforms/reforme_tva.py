"""Réforme : ramener le taux normal de TVA de 20 % à 18 %.

Illustration d'une réforme de taux : le taux normal de l'article 99-A est
modifié à partir de 2025-01-01, sans toucher aux taux réduits ni aux régimes
transitoires. Le taux de 10 % reste celui de l'article 99-B.
"""

from openfisca_core.parameters import ParameterAtInstant
from openfisca_core.reforms import Reform


def modifier_taux_normal(parameters):
    taux = parameters.tva.taux.normal.taux
    # Keep the 2004-2024 history and add the 2025 rate after it.
    history = [value for value in taux.values_list if value.instant_str < "2025-01-01"]
    # values_list is in reverse chronological order.
    taux.values_list = [
        ParameterAtInstant(taux.name, "2025-01-01", {"value": 0.18})
    ] + history
    return parameters


class ReformeTVA(Reform):
    """TVA au taux normal de 18 % à partir de 2025."""

    name = "Taux normal de TVA à 18 %"

    def apply(self):
        self.modify_parameters(modifier_taux_normal)
