"""Prime exceptionnelle de l'ASD après une déclaration à la CNSS.

Sources : Loi n° 41-26 du 9 Muharram 1448 (25 juin 2026), BO n° 7523 du
6 juillet 2026, qui insère les articles 16 bis et 16 bis bis dans la Loi
n° 58-23 ; Décret n° 2-26-434 du 8 Safar 1448 (23 juillet 2026), BO n° 7530 du
30 juillet 2026, qui fixe la durée maximale à douze mois. La loi entre en
vigueur à la publication du texte réglementaire d'application (article 3),
soit le 30 juillet 2026.

La prime est versée aux ménages qui percevaient l'ASD et ont perdu ce droit
parce que le chef de ménage ou l'un des conjoints a été déclaré au régime de
sécurité sociale du secteur privé. Son montant est égal aux aides que le ménage
aurait pu percevoir ; elle est accordée une seule fois, pour douze mois au
maximum, continus ou non, décomptés à partir de la date de déclaration.

Le modèle ne décide ni de la déclaration CNSS ni de la perte de droit : le
montant de référence et les mois restants sont des entrées. Il ne consomme pas
les mois et n'impose pas le caractère unique de la prime : l'appelant doit
décrémenter `mois_restants_prime_exceptionnelle` et ne pas réinitialiser le
compteur. Une valeur supérieure à douze est refusée ; une valeur décimale est
tronquée par le type entier (12,9 devient 12). La durée maximale est un
paramètre nul avant l'entrée en vigueur, ce qui rend la prime nulle avant le
30 juillet 2026.
"""

from numpy import maximum, where
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household


class montant_asd_avant_perte(Variable):
    """Montant mensuel d'ASD que le ménage aurait pu percevoir avant la perte."""

    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Montant d'ASD de référence que le ménage aurait pu percevoir"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Loi 58-23, art. 16 bis
    )


class mois_restants_prime_exceptionnelle(Variable):
    """Mois de prime encore disponibles dans la limite de douze mois.

    Valeur fournie par l'utilisateur : le modèle ne décompte pas les mois
    consommés et n'impose pas le caractère unique de la prime. Une valeur
    supérieure à douze est refusée et ne donne droit à rien ; une valeur
    décimale est tronquée par le type entier (12,9 devient 12).
    """

    value_type = int
    entity = Household
    definition_period = MONTH
    default_value = 0
    label = "Mois restants de prime exceptionnelle (0 à 12)"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Décret 2-26-434, art. 10 bis
    )


class prime_exceptionnelle_asd(Variable):
    """Prime exceptionnelle mensuelle, versée dans la limite de douze mois."""

    value_type = float
    entity = Household
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Prime exceptionnelle ASD du mois"
    reference = (
        "https://www.anss.gov.ma/fr/typologies-d-aides"  # Loi 58-23, art. 16 bis
    )

    def formula(household, period, parameters):
        params = parameters(
            period
        ).prestations_sociales.aide_sociale_directe.prime_exceptionnelle
        remaining = household("mois_restants_prime_exceptionnelle", period)
        reference_amount = household("montant_asd_avant_perte", period)
        in_window = (remaining > 0) & (remaining <= params.mois_max)
        return where(in_window, maximum(reference_amount, 0.0), 0.0)
