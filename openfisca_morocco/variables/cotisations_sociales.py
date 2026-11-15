"""Cotisations sociales obligatoires (CNSS, AMO) et charges patronales.

Pipeline encodé à partir du corpus `morocco-holy-graph` (module `ma_social_protection`, CSOC)
et des textes législatifs et réglementaires suivants :
- Dahir portant loi n° 1-72-184 du 27 juillet 1972 relatif au régime de sécurité sociale
  (prestations familiales, court terme, long terme)
- Décret n° 2-02-175 du 11 juillet 2002 fixant le plafond des rémunérations soumises
  à cotisation CNSS à 6 000 DH par mois
- Loi n° 03-14 et Décret n° 2-14-540 relatifs à l'indemnité pour perte d'emploi (IPE)
- Loi n° 30-97 relative à la taxe de formation professionnelle (TFP, 1,60 % patronale)
- Loi n° 65-00 portant Code de la Couverture Médicale de Base (articles 114 et suivants)
- Décret n° 2-05-734 modifié par Décret n° 2-14-707 (AMO 4,52 % répartie à parts égales,
  plus participation patronale de solidarité AMO de 1,85 %)

Toutes les cotisations sociales sont calculées pour des périodes MENSUELLES (MONTH),
conformément à la périodicité de paie et de déclaration légale au Maroc.
"""

from numpy import minimum as min_
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person


class salaire_brut(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Rémunération brute mensuelle soumise à cotisations sociales"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"  # Dahir 1-72-184, art. 19


class cotisation_cnss_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = (
        "Cotisation CNSS salariale mensuelle plafonnée (court terme, long terme, IPE)"
    )
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"  # Dahir 1-72-184, art. 19 ; Décret 2-02-175 ; Loi 03-14

    def formula(person, period, parameters):
        base = person("salaire_brut", period)
        plafond = parameters(
            period
        ).prestations_sociales.cotisations.cnss.plafond_mensuel
        base_plafonnee = min_(base, plafond)
        taux = (
            parameters(period).prestations_sociales.cotisations.cnss.court_terme.salarie
            + parameters(
                period
            ).prestations_sociales.cotisations.cnss.long_terme.salarie
            + parameters(
                period
            ).prestations_sociales.cotisations.cnss.indemnite_perte_emploi.salarie
        )
        return base_plafonnee * taux


class cotisation_amo_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Cotisation AMO salariale mensuelle sans plafond"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"  # Loi 65-00, art. 114 ; Décret 2-05-734 mod. 2-14-707

    def formula(person, period, parameters):
        base = person("salaire_brut", period)
        taux = parameters(period).prestations_sociales.cotisations.amo.base.salarie
        return base * taux


class cotisations_sociales_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Total des cotisations sociales salariales mensuelles (CNSS + AMO)"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"

    def formula(person, period, parameters):
        return person("cotisation_cnss_salarie", period) + person(
            "cotisation_amo_salarie", period
        )


class cotisation_cnss_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Cotisation CNSS patronale mensuelle (prestations familiales, court et long terme, TFP, IPE)"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"  # Dahir 1-72-184 ; Décret 2-02-175 ; Décret 2-19-461 ; Loi 30-97 ; Loi 03-14

    def formula(person, period, parameters):
        base = person("salaire_brut", period)
        plafond = parameters(
            period
        ).prestations_sociales.cotisations.cnss.plafond_mensuel
        base_plafonnee = min_(base, plafond)
        taux_plafonne = (
            parameters(
                period
            ).prestations_sociales.cotisations.cnss.court_terme.employeur
            + parameters(
                period
            ).prestations_sociales.cotisations.cnss.long_terme.employeur
            + parameters(
                period
            ).prestations_sociales.cotisations.cnss.indemnite_perte_emploi.employeur
        )
        taux_deplafonne = (
            parameters(
                period
            ).prestations_sociales.cotisations.cnss.prestations_familiales.employeur
            + parameters(
                period
            ).prestations_sociales.cotisations.cnss.taxe_formation_professionnelle.employeur
        )
        return base_plafonnee * taux_plafonne + base * taux_deplafonne


class cotisation_amo_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Cotisation AMO patronale mensuelle sans plafond (base + solidarité)"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"  # Loi 65-00 ; Décret 2-05-734 mod. 2-14-707

    def formula(person, period, parameters):
        base = person("salaire_brut", period)
        taux = (
            parameters(period).prestations_sociales.cotisations.amo.base.employeur
            + parameters(
                period
            ).prestations_sociales.cotisations.amo.solidarite.employeur
        )
        return base * taux


class cotisations_sociales_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Total des cotisations et contributions sociales patronales mensuelles"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"

    def formula(person, period, parameters):
        return person("cotisation_cnss_employeur", period) + person(
            "cotisation_amo_employeur", period
        )


class cout_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    unit = "currency-MAD"
    label = "Coût global employeur mensuel (salaire brut + cotisations patronales)"
    reference = "https://github.com/MasterSwords1/morocco-holy-graph/blob/master/laws/ma_social_protection/data/social_security_rates.json"

    def formula(person, period, parameters):
        return person("salaire_brut", period) + person(
            "cotisations_sociales_employeur", period
        )
