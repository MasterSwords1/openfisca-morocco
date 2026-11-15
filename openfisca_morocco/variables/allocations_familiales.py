"""Prestations sociales — Allocations familiales (CNSS).

Modélisation du régime des allocations familiales servies par la Caisse Nationale
de Sécurité Sociale (CNSS) aux assurés sociaux ayant des enfants à charge.

Cadre législatif et réglementaire :
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 relatif au régime de sécurité sociale
  (articles 38 à 41)
- Décret n° 2-19-461 du 19 juillet 2019 fixant le barème des allocations familiales :
  * 300 DH par mois pour chacun des 3 premiers enfants (rangs 1 à 3)
  * 36 DH par mois pour chacun des 3 enfants suivants (rangs 4 à 6)
  * Plafond légal de 6 enfants par assuré social

Entités :
- `nombre_enfants` : Nombre d'enfants à charge (Household, entier, MONTH)
- `allocations_familiales` : Montant mensuel servi au ménage (Household, float, MONTH)
"""

from numpy import clip
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household


class nombre_enfants(Variable):
    value_type = int
    entity = Household
    definition_period = MONTH
    label = (
        "Nombre d'enfants à charge ouvrant droit aux allocations familiales au sein du ménage"
    )
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/family_allowances_grid.json"  # Dahir 1-72-184, art. 38 et 41

    def formula(household, period, parameters):
        """Calcule le nombre d'enfants à charge à partir du rôle CHILD dans le ménage."""
        return household.nb_persons(Household.CHILD)


class allocations_familiales(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "Montant mensuel des allocations familiales CNSS servies au ménage"
    )
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/family_allowances_grid.json"  # Dahir 1-72-184, arts. 38-41 ; Décret 2-19-461

    def formula(household, period, parameters):
        """Calcule les allocations familiales mensuelles de la CNSS selon le barème réglementaire.

        Barème fixé par le Décret n° 2-19-461 :
        - Rangs 1 à 3 : 300 MAD / mois par enfant
        - Rangs 4 à 6 : 36 MAD / mois par enfant
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
