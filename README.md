# OpenFisca Morocco

[OpenFisca](https://openfisca.org) model of Moroccan tax and benefit law, as
code.

**Status: early.** Today the package models one thing: the **impôt sur le revenu
(IR)** on salarial income, for **annual** periods, under the rules in force
since **1 January 2025**. Everything else — social contributions, VAT, family
allowances, the direct social support — is not modelled yet and is tracked in
the [issue list](https://github.com/MasterSwords1/openfisca-morocco/issues).

| | |
|---|---|
| Country | Morocco |
| Currency | dirham (MAD), `currency-MAD` |
| Periods | `YEAR` |
| First modelled period | 2025-01-01 |
| Licence | AGPL-3.0-or-later |

## What is modelled

The IR pipeline of the Code Général des Impôts (CGI) for **salarial income**,
in the order the law applies it:

```
salaire_brut_global − elements_exoneres            (art. 56, 57)
    = salaire_brut_imposable
    − cotisations_sociales_obligatoires             (art. 58)
    − frais_professionnels                          (art. 59)
    = salaire_net_imposable
    → ir_brut via the progressive scale             (art. 73-I)
    − deduction_charges_famille                     (art. 74)
    = impot_sur_le_revenu  (floored at 0)
```

### Coverage table

| CGI article | Provision | Variables | Parameters | From |
|---|---|---|---|---|
| 56 | Salaries, wages, benefits in cash or in kind | `salaire_brut_global` (input) | — | 2025-01-01 |
| 57 | Exempt elements of pay | `elements_exoneres` (input) | — | 2025-01-01 |
| 58 | Compulsory social contributions borne by the employee | `cotisations_sociales_obligatoires` (input) | — | 2025-01-01 |
| 56–58 | Gross taxable pay | `salaire_brut_imposable` | — | 2025-01-01 |
| 59 | Forfaitary professional-expense deduction | `frais_professionnels` | `impot_revenu.frais_professionnels` | 2025-01-01 |
| 58–59 | Net taxable pay (the scale's base) | `salaire_net_imposable` | — | 2025-01-01 |
| 73-I | Progressive annual scale | `ir_brut` | `impot_revenu.bareme` | 2025-01-01 |
| 74 | Family-charge deduction | `deduction_charges_famille` | `impot_revenu.deduction_charges_famille` | 2025-01-01 |
| 74 | Net income tax payable | `impot_sur_le_revenu` | — | 2025-01-01 |

The figures, for reference:

- **Scale (art. 73-I, LF 2025):** 0 % up to 40 000 DH, then 10 % (40 001–60 000),
  20 % (60 001–80 000), 30 % (80 001–100 000), 34 % (100 001–180 000), 37 % above.
- **Professional expenses (art. 59):** 35 % of gross pay up to 78 000 DH, 25 %
  above, capped at 35 000 DH in both cases.
- **Family charges (art. 74):** 500 DH per dependent, at most 6 dependents.

`birth` and `age` are also available: they are factual demographics, not
legislation, and carry no legal reference. Moroccan age-based provisions will
build on them.

## Provenance

Every modelled figure is traceable to a published text, and every input variable
names the article it comes from.

| Piece | Source |
|---|---|
| Code Général des Impôts (arts. 1–248) | Loi n° 43-06, Dahir n° 1-06-232 of 31 December 2006, *Bulletin Officiel* n° 5487 bis of 31 December 2006, pp. 4153–4210 |
| Art. 73-I scale in force in 2025 | Loi de finances n° 60-24 for the 2025 budget year, Dahir n° 1-24-65 of 13 December 2024, *Bulletin Officiel* n° 7362 bis of 19 December 2024 |
| Arts. 59 and 74 figures | CGI as encoded in the validated Catala model of the `morocco-holy-graph` corpus (`laws/ma_tax_law/catala/cgi_ir.catala_fr`) and cross-checked against its tests (`laws/ma_tax_law/tests/test_catala_tax.py`) |
| Parameter values | `metadata.reference` on each parameter file under `openfisca_morocco/parameters/` |

The corpus is the source of truth for this package: figures are taken from
`morocco-holy-graph`, not from memory or from unversioned web pages. Where the
corpus itself has not yet captured the controlling text (for example the
pre-2025 versions of articles 59 and 73), the limitation is stated below rather
than guessed.

## Limitations

Stated plainly, because they determine what you may conclude from a simulation:

- **Salarial income only.** Professional, rental, capital and foreign income are
  not modelled, so this is not a complete IR. See issue
  [#15](https://github.com/MasterSwords1/openfisca-morocco/issues/15).
- **Annual periods only.** The scale is annual; monthly withholding (retenue à
  la source) is not modelled. See issue
  [#9](https://github.com/MasterSwords1/openfisca-morocco/issues/9).
- **2025 onwards only.** Earlier scales, rates and thresholds are not encoded,
  so a simulation for 2024 or before returns the 2025 law or a default value —
  do not use it for historical work.
- **Contributions are an input, not a computation.** `cotisations_sociales_obligatoires`
  must be supplied; CNSS/AMO rates and ceilings are not modelled yet. See issue
  [#5](https://github.com/MasterSwords1/openfisca-morocco/issues/5).
- **No benefits, no VAT.** Allocations familiales, aide sociale directe, TVA and
  the rest of the system are absent. See issues
  [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6),
  [#7](https://github.com/MasterSwords1/openfisca-morocco/issues/7) and
  [#8](https://github.com/MasterSwords1/openfisca-morocco/issues/8).
- **No microdata.** The package computes on situations you provide; it ships no
  survey or administrative dataset.
- **Not published on PyPI yet.** Install from source (below) until issue
  [#12](https://github.com/MasterSwords1/openfisca-morocco/issues/12) is closed.

## Install

Requires Python 3.9 or later (CI runs 3.13) and
[uv](https://docs.astral.sh/uv/).

The package is not on PyPI yet, so install it from source:

```sh
git clone https://github.com/MasterSwords1/openfisca-morocco.git
cd openfisca-morocco
uv sync --locked --all-extras --dev
```

Check that it works:

```sh
make test
# openfisca test --country-package openfisca_morocco openfisca_morocco/tests
# 10 passed
```

Once published, installation will be `uv add openfisca-morocco`.

## Use it

### From Python

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tax_benefit_system = CountryTaxBenefitSystem()

simulation = SimulationBuilder().build_from_dict(
    tax_benefit_system,
    {
        "persons": {
            "Salarie": {
                "salaire_brut_global": {"2025": 200_000},
                "elements_exoneres": {"2025": 0},
                "cotisations_sociales_obligatoires": {"2025": 20_000},
                "nombre_personnes_a_charge": {"2025": 3},
            }
        },
        "households": {"_": {"adults": ["Salarie"]}},
    },
)

print(simulation.calculate("salaire_net_imposable", "2025"))  # [145000.]
print(simulation.calculate("impot_sur_le_revenu", "2025"))  # [25800.]
```

All amounts are annual and in dirhams. Inputs are bare numbers: `salaire_brut_global`
is the gross annual pay, and `nombre_personnes_a_charge` counts the spouse and
dependent children.

### From the Web API

```sh
make serve-local   # openfisca serve --country-package openfisca_morocco
```

Then, in another terminal:

```sh
curl "http://localhost:5000/spec"          # OpenAPI specification

curl -X POST -H "Content-Type: application/json" \
  -d @./openfisca_morocco/situation_examples/salarie.json \
  http://localhost:5000/calculate
```

The bundled example answers `"impot_sur_le_revenu": {"2025": 25800.0}`.

### Run the tests

```sh
make test          # YAML tests under openfisca_morocco/tests/
pre-commit run --all-files
```

The YAML tests in `openfisca_morocco/tests/impot_revenu.yaml` document the
expected law at the scale's boundaries, and
`openfisca_morocco/tests/age.yaml` covers the `age` formula.

## Repository layout

```
openfisca_morocco/
├── entities.py                 # Household (adults/children) and Person
├── parameters/
│   └── impot_revenu/           # barème, frais professionnels, charges de famille
├── variables/
│   ├── impot_revenu.py         # the IR pipeline
│   └── demographics.py         # birth, age
├── situation_examples/
│   └── salarie.json            # one salaried taxpayer, used by the Web API spec
└── tests/                      # YAML tests
```

## Roadmap

The path to a complete, usable package — IR on all income categories,
CNSS/AMO contributions, TVA, family allowances, direct social support,
realistic situation and reform examples, PyPI publication — is tracked in the
[v1.0 milestone](https://github.com/MasterSwords1/openfisca-morocco/milestone/1).
Each issue states its goal, scope, acceptance criteria and the issues it depends
on.

## Contributing

Read [CONTRIBUTING](CONTRIBUTING.md), open a pull request against `main`, and
follow the version and changelog rules described there.

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
