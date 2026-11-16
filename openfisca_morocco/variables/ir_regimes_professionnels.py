"""Régimes professionnels de l'IR : net simplifié, CPU et auto-entrepreneur.

Sources : Code Général des Impôts (édition 2026), articles 12, 32 à 44 et
73-II-B-6° / 73-III. Les taux et coefficients sont paramétrés dans
`parameters/impot_revenu/regimes_professionnels.yaml`.

Le régime du résultat net réel reste le régime par défaut : le revenu net est
fourni par l'entrée `revenu_professionnel_net`. Le régime simplifié applique
l'abattement de 15 % des adhérents des centres de gestion. La contribution
professionnelle unique et le régime de l'auto-entrepreneur sont des impôts
libératoires calculés sur le chiffre d'affaires ; ils ne s'ajoutent pas au
revenu global imposable.
"""

from numpy import maximum as max_, where
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person


class RegimeProfessionnel(Enum):
    net_reel = "Résultat net réel"
    net_simplifie = "Résultat net simplifié"
    cpu = "Contribution professionnelle unique"
    auto_entrepreneur = "Auto-entrepreneur"


class CategorieProfessionnelle(Enum):
    """Catégories de l'article 40-I, dans l'ordre du tableau."""

    alimentation_generale = "Commerce — alimentation générale"
    autres_produits_alimentaires = "Commerce — autres produits alimentaires"
    matieres_premieres = "Commerce — matières premières"
    materiaux_construction = "Commerce — matériaux de construction"
    produits_chimiques = "Commerce — produits chimiques et engrais"
    autres_produits_non_alimentaires = "Commerce — autres produits non alimentaires"
    restauration_rapide = "Services — restauration légère ou rapide"
    restaurant_debit_boissons = "Services — restaurant et débit de boissons"
    transport = "Services — transport de personnes et de marchandises"
    entretien = "Services — activités d'entretien"
    location_biens_meubles = "Services — location de biens meubles"
    autres_locations_gestion = "Services — autres locations et gestion"
    coiffure_esthetique = "Services — coiffure et esthétique"
    metiers_techniques = (
        "Services — mécanicien, réparateur électronique, activités artistiques, moulin"
    )
    autres_artisans_services = "Services — autres artisans de services"
    courtiers = "Services — courtiers"
    autres_prestations = "Services — autres prestations"
    fabrication_alimentaire = "Fabrication — produits alimentaires"
    fabrication_non_alimentaire = "Fabrication — produits non alimentaires"
    chevillard = "Commerces spécifiques — chevillard"
    marchand_tabac = "Commerces spécifiques — marchand de tabac"
    marchand_gaz = "Commerces spécifiques — marchand de gaz"
    marchand_farine = "Commerces spécifiques — marchand de farine"
    armateur_peche = "Commerces spécifiques — armateur ou fermier de pêche"
    boulanger = "Commerces spécifiques — boulanger"


SERVICES = {
    CategorieProfessionnelle.restauration_rapide,
    CategorieProfessionnelle.restaurant_debit_boissons,
    CategorieProfessionnelle.transport,
    CategorieProfessionnelle.entretien,
    CategorieProfessionnelle.location_biens_meubles,
    CategorieProfessionnelle.autres_locations_gestion,
    CategorieProfessionnelle.coiffure_esthetique,
    CategorieProfessionnelle.metiers_techniques,
    CategorieProfessionnelle.autres_artisans_services,
    CategorieProfessionnelle.courtiers,
    CategorieProfessionnelle.autres_prestations,
}


class NatureActivite(Enum):
    commercial = "Activité commerciale, industrielle ou artisanale"
    services = "Prestation de services"


class regime_professionnel(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = RegimeProfessionnel
    default_value = RegimeProfessionnel.net_reel
    label = "Régime de détermination du revenu professionnel"
    reference = "https://maloi.ma/fr/law/code-impots/article/32"


class categorie_professionnelle(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = CategorieProfessionnelle
    default_value = CategorieProfessionnelle.autres_prestations
    label = "Catégorie de professions pour la contribution professionnelle unique"
    reference = "https://maloi.ma/fr/law/code-impots/article/40"


class nature_activite_professionnelle(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = NatureActivite
    default_value = NatureActivite.commercial
    label = "Nature de l'activité professionnelle (commerciale ou de services)"
    reference = "https://maloi.ma/fr/law/code-impots/article/41"


class chiffre_affaires_professionnel(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Chiffre d'affaires annuel du régime professionnel"
    reference = "https://maloi.ma/fr/law/code-impots/article/40"


class adherent_centre_gestion(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "Adhérent d'un centre de gestion de comptabilité agréé"
    reference = "https://maloi.ma/fr/law/code-impots/article/38"


class deficit_professionnel_reportable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Déficit professionnel antérieur reportable"
    reference = "https://maloi.ma/fr/law/code-impots/article/12"

    # Entrée : l'appelant ne fournit que les déficits des quatre exercices
    # précédents (article 12) ; le modèle ne conserve pas l'historique.


class revenu_professionnel_imposable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenu professionnel imposable après report déficitaire et abattement"
    reference = "https://maloi.ma/fr/law/code-impots/article/37"

    def formula(person, period, parameters):
        regime = person("regime_professionnel", period)
        net = person("revenu_professionnel_net", period)
        deficit = person("deficit_professionnel_reportable", period)
        base = max_(net - max_(deficit, 0), 0)
        if period.start.year < 2026:
            if (regime != RegimeProfessionnel.net_reel).any():
                raise ValueError(
                    "The simplified, CPU and auto-entrepreneur regimes are only "
                    "modelled from 2026."
                )
            return base
        abattement = parameters(
            period
        ).impot_revenu.regimes_professionnels.net_simplifie.abattement_centre_gestion
        adherent = person("adherent_centre_gestion", period)
        simplifie = base * (1 - abattement * adherent)
        return where(
            regime == RegimeProfessionnel.net_reel,
            base,
            where(
                regime == RegimeProfessionnel.net_simplifie,
                simplifie,
                0.0,
            ),
        )


def _droits_complementaires(droits, params):
    """Droits complémentaires annuels de l'article 73-II-B-6°."""
    table = params.cpu.droits_complementaires
    complement = table.montant_8
    for seuil, montant in (
        (table.seuil_7, table.montant_7),
        (table.seuil_6, table.montant_6),
        (table.seuil_5, table.montant_5),
        (table.seuil_4, table.montant_4),
        (table.seuil_3, table.montant_3),
        (table.seuil_2, table.montant_2),
    ):
        complement = where(droits <= seuil, montant, complement)
    return where(droits < table.seuil_1, table.montant_1, complement)


class impot_contribution_professionnelle_unique(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Contribution professionnelle unique (libératoire)"
    reference = "https://maloi.ma/fr/law/code-impots/article/40"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            if (person("chiffre_affaires_professionnel", period) != 0).any():
                raise ValueError("Professional regimes are only modelled from 2026.")
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.regimes_professionnels
        regime = person("regime_professionnel", period)
        concerne = regime == RegimeProfessionnel.cpu

        coefficient = person.filled_array(0.0)
        categorie = person("categorie_professionnelle", period)
        for value in CategorieProfessionnelle:
            coefficient += where(
                categorie == value,
                getattr(params.cpu.coefficients, value.name),
                0.0,
            )

        # La nature de l'activité se déduit de la catégorie de l'article 40-I :
        # les onze catégories de services relèvent du plafond de 500 000 DH,
        # les activités commerciales, industrielles et artisanales de 2 M DH.
        est_service = categorie == CategorieProfessionnelle.restauration_rapide
        for value in SERVICES:
            est_service = est_service | (categorie == value)
        chiffre_affaires = max_(person("chiffre_affaires_professionnel", period), 0)
        seuil = where(
            est_service, params.cpu.seuil_services, params.cpu.seuil_commercial
        )
        assiette = chiffre_affaires * coefficient
        droits = assiette * params.cpu.taux
        total = droits + _droits_complementaires(droits, params)
        return where(concerne & (chiffre_affaires <= seuil), total, 0.0)


class impot_auto_entrepreneur(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt libératoire de l'auto-entrepreneur"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"

    def formula(person, period, parameters):
        if period.start.year < 2026:
            if (person("chiffre_affaires_professionnel", period) != 0).any():
                raise ValueError("Professional regimes are only modelled from 2026.")
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.regimes_professionnels
        regime = person("regime_professionnel", period)
        activite = person("nature_activite_professionnelle", period)
        chiffre_affaires = max_(person("chiffre_affaires_professionnel", period), 0)

        commercial = activite == NatureActivite.commercial
        taux = where(
            commercial,
            params.auto_entrepreneur.taux_commercial,
            params.auto_entrepreneur.taux_services,
        )
        seuil = where(
            commercial,
            params.auto_entrepreneur.seuil_commercial,
            params.auto_entrepreneur.seuil_services,
        )
        dans_le_regime = (regime == RegimeProfessionnel.auto_entrepreneur) & (
            chiffre_affaires <= seuil
        )
        droits = chiffre_affaires * taux
        total = droits + _droits_complementaires(droits, params)
        return where(dans_le_regime, total, 0.0)


class impot_regimes_professionnels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôts libératoires des régimes professionnels (CPU et auto-entrepreneur)"
    reference = "https://maloi.ma/fr/law/code-impots/article/73"

    def formula(person, period, parameters):
        return person("impot_contribution_professionnelle_unique", period) + person(
            "impot_auto_entrepreneur", period
        )
