"""Plus-values immobilières et revenus de source étrangère.

Sources : Code Général des Impôts (édition 2026), articles 25, 61-II, 63, 65 et
73-II-C-2° / F-5° / F-6°.

Le profit net imposable est le prix de cession diminué des frais de cession,
moins le prix d'acquisition augmenté des frais d'acquisition évalués
forfaitairement à 15 % et des dépenses d'investissement (article 65). Le
coefficient de réévaluation du prix d'acquisition, publié annuellement par
l'administration, n'est pas encodé : la réévaluation n'est donc pas appliquée.

L'exonération de l'habitation principale exige cinq ans de détention
(article 63-II-B) ; les cessions dont le total annuel ne dépasse pas 140 000 DH
sont exonérées (article 63-II-A).

Les revenus étrangers autres que les capitaux mobiliers sont compris dans le
revenu global pour leur montant brut (article 25). Les revenus et profits de
capitaux mobiliers étrangers sont imposés aux taux spécifiques de 15 % et 20 %
(article 73-II-C-2° et F-5°). Les conventions fiscales et les crédits d'impôt
étrangers ne sont pas modélisés.
"""

from numpy import maximum as max_, where
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person


class prix_cession_immobilier(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Prix de cession de l'immeuble"
    reference = "https://maloi.ma/fr/law/code-impots/article/65"


class prix_acquisition_immobilier(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Prix d'acquisition de l'immeuble cédé"
    reference = "https://maloi.ma/fr/law/code-impots/article/65"


class frais_cession_immobilier(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Frais de cession de l'immeuble"
    reference = "https://maloi.ma/fr/law/code-impots/article/65"


class depenses_investissement_immobilier(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Dépenses d'investissement sur l'immeuble cédé"
    reference = "https://maloi.ma/fr/law/code-impots/article/65"


class total_cessions_immobilieres_annee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Montant total des cessions d'immeubles de l'année"
    reference = "https://maloi.ma/fr/law/code-impots/article/63"


class habitation_principale_cedee(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "L'immeuble cédé est l'habitation principale du contribuable"
    reference = "https://maloi.ma/fr/law/code-impots/article/63"


class annees_detention_habitation(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    label = "Années de détention de l'immeuble comme habitation principale"
    reference = "https://maloi.ma/fr/law/code-impots/article/63"


class plus_value_immobiliere_imposable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Profit net imposable de cession d'immeuble"
    reference = "https://maloi.ma/fr/law/code-impots/article/65"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            provided = (
                person("prix_cession_immobilier", period)
                + person("prix_acquisition_immobilier", period)
                + person("frais_cession_immobilier", period)
                + person("depenses_investissement_immobilier", period)
            )
            if (provided != 0).any():
                raise ValueError("Property gains are only modelled from 2026.")
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.patrimoine
        prix = max_(person("prix_cession_immobilier", period), 0)
        frais = max_(person("frais_cession_immobilier", period), 0)
        acquisition = max_(person("prix_acquisition_immobilier", period), 0)
        depenses = max_(person("depenses_investissement_immobilier", period), 0)

        total = person("total_cessions_immobilieres_annee", period)
        total = where(total > 0, total, prix)
        exonere_total = total <= params.seuil_exoneration_cessions

        residence = person("habitation_principale_cedee", period) & (
            person("annees_detention_habitation", period)
            >= params.duree_habitation_principale
        )

        cout = acquisition * (1 + params.frais_acquisition_forfait) + depenses
        profit = max_(prix - frais - cout, 0)
        return where(exonere_total | residence, 0.0, profit)


class impot_plus_value_immobiliere(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt sur le profit de cession d'immeuble"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            return person.filled_array(0.0)
        taux = parameters(period).impot_revenu.patrimoine.taux_plus_value_immobiliere
        return person("plus_value_immobiliere_imposable", period) * taux


class revenus_etrangers_bruts(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenus de source étrangère compris dans le revenu global"
    reference = "https://maloi.ma/fr/law/code-impots/article/25"


class revenus_capitaux_etrangers_bruts(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenus bruts de capitaux mobiliers de source étrangère"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"


class profits_capitaux_etrangers(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Profits bruts de capitaux mobiliers de source étrangère"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"


class impot_capitaux_etrangers(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt sur les revenus et profits de capitaux étrangers"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            provided = person("revenus_capitaux_etrangers_bruts", period) + person(
                "profits_capitaux_etrangers", period
            )
            if (provided != 0).any():
                raise ValueError("Foreign capital income is only modelled from 2026.")
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.patrimoine
        return (
            max_(person("revenus_capitaux_etrangers_bruts", period), 0)
            * params.taux_revenus_capitaux_etrangers
            + max_(person("profits_capitaux_etrangers", period), 0)
            * params.taux_profits_capitaux_etrangers
        )
