"""Prestations sociales — Allocations familiales (CNSS).

Modélisation du régime des allocations familiales servies par la Caisse Nationale
de Sécurité Sociale (CNSS) aux assurés sociaux ayant des enfants à charge.

Cadre législatif et réglementaire :
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 relatif au régime de sécurité
  sociale (articles 40 et 41 ; article 40 pour l'affiliation, la résidence et
  le plafond de six enfants, article 41 pour le taux).
- Décret n° 2-72-541, article 6 (modifié par le décret n° 2-96-319) : âges
  limites et situations ouvrant droit.
- Décret n° 2-08-358 du 9 juillet 2008, modifié par le décret n° 2-19-750 puis
  par le décret n° 2-23-715 du 29 octobre 2025 (BO n° 7453) :
  * 300 DH par mois pour chacun des 3 premiers enfants (rangs 1 à 3) ;
  * 36 DH par mois pour les rangs 4 à 6 de 2019-07 à 2022-12 (le régime
    antérieur à 2019-07 n'est pas encodé) ;
  * 100 DH par mois pour les rangs 4 à 6 depuis 2023-01-01 (effet rétroactif
    du décret 2-23-715) ;
  * plafond légal de 6 enfants par assuré social.

Conditions d'ouverture du droit (Décret 2-72-541, art. 6 ; Dahir 1-72-184,
art. 40 et 41) : l'enfant doit résider au Maroc et être à la charge de
l'assuré. L'âge limite dépend de la situation :
- moins de 12 ans : droit sans condition de scolarité ;
- de 12 à moins de 21 ans : enfant scolarisé ou poursuivant des études au
  Maroc ou à l'étranger ;
- de 12 à moins de 18 ans : enfant placé en apprentissage ;
- sans limite d'âge : enfant en situation de handicap, sans revenu, lorsque le
  handicap est survenu avant la limite d'âge applicable à sa situation
  (12/18/21 ans). La date de survenance n'est pas un input :
  `enfant_handicape_cnss` doit être déclaré par l'appelant comme couvrant ce
  cas.

La condition d'affiliation (108 jours de cotisations, art. 40), la résidence
effective au Maroc, la charge exclusive et effective de l'enfant de moins de
12 ans, la preuve de la scolarité ou du handicap, la condition de rémunération
d'au moins 60 % du SMIG/SMAG (Décret 2-08-358, art. 2), la condition de
ressources du père (loi n° 07-92, art. 21) et le cas de la fille ou sœur de
l'article 6(e) ne sont pas modélisés. Les inputs `enfant_*_cnss` permettent de déclarer la situation de
chaque enfant ; un enfant de moins de 12 ans est éligible par défaut **si son
âge est connu** (une date de naissance absente donne un âge bien au-delà des limites et
n'ouvre pas le droit au titre de l'âge ; seule la branche handicap peut alors
s'appliquer).
L'âge est apprécié au premier jour du mois : l'enfant né le 1er atteint la
limite ce mois-là, celui né après le 1er le mois suivant. Un enfant dépendant doit être placé dans le rôle `children`, y compris
lorsqu'il est majeur ou handicapé : le rôle décrit la dépendance, pas l'âge.

Le rang est la position parmi les enfants éligibles, et non l'ordre de
naissance : des enfants devenus inéligibles ne consomment pas de rang.

Entités :
- `nombre_enfants` : Nombre d'enfants à charge ouvrant droit (Household, entier, MONTH)
- `allocations_familiales` : Montant mensuel servi au ménage (Household, float, MONTH)
"""

from numpy import clip, datetime64
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household, Person


class enfant_scolarise_cnss(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant scolarisé ou poursuivant des études de 12 à moins de 21 ans au sens des allocations familiales CNSS"
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"


class enfant_apprenti_cnss(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant en apprentissage de 12 à moins de 18 ans au sens des allocations familiales CNSS"
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"


class enfant_etudes_superieures_cnss(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = "Enfant de 12 à moins de 21 ans poursuivant des études supérieures (variante de enfant_scolarise_cnss)"
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"


class enfant_handicape_cnss(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = (
        "Enfant en situation de handicap survenu avant la limite d'âge applicable, "
        "au sens des allocations familiales CNSS"
    )
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"


class enfant_handicape_sans_revenu_cnss(Variable):
    value_type = bool
    entity = Person
    definition_period = MONTH
    default_value = False
    label = (
        "Enfant handicapé sans revenu stable ; la condition de ressources du père "
        "(loi n° 07-92, art. 21) doit être vérifiée par l'appelant"
    )
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"


class nombre_enfants(Variable):
    value_type = int
    entity = Household
    definition_period = MONTH
    label = (
        "Nombre d'enfants à charge remplissant les conditions d'âge (rôle "
        "children, non plafonné ; le plafond de 6 s'applique au montant)"
    )
    reference = "https://www.acaps.ma/sites/default/files/publication_documents/decret_ndeg_2-72-541.pdf"  # Décret 2-72-541, art. 6

    def formula(household, period, parameters):
        """Compte les enfants du rôle CHILD qui remplissent les conditions d'âge."""
        age = household.members("age", period)
        birth = household.members("birth", period)
        scolarise = household.members("enfant_scolarise_cnss", period)
        apprenti = household.members("enfant_apprenti_cnss", period)
        superieur = household.members("enfant_etudes_superieures_cnss", period)
        handicape = household.members("enfant_handicape_cnss", period)
        sans_revenu = household.members("enfant_handicape_sans_revenu_cnss", period)
        is_child = household.members_role == Household.CHILD
        # A child born during the month is entitled for that month, even though
        # `age` (computed at the period start) is still negative.
        alive = birth <= datetime64(str(period.stop))
        eligible = alive & (
            (age < 12)
            | ((age >= 12) & (age < 21) & (scolarise | superieur))
            | ((age >= 12) & (age < 18) & apprenti)
            | (handicape & sans_revenu)
        )
        return household.sum(eligible & is_child)


class allocations_familiales(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Montant mensuel des allocations familiales CNSS servies au ménage"
    reference = "https://www.cnss.ma/fr/assure/salarie/prestations-sociales/allocations-familiales"  # Dahir 1-72-184, arts. 40-41 ; Décret 2-08-358

    def formula(household, period, parameters):
        """Calcule les allocations familiales mensuelles de la CNSS selon le barème réglementaire.

        Barème fixé par le Décret n° 2-08-358, modifié par les décrets
        n° 2-19-750 et n° 2-23-715 :
        - Rangs 1 à 3 : 300 MAD / mois par enfant
        - Rangs 4 à 6 : 36 MAD / mois de 2019-07 à 2022-12, 100 MAD / mois
          depuis 2023-01-01 (effet rétroactif du décret 2-23-715)
        - Au-delà du 6ème enfant : 0 MAD (plafond légal de 6 enfants)
        """
        params = parameters(period).prestations_sociales.allocations_familiales.cnss
        nb_enfants = household("nombre_enfants", period)

        plafond = params.plafond_enfants
        montant_t1 = params.montant_enfants_1_a_3
        montant_t2 = params.montant_enfants_4_a_6

        enfants_eligibles = clip(nb_enfants, 0, plafond)
        enfants_t1 = clip(enfants_eligibles, 0, 3)
        enfants_t2 = clip(enfants_eligibles - 3, 0, 3)

        return (enfants_t1 * montant_t1) + (enfants_t2 * montant_t2)
