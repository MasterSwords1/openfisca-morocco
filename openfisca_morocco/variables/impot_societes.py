"""Impôt sur les sociétés (IS) et cotisation minimale (CM).

Sources : Code Général des Impôts (édition 2026), articles 19 et 144.

IS (article 19) :
- 20 % pour les bénéfices inférieurs à 100 000 000 DH, sous réserve que le
  bénéfice soit resté sous ce seuil pendant trois exercices consécutifs ;
- 35 % à partir de 100 000 000 DH, sous réserve des exclusions de
  l'article 19-I-B (Casablanca Finance City, zones d'accélération industrielle,
  convention d'investissement d'au moins 1,5 milliard de DH) ;
- 40 % pour les établissements de crédit et organismes assimilés, Bank
  Al-Maghrib, la Caisse de dépôt et de gestion et les entreprises d'assurances
  et de réassurance.

CM (article 144) : assise sur le chiffre d'affaires hors taxes et les autres
produits d'exploitation et financiers, au taux de 0,25 %, ramené à 0,15 % pour
les ventes des produits listés, avec un minimum de 3 000 DH pour les sociétés.
Le taux de 4 % des professions des articles 89-I-12° et 91-VI-1° vise les
contribuables soumis à l'IR ; il ne s'applique pas à l'entité `Company`.

Le modèle ne reconstitue pas le bénéfice fiscal à partir de la comptabilité :
`benefice_fiscal` est une entrée. La condition des trois exercices et les
exclusions du taux de 35 % sont des affirmations de l'appelant. L'exonération
de CM des 36 premiers mois (plafonnée à 60 mois depuis la constitution) est
également une entrée, `exonere_cotisation_minimale` ; les dates de constitution
et de début d'exploitation ne sont pas des inputs.
"""

from numpy import clip, maximum as max_, where
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Company


class benefice_fiscal(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Bénéfice net fiscal de l'exercice (négatif en cas de déficit)"
    reference = "https://www.tax.gov.ma"  # CGI, article 19


class chiffre_affaires_annuel(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Chiffre d'affaires annuel hors taxes"
    reference = "https://www.tax.gov.ma"  # CGI, article 144-I-B


class produits_accessoires_financiers(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Autres produits d'exploitation, produits financiers et subventions "
        "inclus dans la base de la cotisation minimale"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 144-I-B


class chiffre_affaires_produits_taux_reduit(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Chiffre d'affaires des ventes de produits pétroliers, gaz, beurre, "
        "huile, sucre, farine, eau, électricité et médicaments"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 144-I-D


class est_etablissement_financier(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = False
    label = (
        "Établissement de crédit ou organisme assimilé, Bank Al-Maghrib, CDG "
        "ou entreprise d'assurances et de réassurance"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 19-I-C


class benefice_sous_seuil_trois_ans(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = True
    label = (
        "Le bénéfice est resté inférieur à 100 000 000 DH pendant trois "
        "exercices consécutifs"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 19-I-B


class exclusion_taux_35(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = False
    label = (
        "Société exclue du taux de 35 % (Casablanca Finance City, zone "
        "d'accélération industrielle ou convention d'investissement)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 19-I-B


class exonere_cotisation_minimale(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = False
    label = (
        "Société exonérée de cotisation minimale au titre des 36 premiers "
        "mois d'exploitation (dans la limite de 60 mois depuis la constitution)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 144-I-C


class credit_impot(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Crédits d'impôt imputables sur l'IS"
    reference = "https://www.tax.gov.ma"  # CGI, articles 19 et 144


class benefice_atteint_100m(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    label = (
        "Le bénéfice net atteint 100 000 000 DH ; la comparaison par défaut "
        "suit la valeur stockée en float32 et peut être déclarée par l'appelant"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 19-I-B

    def formula(company, period, parameters):
        return (
            company("benefice_fiscal", period)
            >= parameters(period).impot_societes.taux.seuil_taux_eleve
        )


class taux_is_applique(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "/1"
    label = "Taux d'IS appliqué au bénéfice fiscal"
    reference = "https://www.tax.gov.ma"  # CGI, article 19

    def formula(company, period, parameters):
        params = parameters(period).impot_societes.taux
        au_dessus = company("benefice_atteint_100m", period)
        taux_eleve = (au_dessus | ~company("benefice_sous_seuil_trois_ans", period)) & (
            ~company("exclusion_taux_35", period)
        )
        return where(
            company("est_etablissement_financier", period),
            params.taux_financier,
            where(taux_eleve, params.taux_eleve, params.taux_normal),
        )


class is_theorique(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt sur les sociétés théorique sur le bénéfice fiscal"
    reference = "https://www.tax.gov.ma"  # CGI, article 19

    def formula(company, period, parameters):
        return max_(company("benefice_fiscal", period), 0) * company(
            "taux_is_applique", period
        )


class base_cotisation_minimale(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Base de la cotisation minimale (chiffre d'affaires et autres produits)"
    reference = "https://www.tax.gov.ma"  # CGI, article 144-I-B

    def formula(company, period, parameters):
        return max_(company("chiffre_affaires_annuel", period), 0) + max_(
            company("produits_accessoires_financiers", period), 0
        )


class cotisation_minimale(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Cotisation minimale due par la société"
    reference = "https://www.tax.gov.ma"  # CGI, article 144

    def formula(company, period, parameters):
        params = parameters(period).impot_societes.cotisation_minimale
        ca = max_(company("chiffre_affaires_annuel", period), 0)
        produits = max_(company("produits_accessoires_financiers", period), 0)
        reduit = clip(company("chiffre_affaires_produits_taux_reduit", period), 0, ca)
        cm = (
            reduit * params.taux_produits_reduits
            + (ca + produits - reduit) * params.taux_normal
        )
        return where(
            company("exonere_cotisation_minimale", period),
            0.0,
            max_(cm, params.minimum_societe),
        )


class is_du_brut(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "IS dû avant imputation des crédits (maximum de l'IS et de la CM)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 19 et 144

    def formula(company, period, parameters):
        return max_(
            company("is_theorique", period),
            company("cotisation_minimale", period),
        )


class is_net_a_payer(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "IS net à payer après imputation des crédits d'impôt"
    reference = "https://www.tax.gov.ma"  # CGI, articles 19 et 144

    def formula(company, period, parameters):
        return max_(
            company("is_du_brut", period) - max_(company("credit_impot", period), 0),
            0,
        )
