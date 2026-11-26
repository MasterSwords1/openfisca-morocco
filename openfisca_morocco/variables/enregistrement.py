"""Droits d'enregistrement et droits de conservation foncière.

Sources : Code Général des Impôts (édition 2026), articles 127 à 155 ; lois de
finances n° 38-07 pour 2008 (6 %, BO n° 5591 bis), n° 22-12 pour 2012 (4 %,
BO n° 6048), n° 73-16 pour 2017 (5 %, BO n° 6577 bis), n° 115-12 pour 2013
(droit fixe de 1 000 DH et seuil de 500 000 DH, BO n° 6113 bis), n° 65-20 pour
2021 (0,5 %, BO n° 6944 bis) et n° 50-25 pour 2026 (supplément de 2 %,
BO n° 7465 bis) ; Décret n° 2-16-375 (BO n° 6484) pour la conservation
foncière.

Taux d'enregistrement :

- locaux construits (habitation, commercial, professionnel, administratif) :
  4 % (art. 133-I-F-1°) ;
- terrains nus ou constructions destinées à être démolies : 5 %
  (art. 133-I-G-1°) ;
- fonds de commerce : 6 % (art. 133-I-A-1°) ;
- apports non exonérés en capital : 0,5 % (art. 133-I-H), avec un droit fixe
  de 1 000 DH lorsque le capital souscrit total n'excède pas 500 000 DH
  (art. 135-I-1°). Les apports en numéraire purs et simples sont exonérés
  (art. 129-IV-23°).

Les droits proportionnels ont un minimum de perception de 100 DH
(art. 133-II), et un supplément de 2 % s'applique, pour les actes à compter du
1er juillet 2026, au prix non acquitté par un moyen traçable (art. 133-III).
Pour les immeubles, seul le prix supérieur à 300 000 DH est concerné ; le fonds
de commerce n'a pas de seuil.

Conservation foncière (Décret n° 2-16-375, chapitre II-A) : 1,5 % ad valorem
+ 100 DH de droit fixe, avec un minimum de perception de 500 DH. Le certificat
de propriété (100 DH, chapitre IV-H-1) est une formalité distincte et
optionnelle, exposée par `demande_certificat_propriete`.

Le type d'acquisition n'a pas de valeur par défaut : sans `type_acquisition`,
aucun droit n'est calculé. Les taux sont encodés à partir de 2026 ; une simulation antérieure qui fournit
l'un des inputs du droit concerné (valeur, type, moyen de paiement ou certificat
pour l'acquisition ; apport pour la constitution) lève une erreur.
"""

from datetime import date

from numpy import datetime64, maximum as max_, where
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import ETERNITY, YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Company, Household

BO_CGI = "https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5487-bis_fr.pdf"
BO_50_25 = "https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_fr.pdf"
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


def _droits_enregistrement(nature, valeur, tracable, date_acte, params):
    taux = _taux(nature, params)
    droits = where(
        (nature == TypeAcquisition.non_renseigne) | (valeur <= 0),
        0.0,
        max_(valeur * taux, params.minimum_proportionnel),
    )
    # The 2 % surcharge applies to acts from 1 July 2026. The 300,000 DH
    # threshold concerns immovable property; a fonds de commerce is liable
    # from the first dirham.
    seuil_applicable = (nature == TypeAcquisition.fonds_commerce) | (
        valeur > params.seuil_non_tracable
    )
    supplement = where(
        (~tracable) & (date_acte >= datetime64("2026-07-01")) & seuil_applicable,
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


class date_acte_enregistrement(Variable):
    value_type = date
    entity = Household
    definition_period = ETERNITY
    default_value = date(2026, 7, 1)
    label = "Date de l'acte d'acquisition (pour le supplément de 2 % à compter du 1er juillet 2026)"
    reference = BO_50_25


class type_acquisition_immobiliere(Variable):
    value_type = Enum
    entity = Household
    definition_period = YEAR
    possible_values = TypeAcquisition
    default_value = TypeAcquisition.non_renseigne
    label = "Nature du bien acquis par le ménage"
    reference = BO_CGI


class valeur_bien_acquis(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Valeur d'acquisition du bien"
    reference = BO_CGI


class paiement_par_moyen_tracable(Variable):
    value_type = bool
    entity = Household
    definition_period = YEAR
    default_value = True
    label = "Prix acquitté par un moyen de paiement traçable"
    reference = BO_CGI


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
    reference = BO_CGI

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
            household("date_acte_enregistrement", period),
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
    reference = BO_CGI

    def formula(household, period, parameters):
        return household("droits_enregistrement", period) + household(
            "frais_conservation_fonciere", period
        )


class date_acte_enregistrement_societe(Variable):
    value_type = date
    entity = Company
    definition_period = ETERNITY
    default_value = date(2026, 7, 1)
    label = "Date de l'acte d'acquisition de la société (supplément de 2 % à compter du 1er juillet 2026)"
    reference = BO_50_25


class type_acquisition_immobiliere_societe(Variable):
    value_type = Enum
    entity = Company
    definition_period = YEAR
    possible_values = TypeAcquisition
    default_value = TypeAcquisition.non_renseigne
    label = "Nature du bien acquis par la société"
    reference = BO_CGI


class valeur_bien_acquis_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Valeur d'acquisition du bien par la société"
    reference = BO_CGI


class paiement_par_moyen_tracable_societe(Variable):
    value_type = bool
    entity = Company
    definition_period = YEAR
    default_value = True
    label = "Prix acquitté par la société au moyen d'un paiement traçable"
    reference = BO_CGI


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
    reference = BO_CGI

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
            company("date_acte_enregistrement_societe", period),
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
    reference = BO_CGI

    def formula(company, period, parameters):
        return company("droits_enregistrement_societe", period) + company(
            "frais_conservation_fonciere_societe", period
        )


class apport_capital_numeraires(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Apports en numéraire purs et simples, exonérés (art. 129-IV-23°) ; "
        "exclus de l'assiette, mais inclus dans le capital souscrit total du "
        "seuil de 500 000 DH"
    )
    reference = BO_CGI


class apport_capital_non_exonere(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Apports non exonérés lors d'une constitution ou augmentation de capital"
    reference = BO_CGI


class apport_capital_total(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Capital souscrit total (apports en numéraire et apports non exonérés)"
    reference = BO_CGI

    def formula(company, period, parameters):
        return max_(company("apport_capital_numeraires", period), 0) + max_(
            company("apport_capital_non_exonere", period), 0
        )


class droits_enregistrement_constitution_societe(Variable):
    value_type = float
    entity = Company
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Droits sur les apports non exonérés en capital"
    reference = BO_CGI

    def formula(company, period, parameters):
        if period.start.year < 2026:
            provided = (company("apport_capital_non_exonere", period) != 0) | (
                company("apport_capital_numeraires", period) != 0
            )
            if provided.any():
                raise ValueError("Registration duties are only modelled from 2026.")
            return company.filled_array(0.0)
        params = parameters(period).enregistrement.droits.enregistrement
        total = company("apport_capital_total", period)
        taxable = max_(company("apport_capital_non_exonere", period), 0)
        # Art. 135-I-1° reads "le capital social souscrit au titre dudit
        # apport" ; DGI circular 721 clarifies that the 500,000 DH is the
        # amount of the capital increase, not the post-increase share capital.
        # The total includes cash apports, while only the non-exempt apport is
        # taxable. The 1,000 DH
        # fixed duty applies when that total does not exceed 500,000 DH. Above
        # it, the 0.5 % duty applies to the non-exempt apport, with the 1,000 DH
        # capital minimum of art. 133-II.
        return where(
            (total <= 0) | (taxable <= 0),
            0.0,
            where(
                total <= params.seuil_droit_fixe_constitution,
                params.droit_fixe_constitution,
                max_(
                    taxable * params.constitution_societe,
                    params.minimum_constitution,
                ),
            ),
        )
