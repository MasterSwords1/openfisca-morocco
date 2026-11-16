"""Impôt sur le revenu (IR) — revenus salariaux et assimilés.

Pipeline encoded from the Code Général des Impôts (Loi n° 43-06), as reformed
by the Loi de Finances 2025:

- article 56: salarial income subject to the IR
- article 59: forfaitary professional-expense deduction (35 % up to 78 000 DH of
  gross annual pay, 25 % above, both capped at 35 000 DH)
- article 73-I: progressive annual scale on net taxable income
- article 74: 600 DH deduction per dependent from 2026 (500 in 2025),
  capped at 6 dependents

Salary and exempt remuneration inputs are monthly amounts. Annual totals can
still be supplied and are divided between months by OpenFisca. The taxable
income pipeline, contribution deduction and family-dependent count remain
annual: the CGI scale is applied once to the year's income, not month by month.
Monthly withholding is not modelled.
"""

from numpy import float64, maximum as max_, minimum as min_, sum as sum_, where
from openfisca_core.holders import set_input_divide_by_period
from openfisca_core.model_api import ADD
from openfisca_core.periods import MONTH, YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Household, Person


class salaire_brut_global(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    set_input = set_input_divide_by_period
    unit = "currency-MAD"
    label = "Rémunération brute globale mensuelle (traitements, indemnités, salaires, avantages en argent ou en nature)"
    reference = "https://www.tax.gov.ma"  # CGI, article 56


class elements_exoneres(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    set_input = set_input_divide_by_period
    unit = "currency-MAD"
    label = "Éléments mensuels de rémunération exonérés de l'IR"
    reference = "https://www.tax.gov.ma"  # CGI, article 57


class cotisations_sociales_obligatoires(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Cotisations sociales obligatoires à la charge du salarié (CNSS, AMO, retraite)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 58

    def formula(person, period, parameters):
        return person("cotisations_sociales_salarie", period, options=[ADD])


class nombre_personnes_a_charge(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Nombre de personnes à charge (conjoint et enfants légitimes ou légalement recueillis)"
    reference = "https://www.tax.gov.ma"  # CGI, article 74


class salaire_brut_imposable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Rémunération brute imposable (brut global moins éléments exonérés)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 56 à 58

    def formula(person, period, parameters):
        months = period.get_subperiods(MONTH)
        # Annual totals split into float32 months can accumulate rounding error.
        # Sum in float64 before OpenFisca casts the annual result to float32.
        return sum_(
            [person("salaire_brut_global", month) for month in months],
            axis=0,
            dtype=float64,
        ) - sum_(
            [person("elements_exoneres", month) for month in months],
            axis=0,
            dtype=float64,
        )


class frais_professionnels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Déduction forfaitaire pour frais professionnels (article 59)"
    reference = "https://www.tax.gov.ma"  # CGI, article 59

    def formula(person, period, parameters):
        base = person("salaire_brut_imposable", period) - person(
            "cotisations_sociales_obligatoires", period
        )
        seuil = parameters(
            period
        ).impot_revenu.frais_professionnels.seuil_taux_basse_remuneration
        taux = (person("salaire_brut_imposable", period) <= seuil) * parameters(
            period
        ).impot_revenu.frais_professionnels.taux_basse_remuneration + (
            person("salaire_brut_imposable", period) > seuil
        ) * parameters(period).impot_revenu.frais_professionnels.taux_haute_remuneration
        plafond = parameters(period).impot_revenu.frais_professionnels.plafond
        return min_(base * taux, plafond)


class salaire_net_imposable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Salaire net imposable annuel (assiette du barème)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 58 et 59

    def formula(person, period, parameters):
        assiette = (
            person("salaire_brut_imposable", period)
            - person("cotisations_sociales_obligatoires", period)
            - person("frais_professionnels", period)
        )
        return max_(assiette, 0)


class revenu_professionnel_net(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenu professionnel net annuel (régime du résultat net réel ou simplifié)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 30 à 39

    # Entrée : bénéfice net après charges déductibles. Un déficit est accepté ;
    # son report sur les exercices suivants (article 37) n'est pas modélisé.


class revenus_fonciers_bruts(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenus fonciers bruts annuels (loyers encaissés)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 61 et 64-I


class revenu_foncier_net(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenu foncier net imposable (brut moins abattement de 40 %)"
    reference = "https://www.tax.gov.ma"  # CGI, article 64-II

    def formula(person, period, parameters):
        brut = person("revenus_fonciers_bruts", period)
        if period.start.year < 2026:
            if (brut != 0).any():
                raise ValueError(
                    "Rental income is only modelled from 2026; no 2025 rules "
                    "are encoded."
                )
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.revenus_categories.revenus_fonciers
        return max_(brut.astype(float64) * (1 - params.abattement), 0)


class retenue_fonciere(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Retenue à la source sur les revenus fonciers, imputable sur l'IR"
    reference = "https://www.tax.gov.ma"  # CGI, articles 73-II et 160 bis

    def formula(person, period, parameters):
        brut = person("revenus_fonciers_bruts", period)
        if period.start.year < 2026:
            if (brut != 0).any():
                raise ValueError(
                    "Rental income is only modelled from 2026; no 2025 rules "
                    "are encoded."
                )
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.revenus_categories.revenus_fonciers
        brut = brut.astype(float64)
        return where(
            brut <= params.seuil_exoneration_retenue,
            0.0,
            where(
                brut < params.seuil_taux_reduit,
                brut * params.taux_reduit,
                brut * params.taux_normal,
            ),
        )


class revenu_global_imposable(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Revenu global imposable au barème (salaires, professionnel, foncier)"
    reference = "https://www.tax.gov.ma"  # CGI, articles 22 et 25

    def formula(person, period, parameters):
        # Chaque catégorie est déterminée distinctement (art. 25) : un déficit
        # professionnel ne s'impute pas sur les salaires ou le foncier. Il est
        # ramené à zéro ici ; son report (art. 37) n'est pas modélisé.
        total = (
            person("salaire_net_imposable", period)
            + max_(person("revenu_professionnel_net", period), 0)
            + person("revenu_foncier_net", period)
        )
        return max_(total, 0)


class dividendes_bruts(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Produits bruts d'actions et parts sociales"
    reference = "https://www.tax.gov.ma"  # CGI, articles 13 et 66-I-A


class interets_bruts(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Produits bruts de placements à revenu fixe"
    reference = "https://www.tax.gov.ma"  # CGI, articles 14 et 66-I-B


class plus_values_actions_cotees(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Profits nets de cession d'actions cotées en bourse"
    reference = "https://www.tax.gov.ma"  # CGI, article 66-II


class plus_values_titres_non_cotes(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Profits nets de cession de titres non cotés et de créances"
    reference = "https://www.tax.gov.ma"  # CGI, article 66-II


class impot_dividendes(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt libératoire sur les dividendes"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-II-B-7°

    def formula(person, period, parameters):
        if period.start.year < 2026:
            if (person("dividendes_bruts", period) != 0).any():
                raise ValueError(
                    "Capital income is only modelled from 2026; no 2025 rates "
                    "are encoded."
                )
            return person.filled_array(0.0)
        taux = parameters(
            period
        ).impot_revenu.revenus_categories.capitaux_mobiliers.taux_dividendes
        return max_(person("dividendes_bruts", period).astype(float64), 0) * taux


class impot_interets(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt libératoire sur les produits de placements à revenu fixe"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-II-G-3°

    def formula(person, period, parameters):
        if period.start.year < 2026:
            if (person("interets_bruts", period) != 0).any():
                raise ValueError(
                    "Capital income is only modelled from 2026; no 2025 rates "
                    "are encoded."
                )
            return person.filled_array(0.0)
        taux = parameters(
            period
        ).impot_revenu.revenus_categories.capitaux_mobiliers.taux_interets
        return max_(person("interets_bruts", period).astype(float64), 0) * taux


class impot_plus_values(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt sur les profits de cession de valeurs mobilières"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-II-C-1° et F-2°

    def formula(person, period, parameters):
        if period.start.year < 2026:
            return person.filled_array(0.0)
        params = parameters(period).impot_revenu.revenus_categories.capitaux_mobiliers
        return (
            max_(person("plus_values_actions_cotees", period), 0)
            * params.taux_plus_values_cotees
            + max_(person("plus_values_titres_non_cotes", period), 0)
            * params.taux_plus_values_non_cotees
        )


class impot_capitaux_mobiliers(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt total sur les revenus et profits de capitaux mobiliers"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-II

    def formula(person, period, parameters):
        if period.start.year < 2026:
            capital = (
                person("dividendes_bruts", period)
                + person("interets_bruts", period)
                + person("plus_values_actions_cotees", period)
                + person("plus_values_titres_non_cotes", period)
            )
            if (capital != 0).any():
                raise ValueError(
                    "Capital income is only modelled from 2026; no 2025 rates "
                    "are encoded."
                )
            return person.filled_array(0.0)
        return (
            person("impot_dividendes", period)
            + person("impot_interets", period)
            + person("impot_plus_values", period)
        )


class ir_brut(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt brut sur le revenu selon le barème progressif annuel (article 73-I)"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-I

    def formula(person, period, parameters):
        bareme = parameters(period).impot_revenu.bareme
        return bareme.calc(person("revenu_global_imposable", period))


class deduction_charges_famille(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Déduction pour charges de famille (500 DH en 2025, 600 DH à partir de 2026, maximum 6 personnes)"
    reference = "https://www.tax.gov.ma"  # CGI, article 74

    def formula(person, period, parameters):
        montant = parameters(
            period
        ).impot_revenu.deduction_charges_famille.montant_par_personne
        maximum = parameters(
            period
        ).impot_revenu.deduction_charges_famille.nombre_maximum_personnes
        personnes = min_(person("nombre_personnes_a_charge", period), maximum)
        return personnes * montant


class impot_sur_le_revenu(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Impôt net sur le revenu à payer (impôt brut moins déductions, plancher à zéro)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 74

    def formula(person, period, parameters):
        brut = person("ir_brut", period)
        deduction = person("deduction_charges_famille", period)
        apres_deduction = max_(brut - deduction, 0)
        # La retenue foncière est imputée sur l'impôt dû, sans restitution de
        # l'excédent : le plancher à zéro borne déjà le crédit.
        return max_(apres_deduction - person("retenue_fonciere", period), 0)


class impot_sur_le_revenu_menage(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Impôt sur le revenu du ménage (somme des impôts individuels et des "
        "impôts libératoires du capital)"
    )
    reference = "https://www.tax.gov.ma"  # CGI, article 25

    def formula(household, period, parameters):
        return household.sum(
            household.members("impot_sur_le_revenu", period)
        ) + household.sum(household.members("impot_capitaux_mobiliers", period))
