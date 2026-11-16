"""Taxe sur la valeur ajoutée (TVA) — déclaration d'entreprise.

Modèle de déclaration de TVA d'une entreprise, encodé depuis le Code Général
des Impôts (loi n° 43-06) tel que réformé par la loi de finances n° 55-23 pour
2024 :

- articles 98 et 99 : taux applicables (20 %, 10 %, et 14 % / 7 % jusqu'au
  31 décembre 2023) ;
- article 247-XXXXI : taux transitoires 2024-2026 pour sept catégories
  d'opérations ;
- article 100 : taux spécifiques en volume/masse de 2007 à 2019 ;
- articles 101 et 104 : droit à déduction et règle du prorata ;
- article 112 : déclaration mensuelle — d'où le période MONTH.

Les chiffres attendus par les tests sont ceux du modèle Catala validé du corpus
``morocco-holy-graph`` (``laws/ma_tax_law/catala/cgi_tva.catala_fr`` et son test
``test_tva_multi_rate_and_deductions`` : 257 000 / 150 000 / 107 000), et les
taux datés sont ceux de ``laws/ma_tax_law/data/tva_rate_history.json``.

Ce que ce module ne fait pas : il ne choisit pas le taux à la place de
l'entreprise. Les articles 91, 92 et 99 exposent des listes d'exemptions et de
catégories par snapshot dans des catalogues séparés; ils ne classent pas
automatiquement les descriptions de ventes. Le chiffre d'affaires est déclaré
par taux, et les opérations spécifiques de l'article 100 doivent être
explicitement fournies en hectolitres ou en grammes. Les snapshots ne
définissent pas une validité continue entre éditions.
"""

from datetime import date

import numpy
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Company
from openfisca_morocco.tva_article100 import list_article_100_rates


class OperationTauxTransitoire(Enum):
    """Catégories d'opérations soumises à un taux transitoire (art. 247-XXXXI)."""

    aucune = "Aucune opération à taux transitoire"
    electricite = "Énergie électrique"
    compteur_electricite = "Location du compteur d'électricité"
    electricite_renouvelable = "Ventes des producteurs d'électricité produite à partir d'énergies renouvelables"
    sucre = "Sucre raffiné ou aggloméré"
    transport_hors_urbain_et_routier = (
        "Transport de voyageurs et de marchandises hors transport urbain et routier"
    )
    transport_urbain_et_routier = (
        "Transport urbain et transport routier de voyageurs et de marchandises"
    )
    courtier_assurances = "Prestations des agents démarcheurs et courtiers d'assurances"


# --- Entrées de la déclaration -------------------------------------------


class chiffre_affaires_taux_normal(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Chiffre d'affaires du mois soumis au taux normal de 20 %"
    reference = "https://www.tax.gov.ma"  # CGI, articles 98 (2004-2023) et 99-A


class chiffre_affaires_taux_reduit_10(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Chiffre d'affaires du mois soumis au taux réduit de 10 %"
    reference = "https://www.tax.gov.ma"  # CGI, articles 99-2° (2004-2023) et 99-B


class chiffre_affaires_taux_reduit_14(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "Chiffre d'affaires du mois déclaré au taux réduit de 14 %, en vigueur "
        "jusqu'au 31 décembre 2023"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 99-3° (abrogé en 2024)


class chiffre_affaires_taux_reduit_7(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "Chiffre d'affaires du mois déclaré au taux réduit de 7 %, en vigueur "
        "jusqu'au 31 décembre 2023"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 99-1° (abrogé en 2024)


class tva_operation_transitoire(Variable):
    value_type = Enum
    entity = Company
    definition_period = MONTH
    possible_values = OperationTauxTransitoire
    default_value = OperationTauxTransitoire.aucune
    label = (
        "Catégorie d'opération soumise à un taux transitoire de TVA (article 247-XXXXI)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 247-XXXXI


class chiffre_affaires_taux_transitoire(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Chiffre d'affaires du mois relevant du taux transitoire déclaré"
    reference = "https://www.tax.gov.ma"  # CGI, article 247-XXXXI


class volume_vins_boissons_alcoolisees_article100(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "hectolitre"
    default_value = 0.0
    label = (
        "Volume vendu (hl) de vins et boissons alcoolisées relevant du taux "
        "spécifique de l'article 100, hors consommation sur place"
    )
    reference = "https://www.sgg.gov.ma/BO/bo_fr/2007/BO_5487-bis_fr.pdf"


class grammes_or_platine_article100(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "gramme"
    default_value = 0.0
    label = (
        "Grammes d'or et de platine contenus dans les ouvrages déjà classés "
        "sous l'article 100"
    )
    reference = "https://www.sgg.gov.ma/BO/bo_fr/2007/BO_5487-bis_fr.pdf"


class grammes_argent_article100(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "gramme"
    default_value = 0.0
    label = (
        "Grammes d'argent contenus dans les ouvrages déjà classés sous l'article 100"
    )
    reference = "https://www.sgg.gov.ma/BO/bo_fr/2007/BO_5487-bis_fr.pdf"


class tva_collectee_article100(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée aux taux spécifiques de l'article 100"
    reference = "https://www.sgg.gov.ma/BO/bo_fr/2007/BO_5487-bis_fr.pdf"

    def formula(entreprise, period, parameters):
        as_of = date(period.start.year, period.start.month, period.start.day)
        rates = {
            row.product_group: float(row.rate_value)
            for row in list_article_100_rates(as_of)
        }
        volume = entreprise("volume_vins_boissons_alcoolisees_article100", period)
        gold_platinum = entreprise("grammes_or_platine_article100", period)
        silver = entreprise("grammes_argent_article100", period)
        if not rates:
            return numpy.zeros_like(volume)
        return (
            volume * rates["wine_and_alcohol"]
            + gold_platinum * rates["gold_platinum"]
            + silver * rates["silver"]
        )


class quantites_article100_hors_periode(Variable):
    value_type = bool
    entity = Company
    definition_period = MONTH
    label = (
        "Signale des quantités d'article 100 déclarées en dehors des périodes "
        "de taux vérifiées (2007–2019)"
    )
    reference = "https://www.sgg.gov.ma/BO/bo_fr/2007/BO_5487-bis_fr.pdf"

    def formula(entreprise, period, parameters):
        as_of = date(period.start.year, period.start.month, period.start.day)
        volume = entreprise("volume_vins_boissons_alcoolisees_article100", period)
        gold_platinum = entreprise("grammes_or_platine_article100", period)
        silver = entreprise("grammes_argent_article100", period)
        if list_article_100_rates(as_of):
            return numpy.zeros_like(volume, dtype=bool)
        return (volume != 0) | (gold_platinum != 0) | (silver != 0)


class tva_deductible_charges(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA déductible du mois ayant grevé des biens et services"
    reference = "https://www.tax.gov.ma"  # CGI, article 101


class tva_deductible_immobilisations(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA déductible du mois ayant grevé des immobilisations"
    reference = "https://www.tax.gov.ma"  # CGI, article 101


class prorata_deduction(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "/1"
    default_value = 1.0
    label = (
        "Prorata de déduction applicable au mois (1 pour une activité entièrement "
        "taxable), article 104"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 104


class credit_tva_anterieur(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    default_value = 0.0
    label = "Crédit de TVA reporté de la période précédente"
    reference = "https://www.tax.gov.ma"  # CGI, articles 105 et 106


# --- Taux appliqués -------------------------------------------------------


class tva_taux_transitoire(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "/1"
    label = "Taux transitoire applicable à l'opération déclarée (0 si aucune)"
    reference = "https://www.tax.gov.ma"  # CGI, article 247-XXXXI

    def formula(entreprise, period, parameters):
        # Aucun taux transitoire n'existe avant le 1er janvier 2024: les
        # opérations concernées relevaient alors des taux généraux de
        # l'article 99 (14 % ou 7 %). On ne fabrique donc pas de valeur
        # antérieure dans les paramètres, et on renvoie zéro ici.
        if period.start.year < 2024:
            return 0

        operation = entreprise("tva_operation_transitoire", period)
        taux = parameters(period).tva.transitoires
        return (
            (operation == OperationTauxTransitoire.electricite)
            * float(taux.electricite.taux)
            + (operation == OperationTauxTransitoire.compteur_electricite)
            * float(taux.compteur_electricite.taux)
            + (operation == OperationTauxTransitoire.electricite_renouvelable)
            * float(taux.electricite_renouvelable.taux)
            + (operation == OperationTauxTransitoire.sucre) * float(taux.sucre.taux)
            + (operation == OperationTauxTransitoire.transport_hors_urbain_et_routier)
            * float(taux.transport_hors_urbain_et_routier.taux)
            + (operation == OperationTauxTransitoire.transport_urbain_et_routier)
            * float(taux.transport_urbain_et_routier.taux)
            + (operation == OperationTauxTransitoire.courtier_assurances)
            * float(taux.courtier_assurances.taux)
        )


# --- TVA collectée --------------------------------------------------------


class tva_collectee_taux_normal(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée au taux normal de 20 %"
    reference = "https://www.tax.gov.ma"  # CGI, articles 98 et 99-A

    def formula(entreprise, period, parameters):
        taux = parameters(period).tva.taux.normal.taux
        return entreprise("chiffre_affaires_taux_normal", period) * taux


class tva_collectee_taux_10(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée au taux réduit de 10 %"
    reference = "https://www.tax.gov.ma"  # CGI, articles 99-2° et 99-B

    def formula(entreprise, period, parameters):
        taux = parameters(period).tva.taux.reduit_10.taux
        return entreprise("chiffre_affaires_taux_reduit_10", period) * taux


class tva_collectee_taux_14(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée au taux réduit de 14 % (taux nul à partir de 2024)"
    reference = "https://www.tax.gov.ma"  # CGI, article 99-3°

    def formula(entreprise, period, parameters):
        taux = parameters(period).tva.taux.reduit_14
        return (
            entreprise("chiffre_affaires_taux_reduit_14", period)
            * taux.taux
            * taux.en_vigueur
        )


class tva_collectee_taux_7(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée au taux réduit de 7 % (taux nul à partir de 2024)"
    reference = "https://www.tax.gov.ma"  # CGI, article 99-1°

    def formula(entreprise, period, parameters):
        taux = parameters(period).tva.taux.reduit_7
        return (
            entreprise("chiffre_affaires_taux_reduit_7", period)
            * taux.taux
            * taux.en_vigueur
        )


class tva_collectee_taux_transitoire(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA collectée au taux transitoire de l'opération déclarée"
    reference = "https://www.tax.gov.ma"  # CGI, article 247-XXXXI

    def formula(entreprise, period, parameters):
        return entreprise("chiffre_affaires_taux_transitoire", period) * entreprise(
            "tva_taux_transitoire", period
        )


class tva_collectee_totale(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "TVA collectée totale du mois (taux généraux, taux transitoires et taux "
        "spécifiques de l'article 100 en vigueur)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, articles 98, 99, 100 et 247-XXXXI

    def formula(entreprise, period, parameters):
        return (
            entreprise("tva_collectee_taux_normal", period)
            + entreprise("tva_collectee_taux_10", period)
            + entreprise("tva_collectee_taux_14", period)
            + entreprise("tva_collectee_taux_7", period)
            + entreprise("tva_collectee_taux_transitoire", period)
            + entreprise("tva_collectee_article100", period)
        )


class chiffre_affaires_taux_abroge(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "Chiffre d'affaires déclaré sur un taux abrogé (14 % ou 7 % à partir de "
        "2024) — signale une déclaration incohérente avec le droit en vigueur"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 99 réécrit par la LF 55-23

    def formula(entreprise, period, parameters):
        taux = parameters(period).tva.taux
        return entreprise("chiffre_affaires_taux_reduit_14", period) * (
            1 - taux.reduit_14.en_vigueur
        ) + entreprise("chiffre_affaires_taux_reduit_7", period) * (
            1 - taux.reduit_7.en_vigueur
        )


# --- Déduction et liquidation --------------------------------------------


class tva_deductible_autorisee(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA déductible autorisée après application du prorata"
    reference = "https://www.tax.gov.ma"  # CGI, articles 101 et 104

    def formula(entreprise, period, parameters):
        brute = entreprise("tva_deductible_charges", period) + entreprise(
            "tva_deductible_immobilisations", period
        )
        return brute * entreprise("prorata_deduction", period)


class tva_nette_a_payer(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "TVA nette à payer au titre du mois (plancher à zéro)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 105 et 106

    def formula(entreprise, period, parameters):
        collectee = entreprise("tva_collectee_totale", period)
        deductible = entreprise("tva_deductible_autorisee", period) + entreprise(
            "credit_tva_anterieur", period
        )
        return numpy.maximum(collectee - deductible, 0)


class credit_tva_a_reporter(Variable):
    value_type = float
    entity = Company
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Crédit de TVA à reporter sur la période suivante"
    reference = "https://www.tax.gov.ma"  # CGI, articles 105 et 106

    def formula(entreprise, period, parameters):
        collectee = entreprise("tva_collectee_totale", period)
        deductible = entreprise("tva_deductible_autorisee", period) + entreprise(
            "credit_tva_anterieur", period
        )
        return numpy.maximum(deductible - collectee, 0)
