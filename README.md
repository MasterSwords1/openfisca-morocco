# OpenFisca Morocco

[![CI](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml/badge.svg)](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Licence: AGPL-3.0-or-later](https://img.shields.io/badge/licence-AGPL--3.0--or--later-blue.svg)](https://github.com/MasterSwords1/openfisca-morocco/blob/main/LICENSE)

**English** · [Français](https://github.com/MasterSwords1/openfisca-morocco/blob/main/README.fr.md)

[OpenFisca](https://openfisca.org) model of the Moroccan tax and benefit
system. It computes taxes and benefits on the situations you describe — a
person, a household or a company — for the periods the package covers.

> **Status: early, community-maintained.** The package is not yet on PyPI. The
> public release and the listing on the OpenFisca website are on hold until the
> remaining release blockers are closed ([#12](https://github.com/MasterSwords1/openfisca-morocco/issues/12),
> [#13](https://github.com/MasterSwords1/openfisca-morocco/issues/13)).

## What it covers

| Area | Scope | From |
|---|---|---|
| **IR — salaries** | Progressive scale, professional expenses, family deduction, monthly withholding from 2016 | 2010 |
| **IR — professional (net réel)** | Supplied net-réel professional income | 2010 |
| **IR — other regimes and income** | Simplified/CPU/auto-entrepreneur, rental, capital, property and foreign income | 2026 |
| **CNSS / AMO** | Employee and employer contributions, ceilings, employer cost | 2016 |
| **Family allowances** | CNSS benefit, 300 DH tiers (100 DH for ranks 4–6 from 2023), six-child cap | 2019-07 |
| **Aide sociale directe** | Monthly, school-return, placement and exceptional allowances | 2023-12 |
| **TVA** | Monthly company declaration, dated rates and transitional schedules; annual Article 104 deduction prorata | 2004 |
| **Registration duties** | Property acquisitions, company capital, conservation fees | 2026 |
| **IS / cotisation minimale** | Corporate income tax and minimum contribution | 2026 |
| **Code du travail** | Seniority bonus, severance pay, SMIG floor | 2004-07 |

Entities: `Person`, `Household`, `Company`. Periods: `YEAR` for IR
assessment, IS/CM and registration duties; `MONTH` for IR withholding, TVA,
contributions, family allowances, ASD and the Code du travail.
TVA turnover detail and the calculated deduction prorata use `YEAR` periods;
the resulting prorata applies to monthly deductions in the following year.

The detailed scope, legal references and known limits are in
[`docs/coverage.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/coverage.md).

## Install

The package is not on PyPI yet. You need Python 3.11+ and
[uv](https://docs.astral.sh/uv/). From a checkout (the project started from
the [OpenFisca Country Template](https://github.com/openfisca/country-template)):

```sh
git clone https://github.com/MasterSwords1/openfisca-morocco.git
cd openfisca-morocco
uv sync --locked --all-extras --dev
```

## Quick start

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tbs = CountryTaxBenefitSystem()

# A salaried person in 2025
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

# A company in 2026
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

See [`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md)
for period conventions, the Web API, situation examples and reforms.

## Tests

```sh
make test
```

The five TVA corpus tests also run when `../morocco-holy-graph` exists or
`MOROCCO_HOLY_GRAPH` points to it; otherwise they are skipped.

## Legislation Explorer / Parameters Website

Start the local API and legislation browser with one command:

```sh
docker compose -f explorer/docker-compose.yml up --build -d
```

The website is at <http://localhost:2020> and the API specification is at
<http://localhost:5000/spec>. See
[`explorer/README.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/explorer/README.md)
for deployment, public hosting and legal-link guidance.

## Documentation

| Page | Contents |
|---|---|
| [`ROADMAP.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/ROADMAP.md) | Phases, milestones and what is out of scope |
| [`docs/releasing.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/releasing.md) | PyPI trusted publishing, dispatch and verification |
| [`docs/coverage.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/coverage.md) | What is modelled, sources and limitations |
| [`docs/explorer-links.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/explorer-links.md) | Public reference link policy for the Legislation Explorer |
| [`docs/tva-prorata.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/tva-prorata.md) | Annual TVA deduction prorata under CGI Article 104-I |
| [`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md) | Install, usage, examples, layout, releases |
| [`docs/impot-revenu-categories.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/impot-revenu-categories.md) | Professional, rental, capital and foreign income |
| [`docs/impot-societes.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/impot-societes.md) | IS and cotisation minimale |
| [`docs/enregistrement.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/enregistrement.md) | Registration duties and conservation fees |
| [`docs/aide-sociale-directe.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/aide-sociale-directe.md) | Direct social assistance |
| [`docs/tva-source-review.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/tva-source-review.md) | TVA source review and historical checks |
| [`docs/code-travail.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/code-travail.md) | Seniority bonus, severance and SMIG |
| [`explorer/README.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/explorer/README.md) | Self-hosted Legislation Explorer and public deployment |

## Status and limits

- **A model, not a database.** You provide the situation; the package ships no
  survey or administrative data.
- **Partial coverage.** Each tax and benefit has exclusions; see the page for
  the area you use before drawing conclusions.
- **Historical IR is salarial.** 2010–2024 covers salaries and supplied
  net-réel professional income; rental, capital, property and foreign income
  start in 2026.
- **Payroll defaults start in 2016.** For 2010–2015, supply
  `cotisations_sociales_obligatoires` explicitly.
- **Some rules are caller assertions.** IS three-year/exclusion flags, the CM
  start-up exemption and registration act dates are inputs, not inferred.
- **Labour-code benefits use caller inputs.** `salaire_de_base` is the article
  353 base, `anciennete_annees` is supplied, and severance uses the month's
  gross rather than the 52-week average.

## Contributing

Contributions are welcome. Run `make test` and
`uv run pre-commit run --all-files` before opening a pull request. See
[`docs/development.md`](https://github.com/MasterSwords1/openfisca-morocco/blob/main/docs/development.md).

## Licence

[AGPL-3.0-or-later](https://github.com/MasterSwords1/openfisca-morocco/blob/main/LICENSE).
