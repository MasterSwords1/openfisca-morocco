"""Droits d'enregistrement et droits de conservation foncière.

Sources : Code Général des Impôts (édition 2026), articles 127 à 155, Loi de
finances n° 73-16 pour 2017 (BO n° 6577 bis) et Décret n° 2-16-375
(BO n° 6484 du 21 juillet 2016).

Taux d'enregistrement :

- locaux construits (habitation, commercial, professionnel, administratif) :
  4 % (art. 133-I-F-1°) ;
- terrains nus ou constructions destinées à être démolies : 5 %
  (art. 133-I-G-1°) ;
- fonds de commerce : 6 % (art. 133-I-A-1°) ;
- apports non exonérés en capital : 0,5 % (art. 133-I-H), avec un droit fixe
  de 1 000 DH lorsque le capital souscrit n'excède pas 500 000 DH
  (art. 135-I-1°). Les apports en numéraire purs et simples sont exonérés
  (art. 129-IV-23°).

Les droits proportionnels ont un minimum de perception de 100 DH
(art. 133-II), et un supplément de 2 % s'applique au prix supérieur à
300 000 DH qui n'est pas acquitté par un moyen traçable (art. 133-III).

Conservation foncière (Décret n° 2-16-375, chapitre II-A) : 1,5 % ad valorem
+ 100 DH de droit fixe, avec un minimum de perception de 500 DH. Le certificat
de propriété (100 DH, chapitre IV-H-1) est une formalité distincte et
optionnelle, exposée par `demande_certificat_propriete`.

Le type d'acquisition n'a pas de valeur par défaut : sans `type_acquisition`,
aucun droit n'est calculé. Les taux sont encodés à partir de 2026 ; une simulation antérieure qui fournit
l'un des inputs du droit concerné (valeur, type, moyen de paiement ou certificat
pour l'acquisition ; apport pour la constitution) lève une erreur.
"""

from numpy import maximum as max_, where
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Company, Household

BO_2017 = "https://www.sgg.gov.ma/BO/bo_fr/2017/BO_6577-bis_Fr.pdf"
BO_6484 = "https://www.sgg.gov.ma/BO/bo_fr/2016/BO_6484_Fr.pdf"


class TypeAcquisition(Enum):
    non_renseigne = "Non renseigné"
    immeuble_bati = "Local construit"
    terrain_nu = "Terrain nu ou construction à démolir"
    fonds_commerce = "Fonds de commerce"


def _taux(nature, params):
    return where(
        nature == TypeAcquisition.immeuble_bati,
        params.immeuble_bati,
        where(
            nature == TypeAcquisition.terrain_nu,
            params.terrain_nu,
            where(
                nature == TypeAcquisition.fonds_commerce,
                params.fonds_commerce,
                0.0,
            ),
        ),
    )


def _droits_enregistrement(nature, valeur, tracable, params):
    taux = _taux(nature, params)
    droits = where(
        (nature == TypeAcquisition.non_renseigne) | (valeur <= 0),
        0.0,
        max_(valeur * taux, params.minimum_proportionnel),
    )
    supplement = where(
        (~tracable) & (valeur > params.seuil_non_tracable),
        valeur * params.supplement_non_tracable,
        0.0,
    )
    return droits + where(droits > 0, supplement, 0.0)


def _conservation(nature, valeur, certificat, params):
    inscription = max_(valeur * params.taux + params.droit_fixe, params.minimum)
    return where(
        (nature == TypeAcquisition.non_renseigne)
        | (nature == TypeAcquisition.fonds_commerce)
        | (valeur <= 0),
        0.0,
        inscription + where(certificat, params.certificat, 0.0),
    )


class type_acquisition_immobiliere(Variable):
    value_type = Enum
    entity = Household
    definition_period = YEAR
    possible_values = TypeAcquisition
    default_value = TypeAcquisition.non_renseigne
    label = "Nature du bien acquis par le ménage"
    reference = BO_2017


class valeur_bien_acquis(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Valeur d'acquisition du bien"
    reference = BO_2017


class paiement_par_moyen_tracable(Variable):
    value_type = bool
    entity = Household
    definition_period = YEAR
    default_value = True
    label = "Prix acquitté par un moyen de paiement traçable"
    reference = BO_2017


class demande_certificat_propriete(Variable):
    value_type = bool
    entity = Household
    definition_period = YEAR
    default_value = False
    label = "Demande d'un certificat de propriété"
    reference = BO_6484


class droits_enregistrement(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits d'enregistrement dus par le ménage"
    reference = BO_2017

    def formula(household, period, parameters):
        if period.start.year < 2026:
            provided = (
                (household("valeur_bien_acquis", period) != 0)
                | (
                    household("type_acquisition_immobiliere", period)
                    != TypeAcquisition.non_renseigne
                )
                | ~household("paiement_par_moyen_tracable", period)
                | household("demande_certificat_propriete", period)
            )
            if provided.any():
                raise ValueError("Registration duties are only modelled from 2026.")
            return household.filled_array(0.0)
        params = parameters(period).enregistrement.droits.enregistrement
        return _droits_enregistrement(
            household("type_acquisition_immobiliere", period),
            max_(household("valeur_bien_acquis", period), 0),
            household("paiement_par_moyen_tracable", period),
            params,
        )


class frais_conservation_fonciere(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits de conservation foncière dus par le ménage"
    reference = BO_6484

    def formula(household, period, parameters):
        if period.start.year < 2026:
            provided = (
                (household("valeur_bien_acquis", period) != 0)
                | (
                    household("type_acquisition_immobiliere", period)
                    != TypeAcquisition.non_renseigne
                )
                | ~household("paiement_par_moyen_tracable", period)
                | household("demande_certificat_propriete", period)
            )
            if provided.any():
                raise ValueError("Conservation fees are only modelled from 2026.")
            return household.filled_array(0.0)
        params = parameters(period).enregistrement.droits.conservation_fonciere
        return _conservation(
            household("type_acquisition_immobiliere", period),
            max_(household("valeur_bien_acquis", period), 0),
            household("demande_certificat_propriete", period),
            params,
        )


class frais_acquisition_immobiliere_totaux(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Total des droits et frais d'acquisition immobilière du ménage"
    reference = BO_2017

    def formula(household, period, parameters):
        return household("droits_enregistrement", period) + household(
            "frais_conservation_fonciere", period
        )


class type_acquisition_immobiliere_societe(Variable):
    value_type = Enum
    entity = Company
    definition_period = YEAR
    possible_values = TypeAcquisition
    default_value = TypeAcquisition.non_renseigne
    label = "Nature du bien acquis par la société"
    reference = BO_2017


class valeur_bien_acquis_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Valeur d'acquisition du bien par la société"
    reference = BO_2017


class paiement_par_moyen_tracable_societe(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = True
    label = "Prix acquitté par la société au moyen d'un paiement traçable"
    reference = BO_2017


class demande_certificat_propriete_societe(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = False
    label = "Demande d'un certificat de propriété par la société"
    reference = BO_6484


class droits_enregistrement_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits d'enregistrement dus par la société"
    reference = BO_2017

    def formula(company, period, parameters):
        if period.start.year < 2026:
            provided = (
                (company("valeur_bien_acquis_societe", period) != 0)
                | (
                    company("type_acquisition_immobiliere_societe", period)
                    != TypeAcquisition.non_renseigne
                )
                | ~company("paiement_par_moyen_tracable_societe", period)
                | company("demande_certificat_propriete_societe", period)
            )
            if provided.any():
                raise ValueError("Registration duties are only modelled from 2026.")
            return company.filled_array(0.0)
        params = parameters(period).enregistrement.droits.enregistrement
        return _droits_enregistrement(
            company("type_acquisition_immobiliere_societe", period),
            max_(company("valeur_bien_acquis_societe", period), 0),
            company("paiement_par_moyen_tracable_societe", period),
            params,
        )


class frais_conservation_fonciere_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits de conservation foncière dus par la société"
    reference = BO_6484

    def formula(company, period, parameters):
        if period.start.year < 2026:
            provided = (
                (company("valeur_bien_acquis_societe", period) != 0)
                | (
                    company("type_acquisition_immobiliere_societe", period)
                    != TypeAcquisition.non_renseigne
                )
                | ~company("paiement_par_moyen_tracable_societe", period)
                | company("demande_certificat_propriete_societe", period)
            )
            if provided.any():
                raise ValueError("Conservation fees are only modelled from 2026.")
            return company.filled_array(0.0)
        params = parameters(period).enregistrement.droits.conservation_fonciere
        return _conservation(
            company("type_acquisition_immobiliere_societe", period),
            max_(company("valeur_bien_acquis_societe", period), 0),
            company("demande_certificat_propriete_societe", period),
            params,
        )


class frais_acquisition_immobiliere_totaux_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Total des droits et frais d'acquisition immobilière de la société"
    reference = BO_2017

    def formula(company, period, parameters):
        return company("droits_enregistrement_societe", period) + company(
            "frais_conservation_fonciere_societe", period
        )


class apport_capital_numeraires(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Apports en numéraire purs et simples, exonérés (art. 129-IV-23°)"
    reference = BO_2017


class apport_capital_non_exonere(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Apports non exonérés lors d'une constitution ou augmentation de capital"
    reference = BO_2017


class droits_enregistrement_constitution_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits sur les apports non exonérés en capital"
    reference = BO_2017

    def formula(company, period, parameters):
        if period.start.year < 2026:
            provided = (company("apport_capital_non_exonere", period) != 0) | (
                company("apport_capital_numeraires", period) != 0
            )
            if provided.any():
                raise ValueError("Registration duties are only modelled from 2026.")
            return company.filled_array(0.0)
        params = parameters(period).enregistrement.droits.enregistrement
        apport = max_(company("apport_capital_non_exonere", period), 0)
        return where(
            apport <= 0,
            0.0,
            where(
                apport <= params.seuil_droit_fixe_constitution,
                params.droit_fixe_constitution,
                apport * params.constitution_societe,
            ),
        )
