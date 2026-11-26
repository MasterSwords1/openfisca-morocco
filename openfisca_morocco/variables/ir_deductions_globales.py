"""Déductions sur le revenu global et option foncière libératoire.

Sources : Code Général des Impôts (édition 2026), article 28 et articles 64-IV
et 73-II-F-12°.

Les dons ne sont pas plafonnés par l'article 28-I. Les intérêts de prêt logement
sont plafonnés à 10 % du revenu global. Les primes d'assurance retraite sont
plafonnées à 50 % du salaire net pour un contribuable dont les revenus sont
uniquement salariaux, à 10 % du revenu global en l'absence de salaire, et au plus
favorable des deux plafonds pour un contribuable qui a des revenus salariaux et
d'autres catégories. L'option de 20 % sur les loyers
bruts est libératoire : les loyers sortent du revenu global et la retenue de
10 %/15 % n'est plus imputée.
"""

from numpy import maximum as max_, minimum as min_, where
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person


class dons_organismes(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Dons aux organismes visés à l'article 10-I-B-2°"
    reference = "https://maloi.ma/fr/law/code-impots/article/28"


class interets_pret_logement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Intérêts de prêt pour l'habitation principale"
    reference = "https://maloi.ma/fr/law/code-impots/article/28"


class primes_assurance_retraite(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Primes d'assurance retraite déductibles"
    reference = "https://maloi.ma/fr/law/code-impots/article/28"


class option_foncier_liberatoire(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "Option pour l'imposition libératoire des loyers à 20 %"
    reference = "https://maloi.ma/fr/law/code-impots/article/64"


def plafond_assurance_retraite(salaire, base, autres_revenus, params):
    """Plafond de l'article 28-III-A, selon la composition du revenu."""
    plafond_salaire = salaire * params.taux_plafond_retraite_salaire
    plafond_global = base * params.taux_plafond_retraite
    return where(
        salaire > 0,
        where(autres_revenus, max_(plafond_salaire, plafond_global), plafond_salaire),
        plafond_global,
    )


class deductions_revenu_global(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Déductions de l'article 28, après application des plafonds"
    reference = "https://maloi.ma/fr/law/code-impots/article/28"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            provided = (
                (person("dons_organismes", period) != 0)
                | (person("interets_pret_logement", period) != 0)
                | (person("primes_assurance_retraite", period) != 0)
            )
            if provided.any():
                raise ValueError("Article 28 deductions are only modelled from 2026.")
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.deductions_globales
        base = person("revenu_global_imposable", period)

        logement = min_(
            max_(person("interets_pret_logement", period), 0),
            base * params.taux_plafond_logement,
        )

        salaire = person("salaire_net_imposable", period)
        autres_revenus = (
            (person("revenu_professionnel_net", period) != 0)
            | (person("revenus_fonciers_bruts", period) != 0)
            | (person("chiffre_affaires_professionnel", period) != 0)
            | (person("revenus_etrangers_bruts", period) != 0)
            | (person("revenus_capitaux_etrangers_bruts", period) != 0)
            | (person("dividendes_bruts", period) != 0)
            | (person("interets_bruts", period) != 0)
            | (person("plus_values_actions_cotees", period) != 0)
            | (person("plus_values_titres_non_cotes", period) != 0)
            | (person("profits_capitaux_etrangers", period) != 0)
        )
        # Article 28-III-A : 50 % du salaire net pour un contribuable dont les
        # revenus sont uniquement salariaux ; 10 % du revenu global sinon. Un
        # contribuable qui a aussi des revenus salariaux peut opter pour l'un ou
        # l'autre plafond : le modèle retient le plus favorable.
        plafond_retraite = plafond_assurance_retraite(
            salaire, base, autres_revenus, params
        )
        retraite = min_(
            max_(person("primes_assurance_retraite", period), 0),
            plafond_retraite,
        )

        dons = max_(person("dons_organismes", period), 0)
        return dons + logement + retraite


class revenu_imposable_apres_deductions(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenu global imposable après déductions de l'article 28"
    reference = "https://maloi.ma/fr/law/code-impots/article/28"

    def formula(person, period, parameters):
        return max_(
            person("revenu_global_imposable", period)
            - person("deductions_revenu_global", period),
            0,
        )


class impot_foncier_liberatoire(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt libératoire de 20 % sur les loyers bruts"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.deductions_globales
        brut = max_(person("revenus_fonciers_bruts", period), 0)
        return where(
            person("option_foncier_liberatoire", period),
            brut * params.taux_foncier_liberatoire,
            0.0,
        )
