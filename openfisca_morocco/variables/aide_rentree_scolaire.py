"""Aide de rentrée scolaire de l'ASD, versée au mois de septembre.

Source : Décret n° 2-24-706 du 19 Muharram 1446 (25 juillet 2024), BO n° 7321
du 29 juillet 2024, qui complète l'annexe du Décret n° 2-23-1067. La ligne de
l'annexe vise les enfants scolarisés dans un établissement d'enseignement
public : 200 DH par enfant au primaire ou au collégial, 300 DH par enfant au
secondaire qualifiant, dans la limite de six enfants scolarisés par ménage.

L'aide est versée en septembre : au début du mois aux ménages qui ont reçu
l'ASD mensuelle en août, à la fin du mois avec l'ASD mensuelle pour les ménages
devenus éligibles en septembre. Le modèle paie en septembre si le ménage est
éligible ce mois-là ou le mois précédent ; la différence de date de versement
n'est pas reproduite.

Le plafond porte sur le nombre d'enfants, pas sur leur rang : l'annexe ne
publie aucun ordre de priorité. Le modèle retient d'abord les enfants du
secondaire qualifiant (300 DH), puis ceux du primaire et du collégial (200 DH),
ce qui est la lecture la plus favorable au ménage. Un enfant hébergé dans un
établissement de protection sociale est exclu pour éviter un double soutien ;
cette exclusion est un choix de modélisation, la règle de non-cumul du Décret
2-25-1064 ne visant que l'allocation mensuelle et le soutien complémentaire.
"""

from numpy import minimum, where
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household, Person


class NiveauScolaireAsd(Enum):
    """Niveau d'enseignement ouvrant droit à l'aide de rentrée scolaire."""

    non_renseigne = "Niveau non renseigné"
    primaire_collegial = "Primaire ou secondaire collégial"
    qualifiant = "Secondaire qualifiant"


class niveau_scolaire_asd(Variable):
    """Niveau déclaré de l'enfant pour l'aide de rentrée scolaire.

    Ce niveau est l'entrée de référence pour l'aide de rentrée ; il ne remplace
    pas `enfant_scolarise`, qui pilote le barème mensuel.
    """

    value_type = Enum
    entity = Person
    definition_period = MONTH
    possible_values = NiveauScolaireAsd
    default_value = NiveauScolaireAsd.non_renseigne
    label = "Niveau d'enseignement de l'enfant (aide de rentrée scolaire)"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-24-706


class scolarise_etablissement_public(Variable):
    """Enfant scolarisé dans un établissement d'enseignement public."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant scolarisé dans un établissement public"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-24-706


class aide_rentree_scolaire(Variable):
    """Aide de rentrée scolaire du ménage, due uniquement en septembre.

    Le plafond de six enfants est appliqué au nombre d'enfants éligibles, en
    retenant d'abord le taux qualifiant (300 DH). Un enfant hébergé dans un
    établissement de protection sociale est exclu.
    """

    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Aide de rentrée scolaire du ménage (septembre)"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-24-706

    def formula(household, period, parameters):
        if period.start.month != 9:
            return household.filled_array(0.0)

        asd = parameters(period).prestations_sociales.aide_sociale_directe
        params = asd.aide_rentree_scolaire

        score = household("score_rsu", period)
        admin_ok = household("conditions_administratives_asd_remplies", period)
        eligible_now = admin_ok & (score <= asd.seuil_score_rsu)

        august = period.last_month
        august_asd = parameters(august).prestations_sociales.aide_sociale_directe
        eligible_august = household(
            "conditions_administratives_asd_remplies", august
        ) & (household("score_rsu", august) <= august_asd.seuil_score_rsu)

        level = household.members("niveau_scolaire_asd", period)
        counted = (
            household.members.has_role(Household.CHILD)
            & household.members("enfant_eligible_asd", period)
            & household.members("scolarise_etablissement_public", period)
            & ~household.members("enfant_place_institution", period)
        )

        count_qualifiant = household.sum(
            counted & (level == NiveauScolaireAsd.qualifiant)
        )
        count_primaire = household.sum(
            counted & (level == NiveauScolaireAsd.primaire_collegial)
        )
        cap = params.plafond_enfants
        paid_qualifiant = minimum(count_qualifiant, cap)
        paid_primaire = minimum(count_primaire, cap - paid_qualifiant)
        total = (
            paid_qualifiant * params.montant_qualifiant
            + paid_primaire * params.montant_primaire_collegial
        )
        return where(eligible_now | eligible_august, total, 0.0)
