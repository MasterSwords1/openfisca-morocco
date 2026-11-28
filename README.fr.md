# OpenFisca Maroc

[![CI](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml/badge.svg)](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Licence : AGPL-3.0-or-later](https://img.shields.io/badge/licence-AGPL--3.0--or--later-blue.svg)](https://github.com/MasterSwords1/openfisca-morocco/blob/main/LICENSE)

[English](https://github.com/MasterSwords1/openfisca-morocco/blob/main/README.md) · **Français**

Modèle [OpenFisca](https://openfisca.org) du système fiscal et social marocain.
Le paquet calcule les impôts et prestations sur les situations que vous
décrivez — une personne, un ménage ou une entreprise — pour les périodes
couvertes.

> **Statut : préliminaire, maintenu par la communauté.** Le paquet n'est pas
> encore publié sur PyPI. La publication publique et le référencement sur le
> site OpenFisca sont en attente de la levée des derniers blocages de publication
> ([#12](https://github.com/MasterSwords1/openfisca-morocco/issues/12),
> [#13](https://github.com/MasterSwords1/openfisca-morocco/issues/13)).

## Ce qui est modélisé

| Domaine | Périmètre | Depuis |
|---|---|---|
| **IR — salaires** | Barème progressif, frais professionnels, charges de famille, retenue mensuelle à la source depuis 2016 | 2010 |
| **IR — professionnel (net réel)** | Revenu professionnel net réel fourni | 2010 |
| **IR — autres régimes et revenus** | Régimes simplifié/CPU/auto-entrepreneur, revenus fonciers, de capitaux, du patrimoine et étrangers | 2026 |
| **CNSS / AMO** | Cotisations salariales et patronales, plafonds, coût employeur | 2016 |
| **Allocations familiales** | Prestation CNSS, paliers de 300 DH (100 DH pour les rangs 4 à 6 depuis 2023), plafond de six enfants | 2019-07 |
| **Aide sociale directe** | Allocations mensuelles, de rentrée, de placement et exceptionnelle | 2023-12 |
| **TVA** | Déclaration mensuelle d'entreprise, taux datés et taux transitoires ; prorata annuel de déduction selon l'article 104 | 2004 |
| **Droits d'enregistrement** | Acquisitions immobilières, capital social, conservation foncière | 2026 |
| **IS / cotisation minimale** | Impôt sur les sociétés et cotisation minimale | 2026 |
| **Code du travail** | Prime d'ancienneté, indemnité de licenciement, plancher SMIG | 2004-07 |

Entités : `Person`, `Household`, `Company`. Périodes : `YEAR` pour l'IR
annuel, l'IS/CM et les droits d'enregistrement ; `MONTH` pour la retenue à la
source de l'IR, la TVA, les cotisations, les allocations familiales, l'ASD et
le Code du travail.
Le détail annuel du chiffre d'affaires TVA et le prorata calculé utilisent la
période `YEAR` ; le prorata s'applique aux déductions mensuelles de l'année
suivante.

Le périmètre détaillé, les références légales et les limites connues sont
dans [`docs/coverage.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/coverage.md).

## Installation

Le paquet n'est pas encore sur PyPI. Il faut Python 3.11+ et
[uv](https://docs.astral.sh/uv/). Depuis un dépôt cloné (le projet est issu
du [modèle de pays OpenFisca](https://github.com/openfisca/country-template)) :

```sh
git clone https://github.com/MasterSwords1/openfisca-morocco.git
cd openfisca-morocco
uv sync --locked --all-extras --dev
```

## Démarrage rapide

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tbs = CountryTaxBenefitSystem()

# Un salarié en 2025
simulation = SimulationBuilder().build_from_dict(
    tbs,
    {
        "persons": {
            "Salarie": {
                "salaire_brut_global": {"2025": 120_000},
                "salaire_brut": {"2025": 120_000},
            }
        },
        "households": {"Menage": {"adults": ["Salarie"]}},
    },
)
print(simulation.calculate("impot_sur_le_revenu", "2025").round(2))  # [7218.72]

# Une société en 2026
simulation = SimulationBuilder().build_from_dict(
    tbs,
    {
        "persons": {"Gerant": {}},
        "companies": {
            "Societe": {
                "membres": ["Gerant"],
                "benefice_fiscal": {"2026": 500_000},
                "chiffre_affaires_annuel": {"2026": 2_000_000},
            }
        },
    },
)
print(simulation.calculate("is_net_a_payer", "2026"))  # [100000.]
```

Voir [`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md)
pour les conventions de période, l'API Web, les exemples de situations et les
réformes.

## Tests

```sh
make test
```

Les cinq tests du corpus TVA s'exécutent aussi lorsque `../morocco-holy-graph`
existe ou que `MOROCCO_HOLY_GRAPH` pointe vers le corpus ; sinon ils sont
ignorés.

## Explorateur de la législation / Site des paramètres

Démarrez l'API locale et l'explorateur de la législation avec une seule
commande :

```sh
docker compose -f explorer/docker-compose.yml up --build -d
```

Le site est disponible sur <http://localhost:2020> et la spécification de
l'API sur <http://localhost:5000/spec>. Consultez
[`explorer/README.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/explorer/README.md)
pour le déploiement, l'hébergement public et les liens juridiques.

## Documentation

| Page | Contenu |
|---|---|
| [`ROADMAP.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/ROADMAP.md) | Phases, jalons et périmètre exclu |
| [`docs/releasing.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/releasing.md) | Publication PyPI, déclenchement et vérification |
| [`docs/coverage.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/coverage.md) | Périmètre, sources et limites |
| [`docs/tva-prorata.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/tva-prorata.md) | Prorata annuel de déduction TVA selon l'article 104-I du CGI |
| [`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md) | Installation, usage, exemples, arborescence, publication |
| [`docs/impot-revenu-categories.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/impot-revenu-categories.md) | Revenus professionnels, fonciers, capitaux et étrangers |
| [`docs/impot-societes.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/impot-societes.md) | IS et cotisation minimale |
| [`docs/enregistrement.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/enregistrement.md) | Droits d'enregistrement et conservation foncière |
| [`docs/aide-sociale-directe.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/aide-sociale-directe.md) | Aide sociale directe |
| [`docs/tva-source-review.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/tva-source-review.md) | Revue des sources TVA et vérifications historiques |
| [`docs/code-travail.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/code-travail.md) | Prime d'ancienneté, indemnité de licenciement et SMIG |
| [`explorer/README.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/explorer/README.md) | Explorateur de la législation et déploiement public |

## Statut et limites

- **Un modèle, pas une base de données.** Vous fournissez la situation ; le
  paquet ne contient ni enquête ni données administratives.
- **Couverture partielle.** Chaque impôt et prestation a des exclusions ;
  consultez la page du domaine concerné avant de conclure.
- **L'IR historique est salarial.** 2010–2024 couvre les salaires et le revenu
  professionnel net réel fourni ; les revenus fonciers, de capitaux, du
  patrimoine et étrangers sont modélisés à partir de 2026.
- **Les paramètres de paie par défaut n'existent qu'à partir de 2016.** Pour
  2010–2015, fournissez `cotisations_sociales_obligatoires` explicitement.
- **Certaines règles sont déclarées par l'appelant.** La condition des trois
  exercices et les exclusions de l'IS, l'exonération de CM de démarrage et la
  date de l'acte d'enregistrement sont des entrées, et non des valeurs
  déduites d'office.
- **Les prestations du Code du travail reposent sur des entrées.** L'assiette
  `salaire_de_base` est celle de l'article 353, `anciennete_annees` est
  fournie, et l'indemnité utilise le salaire du mois plutôt que la moyenne des
  52 semaines.

## Contribuer

Les contributions sont bienvenues. Exécutez `make test` et
`uv run pre-commit run --all-files` avant d'ouvrir une pull request. Voir
[`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md).

## Licence

[AGPL-3.0-or-later](https://github.com/MasterSwords1/openfisca-morocco/blob/main/LICENSE).
