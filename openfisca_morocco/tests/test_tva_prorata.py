"""Annual TVA deduction prorata under CGI Article 104-I."""

from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def build(company_inputs):
    return SimulationBuilder().build_from_dict(
        TBS,
        {
            "persons": {"Gerant": {}},
            "companies": {"Entreprise": {"membres": ["Gerant"], **company_inputs}},
        },
    )


def test_prorata_annuel_et_application_sur_annee_suivante():
    simulation = build(
        {
            "chiffre_affaires_taux_normal": {
                f"2024-{month:02d}": 100_000 for month in range(1, 13)
            },
            "tva_deductible_charges": {"2025-01": 1_000},
        }
    )
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [1.0]
    assert list(simulation.calculate("tva_deductible_autorisee", "2025-01")) == [1_000]


def test_mixte_export_exonere_deduisible_et_exonere_sans_deduction():
    simulation = build(
        {
            "chiffre_affaires_taxable_autres": {"2024": 600_000},
            "chiffre_affaires_exonere_avec_deduction": {"2024": 300_000},
            "chiffre_affaires_exonere_sans_deduction": {"2024": 100_000},
            "tva_deductible_charges": {"2025-01": 1_000},
        }
    )
    assert list(simulation.calculate("chiffre_affaires_total_declare", "2024")) == [
        1_000_000
    ]
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [0.9]
    assert list(simulation.calculate("tva_deductible_autorisee", "2025-01")) == [900]


def test_exonere_sans_droit_de_deduction():
    simulation = build({"chiffre_affaires_exonere_sans_deduction": {"2024": 500_000}})
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [0.0]


def test_suspension_article_94_est_au_numerateur():
    simulation = build(
        {
            "chiffre_affaires_taxable_autres": {"2024": 500_000},
            "chiffre_affaires_suspension": {"2024": 250_000},
            "chiffre_affaires_exonere_sans_deduction": {"2024": 250_000},
        }
    )
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [0.75]


def test_hors_champ_est_au_denominateur():
    simulation = build(
        {
            "chiffre_affaires_taxable_autres": {"2024": 500_000},
            "chiffre_affaires_hors_champ": {"2024": 500_000},
        }
    )
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [0.5]


def test_absence_de_detail_conserve_le_prorata_manuel():
    simulation = build(
        {
            "prorata_deduction": {"2025-01": 0.5},
            "tva_deductible_charges": {"2025-01": 1_000},
        }
    )
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [1.0]
    assert list(simulation.calculate("tva_deductible_autorisee", "2025-01")) == [500]


def test_annee_courante_ne_change_pas_ses_deductions_mensuelles():
    simulation = build(
        {
            "chiffre_affaires_exonere_sans_deduction": {"2025": 500_000},
            "prorata_deduction": {"2025-01": 0.8, "2026-01": 0.8},
            "tva_deductible_charges": {"2025-01": 1_000, "2026-01": 1_000},
        }
    )
    assert list(simulation.calculate("tva_deductible_autorisee", "2025-01")) == [800]
    assert list(simulation.calculate("tva_deductible_autorisee", "2026-01")) == [0]


def test_zero_et_montants_negatifs_ne_produisent_pas_un_prorata_hors_limites():
    simulation = build(
        {
            "chiffre_affaires_taxable_autres": {"2024": -10},
            "chiffre_affaires_exonere_sans_deduction": {"2024": 20},
        }
    )
    assert list(simulation.calculate("chiffre_affaires_taxable_annuel", "2024")) == [
        -10
    ]
    assert list(simulation.calculate("chiffre_affaires_total_declare", "2024")) == [10]
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [0.0]

    zero = build({"chiffre_affaires_taxable_autres": {"2024": 0}})
    assert list(zero.calculate("chiffre_affaires_total_declare", "2024")) == [0]
    assert list(zero.calculate("prorata_deduction_calcule", "2024")) == [1.0]


def test_somme_annuelle_inclut_tous_les_taux_mais_pas_le_taux_abroge_derivable():
    simulation = build(
        {
            "chiffre_affaires_taux_normal": {"2024-01": 100},
            "chiffre_affaires_taux_reduit_10": {"2024-02": 200},
            "chiffre_affaires_taux_reduit_14": {"2024-03": 300},
            "chiffre_affaires_taux_reduit_7": {"2024-04": 400},
            "chiffre_affaires_taux_transitoire": {"2024-05": 500},
            "chiffre_affaires_taxable_autres": {"2024": 600},
        }
    )
    assert list(simulation.calculate("chiffre_affaires_taxable_annuel", "2024")) == [
        2_100
    ]


def test_exonere_avec_deduction_seul_donne_un_prorata_de_un():
    simulation = build({"chiffre_affaires_exonere_avec_deduction": {"2024": 500_000}})
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [1.0]


def test_numerateur_superieur_au_denominateur_est_plafonne_a_un():
    simulation = build(
        {
            "chiffre_affaires_taxable_autres": {"2024": 100},
            "chiffre_affaires_exonere_sans_deduction": {"2024": -50},
        }
    )
    assert list(simulation.calculate("chiffre_affaires_total_declare", "2024")) == [50]
    assert list(simulation.calculate("prorata_deduction_calcule", "2024")) == [1.0]
