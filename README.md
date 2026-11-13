# OpenFisca Morocco

[OpenFisca](https://openfisca.org) model of Moroccan tax and benefit law, as
code.

**Status: early.** The package models two things: the **impôt sur le revenu
(IR)** on salarial income for **annual** periods under the rules in force since
**1 January 2025**, and the **taxe sur la valeur ajoutée (TVA)** declared by an
enterprise for **monthly** periods, with dated rates running **2004–2026**.
Everything else — social contributions, family allowances, the direct social
support — is not modelled yet and is tracked in the
[issue list](https://github.com/MasterSwords1/openfisca-morocco/issues).

| | |
|---|---|
| Country | Morocco |
| Currency | dirham (MAD), `currency-MAD` |
| Entities | `Person`, `Household`, `Company` |
| Periods | `YEAR` (IR), `MONTH` (TVA) |
| First modelled period | 2004-01-01 (TVA), 2025-01-01 (IR) |
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

## What is modelled — TVA

The VAT declaration of an enterprise, on the `Company` entity, for **monthly**
periods (CGI article 112):

```
chiffre_affaires × taux par taux déclaré        (art. 98, 99, 247-XXXXI)
    = tva_collectee_totale
(tva_deductible_charges + tva_deductible_immobilisations)
    × prorata_deduction                          (art. 101, 104)
    + credit_tva_anterieur
    = tva_deductible_autorisee
tva_collectee_totale − tva_deductible_autorisee
    = tva_nette_a_payer / credit_tva_a_reporter  (floored at 0)
```

### Dated rates, not a flat triple

| Period | General rates | Legal basis |
|---|---|---|
| 2004-01-01 → 2023-12-31 | 20 % · 14 % · 10 % · 7 % | Loi n° 30-85, then CGI arts. 98–99 (loi n° 43-06) |
| 2024-01-01 → 2026-12-31 | 20 % · 10 % | CGI art. 99 rewritten by loi de finances n° 55-23; art. 98 abrogated |

The four-rate structure ends on **1 January 2024**, not in 2026: the 2024
finance law rewrites article 99 as `A) 20 %` / `B) 10 %` and abrogates article
98. The 7 % and 14 % parameters therefore stay declared (so 2004–2023 can be
simulated) but carry `en_vigueur = 0` from 2024-01-01, and a chiffre d'affaires
declared on those brackets is reported separately in
`chiffre_affaires_taux_abroge` instead of being taxed at an abrogated rate.

### Transitional rates, 2024–2026

Article 247-XXXXI gives seven operation categories their own glide path. They
are selected by the `tva_operation_transitoire` input, and they are *not*
general rates:

| Operation (`tva_operation_transitoire`) | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| `electricite` | 16 % | 18 % | 20 % |
| `compteur_electricite` | 11 % | 15 % | 20 % |
| `electricite_renouvelable` | 12 % | 10 % | 10 % |
| `sucre` | 8 % | 9 % | 10 % |
| `transport_hors_urbain_et_routier` | 16 % | 18 % | 20 % |
| `transport_urbain_et_routier` | 13 % | 12 % | 10 % |
| `courtier_assurances` | 12 % | 10 % | 10 % |

Water and sanitation have no glide path: 10 % from 1 January 2024
(art. 247-XXXXI-A). Before 2024 no transitional rate exists, and
`tva_taux_transitoire` returns 0 rather than an invented value.

### What the TVA module does not do

It does **not** choose a rate from a product description. A quote-backed
Article 99 catalog is available for the consolidated editions 2007, 2010, 2014,
2018, 2021, 2024 and 2026, but each entry must be requested by its exact edition
year and item ID. The returned quote, rate, item ID, corpus path and any source
endnote labels let a caller inspect a documented clause; the package does not
classify arbitrary products or select an edition for an effective date. Some
catalog quotes cover combined clauses and are returned whole.

The catalog has **no 2004 consolidated snapshot**. Snapshot labels are not
continuous effective-date ranges, so they cannot establish which clause
applies between editions. The 2004 gap and the absence of continuous validity
remain blockers for issue [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6);
the corpus work is tracked in
[morocco-holy-graph#80](https://github.com/MasterSwords1/morocco-holy-graph/issues/80).

To enumerate the documented clauses for an exact snapshot, then retrieve one
item directly:

```python
from openfisca_morocco.tva_article99 import (
    get_article_99_item,
    list_article_99_items,
)

items = list_article_99_items(2024)
print([(item.item_id, item.rate) for item in items])
item = get_article_99_item(2024, "2024-art99-general-20pct")
print(item.rate)  # "20%"
print(item.quote)  # verbatim clause from the 2024 edition
print(item.corpus_file)  # source text path in morocco-holy-graph
print(item.source_endnote_labels)  # tuple of catalog labels, or None
```

`list_article_99_items` preserves the source order and returns an immutable
tuple. The package-local catalog is
`openfisca_morocco/data/tva_article99_catalog.json`.
It retains source quotes and provenance but omits the source's one-day
`as_of`, `valid_from` and `valid_to` snapshot markers so they cannot be mistaken
for continuous validity.

## Provenance

Every modelled figure is traceable to a published text, and every input variable
names the article it comes from.

| Piece | Source |
|---|---|
| Code Général des Impôts (arts. 1–248) | Loi n° 43-06, Dahir n° 1-06-232 of 31 December 2006, *Bulletin Officiel* n° 5487 bis of 31 December 2006, pp. 4153–4210 |
| Art. 73-I scale in force in 2025 | Loi de finances n° 60-24 for the 2025 budget year, Dahir n° 1-24-65 of 13 December 2024, *Bulletin Officiel* n° 7362 bis of 19 December 2024 |
| Arts. 59 and 74 figures | CGI as encoded in the validated Catala model of the `morocco-holy-graph` corpus (`laws/ma_tax_law/catala/cgi_ir.catala_fr`) and cross-checked against its tests (`laws/ma_tax_law/tests/test_catala_tax.py`) |
| TVA rates 2004–2026 | `morocco-holy-graph`, verified dataset `laws/ma_tax_law/data/tva_rate_history.json` (PR #81), where every rate carries a literal quote from the finance-law text layer; cross-checked by `openfisca_morocco/tests/test_tva_taux.py` |
| Article 99 catalog entries | Consolidated snapshots in `laws/ma_tax_law/data/consolidated/tva_article_lists.json`; the package artifact preserves each selected item's quote, rate, ID and corpus path for snapshots 2007, 2010, 2014, 2018, 2021, 2024 and 2026, with no 2004 snapshot and no continuous effective-date claim |
| TVA declaration arithmetic | CGI arts. 98, 99, 101, 104 and 247-XXXXI as encoded in the validated Catala model `laws/ma_tax_law/catala/cgi_tva.catala_fr` and its test `test_tva_multi_rate_and_deductions` (257 000 / 150 000 / 107 000) |
| Parameter values | `metadata.reference` (title + href) on each parameter, or on each of its dated values, under `openfisca_morocco/parameters/` — enforced by `openfisca_morocco/tests/test_parameter_provenance.py` |

The corpus is the source of truth for this package: figures are taken from
`morocco-holy-graph`, not from memory or from unversioned web pages. Where the
corpus itself has not yet captured the controlling text (for example the
pre-2025 versions of articles 59 and 73), the limitation is stated below rather
than guessed.

## Limitations

Stated plainly, because they determine what you may conclude from a simulation:

- **Salarial income only (IR).** Professional, rental, capital and foreign
  income are not modelled, so this is not a complete IR. See issue
  [#15](https://github.com/MasterSwords1/openfisca-morocco/issues/15).
- **Annual periods only (IR).** The IR scale is annual; monthly withholding
  (retenue à la source) is not modelled. See issue
  [#9](https://github.com/MasterSwords1/openfisca-morocco/issues/9).
- **IR from 2025 only.** Earlier IR scales, rates and thresholds are not
  encoded, so an IR simulation for 2024 or before returns the 2025 law or a
  default value — do not use it for historical IR work.
- **Article 99 lookup is snapshot-scoped.** The package supports exact catalog
  IDs for editions 2007, 2010, 2014, 2018, 2021, 2024 and 2026. It does not
  classify product descriptions, interpolate between editions or provide a
  2004 snapshot; #6 remains open until the historical gap and effective-date
  coverage are resolved. See the TVA section above and
  [morocco-holy-graph#80](https://github.com/MasterSwords1/morocco-holy-graph/issues/80).
- **TVA before 2004 is not modelled.** The rate dataset starts on 1 January
  2004; before that date the parameters return the 2004 regime.
- **No import or export VAT, no registration duties, no specific rates**
  (article 100: wine, gold and silver). See issue
  [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6).
- **Contributions are an input, not a computation.** `cotisations_sociales_obligatoires`
  must be supplied; CNSS/AMO rates and ceilings are not modelled yet. See issue
  [#5](https://github.com/MasterSwords1/openfisca-morocco/issues/5).
- **No benefits.** Allocations familiales, aide sociale directe and the rest of
  the transfer system are absent. See issues
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
# 72 passed
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

For VAT, the entity is the company and the period is a month:

```python
simulation = SimulationBuilder().build_from_dict(
    tax_benefit_system,
    {
        "persons": {"Gerant": {}},
        "companies": {
            "Entreprise": {
                "membres": ["Gerant"],
                "chiffre_affaires_taux_normal": {"2024-06": 1_000_000},
                "chiffre_affaires_taux_reduit_10": {"2024-06": 500_000},
                "tva_deductible_charges": {"2024-06": 120_000},
                "tva_deductible_immobilisations": {"2024-06": 30_000},
            }
        },
    },
)

print(simulation.calculate("tva_collectee_totale", "2024-06"))  # [250000.]
print(simulation.calculate("tva_deductible_autorisee", "2024-06"))  # [150000.]
print(simulation.calculate("tva_nette_a_payer", "2024-06"))  # [100000.]
```

`membres` is the single role `Company` declares; it only records that a person
is attached to the company, and no formula reads it.

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

The YAML tests in `openfisca_morocco/tests/impot_revenu.yaml` and
`openfisca_morocco/tests/tva.yaml` document the expected law at the boundaries
(each bracket, each dated rate, each transitional step), and
`openfisca_morocco/tests/age.yaml` covers the `age` formula.
`openfisca_morocco/tests/test_tva_taux.py` checks every declared TVA rate and
period against the verified corpus dataset, and
`openfisca_morocco/tests/test_tva_simulation.py` checks the public simulation
path with a `Company`.

## Repository layout

```
openfisca_morocco/
├── entities.py                 # Household (adults/children), Company, Person
├── tva_article99.py            # snapshot item listing and exact lookup
├── data/
│   └── tva_article99_catalog.json # quoted Article 99 snapshots and provenance
├── parameters/
│   ├── impot_revenu/           # barème, frais professionnels, charges de famille
│   └── tva/                    # dated rates 2004-2026, transitional schedules
├── variables/
│   ├── impot_revenu.py         # the IR pipeline
│   ├── tva.py                  # the TVA declaration
│   └── demographics.py         # birth, age
├── situation_examples/
│   └── salarie.json            # one salaried taxpayer, used by the Web API spec
└── tests/                      # YAML and Python tests
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
