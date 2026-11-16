"""Impôt sur le revenu (IR) — revenus salariaux et assimilés.

Pipeline encoded from the Code Général des Impôts (Loi n° 43-06), as reformed
by the Loi de Finances 2025:

- article 56: salarial income subject to the IR
- article 59: forfaitary professional-expense deduction (35 % up to 78 000 DH of
  gross annual pay, 25 % above, both capped at 35 000 DH)
- article 73-I: progressive annual scale on net taxable income
- article 74: 500 DH deduction per dependent, capped at 6 dependents

Salary and exempt remuneration inputs are monthly amounts. Annual totals can
still be supplied and are divided between months by OpenFisca. The taxable
income pipeline, contribution deduction and family-dependent count remain
annual: the CGI scale is applied once to the year's income, not month by month.
Monthly withholding is not modelled.
"""

from numpy import float64, maximum as max_, minimum as min_, sum as sum_
from openfisca_core.holders import set_input_divide_by_period
from openfisca_core.model_api import ADD
from openfisca_core.periods import MONTH, YEAR
from openfisca_core.variables import Variable

from openfisca_morocco.entities import Person


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


class ir_brut(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = "Impôt brut sur le revenu selon le barème progressif annuel (article 73-I)"
    reference = "https://www.tax.gov.ma"  # CGI, article 73-I

    def formula(person, period, parameters):
        bareme = parameters(period).impot_revenu.bareme
        return bareme.calc(person("salaire_net_imposable", period))


class deduction_charges_famille(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = "currency-MAD"
    label = (
        "Déduction pour charges de famille (500 DH par personne à charge, maximum 6)"
    )
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
        return max_(
            person("ir_brut", period) - person("deduction_charges_famille", period),
            0,
        )
