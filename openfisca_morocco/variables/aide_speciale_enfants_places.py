"""Aide spéciale aux enfants orphelins ou abandonnés placés en institution.

Sources : Loi n° 58-23, articles 1 et 16, et Décret n° 2-25-1064 du 2 Rajab
1447 (23 décembre 2025), BO n° 7468 du 25 décembre 2025. Le décret fixe l'aide
à 500 DH par enfant et par mois, verse les montants sur un compte ouvert au nom
de l'enfant à la Caisse de Dépôt et de Gestion, et prévoit un minimum de
10 000 DH versé à la majorité. Il entre en vigueur trois mois après sa
publication, soit le 25 mars 2026.

Deux entrées distinctes reproduisent l'article 9 : l'enfant est hébergé
(`enfant_place_institution`) et l'aide spéciale est accordée
(`aide_speciale_accordee`). C'est l'acceptation de la demande qui arrête le
versement de l'allocation mensuelle et du soutien complémentaire au titre de
cet enfant ; un enfant simplement hébergé, dont la demande est en cours,
continue donc à ouvrir droit à l'ASD du ménage.

Les autres conditions de l'article 1 (nationalité, inscription au registre,
absence de couverture par un régime d'allocations familiales, bourse) sont des
faits administratifs que le modèle ne calcule pas.
"""

from numpy import where
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household, Person


class enfant_place_institution(Variable):
    """Enfant orphelin ou abandonné hébergé dans un établissement de protection."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant hébergé dans un établissement de protection sociale"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Loi 58-23, art. 16


class aide_speciale_accordee(Variable):
    """Demande d'aide spéciale acceptée pour l'enfant placé (article 9)."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Demande d'aide spéciale acceptée"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-25-1064, art. 9
    )


class aide_speciale_enfant_place(Variable):
    """Aide spéciale mensuelle versée pour un enfant placé en institution."""

    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Aide spéciale mensuelle de l'enfant placé en institution"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-25-1064, art. 11
    )

    def formula(person, period, parameters):
        params = parameters(
            period
        ).prestations_sociales.aide_sociale_directe.aide_speciale_enfant_place
        concerne = person.has_role(Household.CHILD) & person(
            "enfant_place_institution", period
        )
        return where(
            concerne & person("aide_speciale_accordee", period),
            params.montant_mensuel,
            0.0,
        )
