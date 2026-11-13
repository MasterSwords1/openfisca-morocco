"""La TVA se calcule sur une entreprise simulée, pas seulement en unitaire.

Les tests YAML vérifient les montants, mais ils passent par le lanceur de tests
d'OpenFisca. Ce module vérifie le chemin public de simulation
(``SimulationBuilder.build_from_dict``), qui a deux exigences que les tests YAML
ne voient pas :

- l'entité ``Company`` doit pouvoir être instanciée, donc porter au moins un
  rôle (une entité de groupe sans rôle fait échouer le constructeur) ;
- une situation sans entreprise doit continuer à se construire, pour que le
  modèle IR existant ne soit pas cassé par l'ajout de l'entité.

Le premier test reproduit les montants du modèle Catala validé du corpus
``morocco-holy-graph`` (``laws/ma_tax_law/tests/test_catala_tax.py``,
``test_tva_multi_rate_and_deductions``) : 257 000 / 150 000 / 107 000.
"""

from openfisca_core.simulations import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

TBS = CountryTaxBenefitSystem()


def build(situation):
    return SimulationBuilder().build_from_dict(TBS, situation)


def entreprise(chiffre_affaires, period="2023-06", **autres):
    """One company attached to one person, with the given inputs."""
    entreprise_inputs = {
        "membres": ["Gerant"],
        **{
            variable: {period: value}
            for variable, value in {**chiffre_affaires, **autres}.items()
        },
    }
    return build(
        {
            "persons": {"Gerant": {}},
            "companies": {"Entreprise": entreprise_inputs},
        },
    )


def test_la_situation_d_entreprise_se_construit_et_reproduit_le_corpus():
    simulation = entreprise(
        {
            "chiffre_affaires_taux_normal": 1_000_000,
            "chiffre_affaires_taux_reduit_10": 500_000,
            "chiffre_affaires_taux_reduit_7": 100_000,
        },
        tva_deductible_charges=120_000,
        tva_deductible_immobilisations=30_000,
    )

    assert list(simulation.calculate("tva_collectee_totale", "2023-06")) == [257_000]
    assert list(simulation.calculate("tva_deductible_autorisee", "2023-06")) == [
        150_000
    ]
    assert list(simulation.calculate("tva_nette_a_payer", "2023-06")) == [107_000]
    assert list(simulation.calculate("credit_tva_a_reporter", "2023-06")) == [0]


def test_un_chiffre_d_affaires_sur_un_taux_abroge_n_est_pas_impose():
    simulation = entreprise(
        {"chiffre_affaires_taux_reduit_7": 100_000},
        period="2024-06",
    )

    assert list(simulation.calculate("tva_collectee_taux_7", "2024-06")) == [0]
    assert list(simulation.calculate("chiffre_affaires_taux_abroge", "2024-06")) == [
        100_000
    ]


def test_une_situation_sans_entreprise_se_construit_toujours():
    """Le modèle IR ne doit pas dépendre de l'existence d'une entreprise."""
    simulation = build(
        {
            "persons": {
                "Salarie": {
                    "salaire_brut_global": {"2025": 200_000},
                    "elements_exoneres": {"2025": 0},
                    "cotisations_sociales_obligatoires": {"2025": 20_000},
                    "nombre_personnes_a_charge": {"2025": 3},
                },
            },
            "households": {"_": {"adults": ["Salarie"]}},
        },
    )

    assert list(simulation.calculate("impot_sur_le_revenu", "2025")) == [25_800]


def test_une_situation_avec_personnes_seules_se_construit():
    """Régression : une entité de groupe sans rôle casse ce chemin."""
    simulation = build({"persons": {"A": {}}})
    assert simulation is not None
