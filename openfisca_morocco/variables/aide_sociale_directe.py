"""Aide sociale directe (ASD), modélisée au niveau du ménage et au mois.

Sources : Loi n° 58-23, Décrets n° 2-23-1067 / 2-23-1068 et textes modificatifs,
publiés par l'Agence Nationale du Soutien Social. Le modèle calcule une
estimation des montants statutaires à partir d'entrées fournies; il ne reproduit
ni les registres administratifs ni la décision individuelle de l'ANSS.
"""

from numpy import maximum, where
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household, Person


class score_rsu(Variable):
    """Indice socio-économique RSU fourni par l'utilisateur; il n'est pas recalculé.

    Le Décret 2-23-1068 fixe la « عتبة الاستفادة » (seuil d'éligibilité) à
    9,743001 et renvoie à l'article 3, point 5, de la Loi 58-23. L'ANSS applique
    ce seuil à l'indice socio-économique calculé sur rsu.ma.
    """

    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Indice socio-économique RSU déclaré du ménage"
    reference = "https://www.anss.gov.ma/fr/conditions-d-eligibilite"


class conditions_administratives_asd_remplies(Variable):
    """Indique que les conditions d'inscription et de dossier sont vérifiées.

    Cette entrée regroupe les conditions dépendant des registres ou de la
    vérification ANSS; le modèle ne peut pas les établir à partir de ses données.
    """

    value_type = bool
    entity = Household
    definition_period = MONTH
    default_value = False
    label = "Conditions administratives d'accès à l'ASD vérifiées"
    reference = (
        "https://www.anss.gov.ma/fr/conditions-d-eligibilite"  # Loi 58-23, art. 3 et 7
    )


class eligible_aide_forfaitaire_asd(Variable):
    """Ménage relevant de l'allocation forfaitaire.

    L'allocation est versée lorsque aucun montant d'enfant n'est calculé pour le
    ménage (pas d'enfant à charge, enfant hors barème ou rang non renseigné).
    """

    value_type = bool
    entity = Household
    definition_period = MONTH
    default_value = False
    label = "Ménage satisfaisant la condition publiée pour l'aide forfaitaire"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Loi 58-23, art. 4


class enfant_eligible_asd(Variable):
    """Enfant de moins de 21 ans, ou relevant d'une dérogation légale."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant remplissant la condition d'âge ASD (ou dérogation)"
    reference = "https://www.anss.gov.ma/sites/default/files/decrets/Loi_n58.23_AR.pdf"  # Loi 58-23, art. 2 et 3


class enfant_orphelin_pere(Variable):
    """Indique le statut d'orphelin de père pour le soutien complémentaire ASD."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant orphelin de père"
    reference = "https://www.anss.gov.ma/fr/typologies-d-aides"  # Loi 58-23, art. 2; annexe du Décret 2-23-1067


class enfant_handicape(Variable):
    """Indique un handicap lourd.

    Le handicap ouvre le soutien complémentaire de 100 DH et retient le taux de
    base des enfants scolarisés ou de moins de six ans lorsque l'enfant n'est
    pas scolarisé.
    """

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant en situation de handicap lourd"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Annexe du Décret 2-23-1067
    )


class enfant_scolarise(Variable):
    """Indique si l'enfant est scolarisé pour le barème ASD."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant scolarisé au sens du barème d'aide sociale directe"
    reference = "https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1067_AR.pdf"  # Annexe du Décret 2-23-1067


class enfant_moins_de_six_ans(Variable):
    """Indique si l'enfant a moins de six ans."""

    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant âgé de moins de six ans"
    reference = "https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1067_AR.pdf"  # Annexe du Décret 2-23-1067


class rang_enfant_asd(Variable):
    """Rang ASD (1–6) fourni d'après le dossier; 0 si non concerné/inconnu."""

    value_type = int
    entity = Person
    definition_period = MONTH
    default_value = 0
    label = "Rang de l'enfant dans le barème ASD (fourni)"
    reference = "https://www.anss.gov.ma/sites/default/files/decrets/Loi_n58.23_AR.pdf"  # Loi 58-23, art. 2


class prime_naissance_rang(Variable):
    """Rang de naissance ouvrant potentiellement droit à prime ce mois (1 ou 2)."""

    value_type = int
    entity = Household
    definition_period = MONTH
    default_value = 0
    label = "Rang de la naissance ouvrant potentiellement droit à prime (1 ou 2)"
    reference = "https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1067_AR.pdf"  # Annexe du Décret 2-23-1067


class aide_sociale_directe(Variable):
    """Estimation mensuelle de l'ASD selon le seuil RSU et les entrées fournies.

    Le rang ASD est une entrée explicite, et non déduit de l'ordre des membres
    OpenFisca, qui ne représente pas nécessairement le rang légal du dossier.
    Le barème suit l'annexe du Décret 2-23-1067 telle que publiée par l'ANSS :
    montant de base selon le rang et la scolarisation, soutien complémentaire
    orphelin de père (trois premiers rangs) et soutien de 100 DH par enfant en
    situation de handicap lourd à tous les rangs. Hors prime de naissance, le
    total enfants + soutiens est relevé au plancher de 500 DH ; lorsqu'il est
    nul, le ménage reçoit l'allocation forfaitaire s'il y est éligible, sinon
    rien. La prime de naissance est ajoutée après ce calcul, uniquement le mois
    de l'événement. L'aide de rentrée scolaire, l'aide spéciale aux enfants
    placés et la prime exceptionnelle ne sont pas calculées ici.
    """

    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Estimation de l'aide sociale directe mensuelle du ménage"
    reference = "https://www.anss.gov.ma/fr/lois-decrets"  # Loi 58-23; Décrets 2-23-1067 et 2-23-1068

    def formula(household, period, parameters):
        params = parameters(period).prestations_sociales.aide_sociale_directe
        score = household("score_rsu", period)
        admin_ok = household("conditions_administratives_asd_remplies", period)
        eligible = admin_ok & (score <= params.seuil_score_rsu)

        child_role = household.members.has_role(Household.CHILD)
        child_is_eligible = household.members("enfant_eligible_asd", period)
        ranks = household.members("rang_enfant_asd", period)
        school_or_young = household.members(
            "enfant_scolarise", period
        ) | household.members("enfant_moins_de_six_ans", period)
        high_rate = school_or_young | household.members("enfant_handicape", period)
        child_total = household.filled_array(0.0)
        supplemental_total = household.filled_array(0.0)
        orphan = household.members("enfant_orphelin_pere", period)
        disabled = household.members("enfant_handicape", period)

        # Le soutien complémentaire handicap s'applique à tous les rangs
        # (dont le 7e et plus), alors que le montant de base est plafonné.
        supplemental_total += (
            household.sum(child_role & child_is_eligible & disabled & (ranks >= 1))
            * params.montant_complement_handicap
        )

        for rank in range(1, 7):
            in_rank = (
                child_role
                & child_is_eligible
                & (ranks == rank)
                & (rank <= params.plafond_enfants)
            )
            count_high = household.sum(in_rank & high_rate)
            count_low = household.sum(in_rank & ~high_rate)
            if rank <= 3:
                supplemental_total += (
                    household.sum(in_rank & orphan & (school_or_young | disabled))
                    * params.montant_complement_orphelin
                )
                child_total += (
                    count_high * params.montant_enfant_scolarise_ou_moins_de_6_ans
                    + count_low * params.montant_enfant_non_scolarise_6_ans_et_plus
                )
            else:
                child_total += (
                    count_high * params.montant_enfant_scolarise_rang_4_a_6
                    + count_low * params.montant_enfant_non_scolarise_rang_4_a_6
                )

        monthly_amount = maximum(
            child_total + supplemental_total,
            params.plancher_mensuel,
        )
        lump_sum_eligible = household("eligible_aide_forfaitaire_asd", period)
        monthly_amount = where(
            (child_total + supplemental_total) == 0,
            where(lump_sum_eligible, params.aide_forfaitaire_mensuelle, 0.0),
            monthly_amount,
        )
        birth_rank = household("prime_naissance_rang", period)
        birth_grant = where(
            birth_rank == 1,
            params.prime_naissance_premier_enfant,
            where(birth_rank == 2, params.prime_naissance_deuxieme_enfant, 0),
        )
        return where(eligible, monthly_amount + birth_grant, 0.0)
