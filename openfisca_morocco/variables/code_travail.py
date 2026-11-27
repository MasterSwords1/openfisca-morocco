"""Code du travail — primes et indemnités légales.

Règles encodées à partir de la Loi n° 65-99 portant Code du travail
(BO n° 5167 du 8 décembre 2003, complété par le BO n° 5210) :

- article 350 : prime d'ancienneté de 5 % après deux ans, 10 % après cinq ans,
  15 % après douze ans, 20 % après vingt ans et 25 % après vingt-cinq ans ;
- article 353 : assiette de la prime (salaire, accessoires et majorations pour
  heures supplémentaires, hors éléments exclus) ;
- articles 52 et 53 : indemnité de licenciement après six mois d'ancienneté,
  à raison de 96, 144, 192 ou 240 heures de salaire par année ou fraction
  d'année selon la tranche ;
- article 356 : salaire minimum légal, dont le SMIG non agricole est fixé par
  décret et calculé sur 191 heures par mois.

L'assiette de la prime est l'entrée `salaire_de_base` : l'appelant y agrège
les éléments retenus par l'article 353. `salaire_brut_global` est ensuite
recalculé comme `salaire_de_base + prime_anciennete_legale` lorsque
l'utilisateur ne fournit pas directement `salaire_brut_global`.

L'indemnité de licenciement utilise le salaire brut global du mois comme
approximation de la moyenne des salaires des cinquante-deux semaines
précédant la rupture (art. 55), avec un plancher au SMIG (art. 56). Les
dommages-intérêts pour licenciement abusif, l'indemnité de préavis, la
majoration de 100 % des délégués (art. 58) et l'indemnité de perte d'emploi
ne sont pas modélisées.
"""

from numpy import ceil, maximum as max_, minimum as min_, where
from openfisca_core.holders import set_input_divide_by_period
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person

_CODE_DU_TRAVAIL = "https://www.sgg.gov.ma/BO/bo_ar/2003/BO_5167_ar.pdf"

# Salaries are stored as float32. An annual amount divided by twelve can land
# a fraction below the exact centime (for example 3,266.0998 for 3,266.10), so
# the compliance check allows half a centime and stays at the published centime.
_CENTIME_TOLERANCE = 0.005


def _check_labor_period(period):
    """The Code du travail and the SMIG series are modelled from July 2004."""
    if (period.start.year, period.start.month) < (2004, 7):
        raise ValueError("The Code du travail is only modelled from July 2004.")


class salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    set_input = set_input_divide_by_period
    unit = "currency-MAD"
    label = (
        "Salaire de base mensuel servant d'assiette à la prime d'ancienneté "
        "(articles 350 et 353)"
    )
    reference = _CODE_DU_TRAVAIL

    # Entrée : l'appelant agrège les éléments retenus par l'article 353.


class anciennete_annees(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "year"
    label = (
        "Ancienneté du salarié dans la même entreprise, en années "
        "(une fraction d'année est acceptée)"
    )
    reference = _CODE_DU_TRAVAIL

    # Entrée : l'ancienneté est une donnée de paie, non calculée depuis une
    # date d'embauche. Les périodes assimilées (art. 351 et 352) sont à la
    # charge de l'appelant.


class prime_anciennete_legale(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Prime d'ancienneté légale mensuelle (article 350)"
    reference = _CODE_DU_TRAVAIL

    def formula(person, period, parameters):
        _check_labor_period(period)
        params = parameters(period).code_travail.prime_anciennete
        anciennete = person("anciennete_annees", period)
        # Paliers, pas taux marginaux : le taux le plus élevé atteint s'applique
        # à toute l'assiette.
        taux = where(
            anciennete >= params.seuil_25_ans,
            params.taux_25_ans,
            where(
                anciennete >= params.seuil_20_ans,
                params.taux_20_ans,
                where(
                    anciennete >= params.seuil_12_ans,
                    params.taux_12_ans,
                    where(
                        anciennete >= params.seuil_5_ans,
                        params.taux_5_ans,
                        where(
                            anciennete >= params.seuil_2_ans,
                            params.taux_2_ans,
                            0.0,
                        ),
                    ),
                ),
            ),
        )
        return person("salaire_de_base", period) * taux


class licenciement_sans_faute(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    label = (
        "Licenciement prononcé pour un motif autre qu'une faute grave "
        "(articles 52 et 61)"
    )
    reference = _CODE_DU_TRAVAIL

    # Entrée : le motif du licenciement est une décision de l'employeur, pas
    # une donnée calculable.


class indemnite_licenciement_legale(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Indemnité légale de licenciement (articles 52 et 53)"
    reference = _CODE_DU_TRAVAIL

    def formula(person, period, parameters):
        _check_labor_period(period)
        params = parameters(period).code_travail.indemnite_licenciement
        smig = parameters(period).code_travail.smig
        anciennete = person("anciennete_annees", period)
        eligible = (anciennete >= params.anciennete_minimale_mois / 12) & person(
            "licenciement_sans_faute", period
        )
        # « Pour chaque année ou fraction d'année » : une fraction compte pour
        # une année entière.
        annees = ceil(anciennete)
        heures = (
            params.heures_par_annee_1_5 * min_(annees, 5)
            + params.heures_par_annee_6_10 * min_(max_(annees - 5, 0), 5)
            + params.heures_par_annee_11_15 * min_(max_(annees - 10, 0), 5)
            + params.heures_par_annee_16_plus * max_(annees - 15, 0)
        )
        # Art. 55 : moyenne des salaires des 52 semaines précédentes. Le mois
        # courant est utilisé comme approximation. Art. 56 : plancher au SMIG.
        salaire_reference = max_(
            person("salaire_brut_global", period), smig.smig_mensuel
        )
        salaire_horaire = salaire_reference / smig.heures_mensuelles
        return where(eligible, heures * salaire_horaire, 0.0)


class salaire_conforme_smig(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    label = "Le salaire brut global atteint-il le SMIG mensuel ? (article 356)"
    reference = _CODE_DU_TRAVAIL

    def formula(person, period, parameters):
        _check_labor_period(period)
        smig = parameters(period).code_travail.smig
        return person("salaire_brut_global", period) >= (
            smig.smig_mensuel - _CENTIME_TOLERANCE
        )
