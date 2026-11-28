# Development and usage

Installation, Python and Web API usage, period conventions, examples,
repository layout, roadmap and release process. See the [README](../README.md)
for the short overview and [coverage](coverage.md) for the modelled scope.

## Install

Requires Python 3.11 or later (CI runs 3.13) and
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
# 607 passed (of which 387 pytest; 602/382 without the corpus)
```

The five TVA corpus tests run when `../morocco-holy-graph` exists or
`MOROCCO_HOLY_GRAPH` points to it; a bare clone skips them and reports
602 OpenFisca / 382 pytest tests.

Once published, installation will be `uv add openfisca-morocco`.

## Use it

### From Python

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tax_benefit_system = CountryTaxBenefitSystem()
monthly_pay = {f"2025-{month:02d}": 10_000 for month in range(1, 13)}

simulation = SimulationBuilder().build_from_dict(
    tax_benefit_system,
    {
        "persons": {
            "Salarie": {
                "salaire_brut_global": monthly_pay,
                "salaire_brut": monthly_pay,
                "nombre_personnes_a_charge": {"2025": 0},
            }
        },
        "households": {"_": {"adults": ["Salarie"]}},
    },
)

print(simulation.calculate("salaire_brut_global", "2025-01"))  # [10000.]
print(simulation.calculate_add("salaire_brut_global", "2025"))  # [120000.]
print(simulation.calculate("impot_sur_le_revenu", "2025").round(2))  # [7218.72]

# Payroll withholding for one month (from 2016)
print(
    simulation.calculate("ir_prelevement_source_mensuel", "2025-01").round(2)
)  # [601.56]
print(simulation.calculate("salaire_net_a_payer", "2025-01").round(2))  # [8903.64]
```

All monetary amounts are in Moroccan dirhams (MAD). Monthly salary inputs
are summed over the requested calendar year; the annual expense thresholds,
caps, tax brackets and family deduction are applied once to that total. The
monthly withholding variables are a separate payroll calculation: the monthly
barème and prorated deductions apply to the month's pay, and they do not
change the annual `impot_sur_le_revenu`.

### Period conventions

The periods of every variable family are:

| Variables | Definition period | Convention |
|---|---|---|
| `birth` | `ETERNITY` | A fixed birth date. |
| `age` | `MONTH` | Age at the start of the month, in completed years. |
| `salaire_brut_global`, `elements_exoneres` | `MONTH` | Gross remuneration (computed as `salaire_de_base + prime_anciennete_legale` unless supplied directly) and exempt elements, used for IR. |
| `salaire_brut` | `MONTH` | The salary base subject to CNSS/AMO contributions for that month. |
| All other variables in `variables/cotisations_sociales.py` | `MONTH` | Monthly employee/employer contributions and employer cost; CNSS ceilings apply separately each month. |
| `cotisations_sociales_obligatoires` | `YEAR` | Sum of monthly employee contributions, or an explicit annual deduction override (including other mandatory contributions). |
| `nombre_personnes_a_charge` | `YEAR` | Count of spouse and dependent children used for the annual IR deduction; never divided by twelve. |
| `salaire_brut_imposable`, `frais_professionnels`, `salaire_net_imposable`, `ir_brut`, `deduction_charges_famille`, `impot_sur_le_revenu` | `YEAR` | Annual IR bases, deductions and tax. |
| `salaire_brut_imposable_mensuel`, `frais_professionnels_mensuel`, `salaire_net_imposable_mensuel`, `ir_brut_mensuel`, `deduction_charges_famille_mensuelle`, `ir_prelevement_source_mensuel`, `salaire_net_a_payer` | `MONTH` | Payroll withholding from 2016: the annual barème, expense ceiling and family amount are prorated to the month. |
| `salaire_de_base`, `anciennete_annees`, `licenciement_sans_faute` | `MONTH` | Labour-code inputs: article 353 base, seniority in years and non-fault dismissal flag. |
| `prime_anciennete_legale`, `indemnite_licenciement_legale`, `salaire_conforme_smig` | `MONTH` | Labour-code outputs from July 2004: seniority bonus, statutory severance and SMIG compliance. |
| `nombre_enfants`, `allocations_familiales` | `MONTH` | Eligible child count and monthly allowance. |
| `enfant_scolarise_cnss`, `enfant_apprenti_cnss`, `enfant_etudes_superieures_cnss`, `enfant_handicape_cnss`, `enfant_handicape_sans_revenu_cnss` | `MONTH` | CNSS eligibility flags; declare them for every month they apply, because a one-month value does not carry over. |
| Monthly variables in `variables/tva.py` | `MONTH` | Company declaration amounts, physical quantities, category choices and calculated TVA for that month. |
| Annual TVA turnover inputs, `chiffre_affaires_taxable_annuel`, `chiffre_affaires_total_declare`, `prorata_deduction_calcule` | `YEAR` | Calendar-year turnover detail and Article 104-I prorata; the prior year's prorata applies to monthly deductions. |

The monthly withholding subtracts `cotisations_sociales_salarie`, which is
computed from `salaire_brut`. Supply both gross bases for a complete payroll
estimate; if `salaire_brut` is omitted, contributions are zero and the
withholding is overstated, while `salaire_net_a_payer` is zero because it has
no contribution base to start from.

The two gross salary inputs are **distinct bases**. `salaire_brut_global`
feeds IR; `salaire_brut` feeds CNSS/AMO. Supply both when both apply, as in the
example above. `salaire_brut_global` is also computed as `salaire_de_base`
plus the legal seniority bonus when those inputs are used; supplying
`salaire_brut_global` directly overrides that formula, so include the bonus
yourself in that case. The bonus is added to `salaire_brut_global` only; add it
to `salaire_brut` as well when it is subject to CNSS/AMO. Supplying only `salaire_brut_global` does not infer contribution
liability. Without an annual override, `cotisations_sociales_obligatoires`
sums the contributions calculated from `salaire_brut`.

**Compatibility with annual inputs:** `salaire_brut_global`,
`salaire_de_base`, `elements_exoneres` and `salaire_brut` use
`set_input_divide_by_period`.
For example, `"salaire_brut_global": {"2025": 120_000}` means an **annual
total** distributed over twelve months (10,000 each), not 120,000 per month.
Quarter or multi-month totals are likewise distributed over their months.
When monthly details and a larger-period total are supplied together, the
larger-period total's remainder is divided over the unspecified months.
Supply actual monthly contribution salaries when they vary: splitting an
annual total evenly can change the effect of the monthly CNSS ceiling.

The existing annual YAML scenarios and the bundled `salarie.json` example
remain valid without migration. Python callers that previously read
`simulation.calculate("salaire_brut_global", "2025")` (or
`elements_exoneres`) should now use `calculate_add(..., "2025")` for an
annual total, or `calculate(..., "2025-01")` for one month. Annual IR outputs
still use `calculate(..., "2025")`. Missing monthly salary inputs default
to zero; entering one month does not repeat it across the year.

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

### Situation examples

`openfisca_morocco/situation_examples/` holds ready-to-serve situations. Each
file requests its outputs, so the Web API computes them:

- `salarie.json` — the original single-salaried example (25,800 DH of IR);
- `salarie_exonere.json` — below the exemption threshold, IR 0;
- `salarie_impose.json` — above the threshold, with one dependent;
- `couple_avec_enfants.json` — two earners and two children;
- `haut_revenu.json` — a high earner at the top bracket;
- `cout_employeur.json` — salary, CNSS/AMO and employer cost;
- `menage_asd.json` — a household receiving the direct social support.

Every file is simulated by `tests/situations/`.

### Reform examples

```python
from openfisca_morocco import CountryTaxBenefitSystem
from openfisca_morocco.reforms import ReformeBaremeIR, ReformeTVA

baseline = CountryTaxBenefitSystem()
old_scale = ReformeBaremeIR(baseline)  # pre-2025 IR scale
vat_18 = ReformeTVA(baseline)  # normal VAT rate at 18 % from 2025
```

Both are tested against the baseline in `tests/reforms/`.

### Run the tests

```sh
make test          # YAML and Python tests under openfisca_morocco/tests/
uv run pre-commit run --all-files
```

The YAML and Python tests in `openfisca_morocco/tests/impot_revenu.yaml`,
`openfisca_morocco/tests/impot_societes.yaml`,
`openfisca_morocco/tests/cotisations_sociales.yaml`,
`openfisca_morocco/tests/allocations_familiales.yaml`,
`openfisca_morocco/tests/aide_sociale_directe.yaml`,
`openfisca_morocco/tests/impot_revenu_categories.yaml`,
`openfisca_morocco/tests/ir_regimes_professionnels.yaml`,
`openfisca_morocco/tests/ir_deductions_globales.yaml`,
`openfisca_morocco/tests/ir_patrimoine.yaml`,
`openfisca_morocco/tests/enregistrement.yaml`,
`openfisca_morocco/tests/test_ir_categories_gating.py`,
`openfisca_morocco/tests/test_ir_parameter_tables.py`,
`openfisca_morocco/tests/test_ir_deductions_election.py` and
`openfisca_morocco/tests/tva.yaml` document the expected law at the boundaries
(each bracket, each ceiling, each dated rate, each transitional step).
`aide_sociale_directe` is completed by
`aide_rentree_scolaire.yaml`, `aide_speciale_enfants_places.yaml` and
`prime_exceptionnelle_asd.yaml` for the three related allowances, with
`test_prime_exceptionnelle_asd.py` running the twelve-month consumption
sequences. `openfisca_morocco/tests/age.yaml` covers the `age` formula.
`openfisca_morocco/tests/test_cotisations_sociales.py` checks CNSS and AMO
contributions across salary levels and validates integration into the annual IR,
`openfisca_morocco/tests/test_ir_periods.py` checks monthly salary aggregation,
varying pay, partial years, annual input compatibility and monthly CNSS ceilings,
`openfisca_morocco/tests/test_tva_taux.py` checks every declared TVA rate and
period against the verified corpus dataset,
`openfisca_morocco/tests/test_tva_simulation.py` checks the public simulation
path with a `Company`, and
`openfisca_morocco/tests/test_tva_article99.py`,
`openfisca_morocco/tests/test_tva_article101.py`, and
`openfisca_morocco/tests/test_tva_article15.py` check snapshot item lookups,
source-order preservation and quote provenance across all catalogs.
`test_tva_article99.py` additionally checks the effective-date contract: proven
rows carry a method, an instrument and a matching hash, bracketed rows carry no
date, a renumber is not a repeal, a rate move is not a repeal, and a date query
never reaches an undated row.

`openfisca_morocco/tests/situations/` mirrors the bundled examples for the IR,
CNSS and ASD families, and `openfisca_morocco/tests/reforms/` checks both
reforms against the baseline.

## Repository layout

```
openfisca_morocco/
├── entities.py                 # Household (adults/children), Company, Person
├── tva_article15.py            # pre-CGI Loi 30-85 Article 15 snapshots
├── tva_article99.py            # snapshot item listing, exact lookup and dated segments
├── tva_article91_92.py         # exemption snapshot listing and exact lookup
├── tva_article100.py           # specific-rate periods and tax calculation
├── tva_article101.py           # fixed 2006 LAR Article 101 snapshot
├── data/
│   ├── tva_article15_catalog.json # historical Article 15 catalog and audit
│   ├── tva_article91_92_catalog.json # quoted exemption snapshots
│   ├── tva_article100_rates.json # specific-rate periods and amendments
│   ├── tva_article99_catalog.json # quoted Article 99 snapshots, provenance and effective dates
│   └── tva_lar_2006_article101.json # separate LAR Article 101 snapshot
├── parameters/
│   ├── impot_revenu/           # barème, frais professionnels, charges de famille
│   ├── prestations_sociales/   # cotisations CNSS, AMO, allocations familiales, ASD
│   ├── enregistrement/         # registration and conservation duties
│   ├── impot_societes/         # IS rates and cotisation minimale
│   └── tva/                    # dated rates 2004-2026, transitional schedules
├── variables/
│   ├── aide_sociale_directe.py # ASD monthly household estimate
│   ├── aide_rentree_scolaire.py # ASD September school-return allowance
│   ├── aide_speciale_enfants_places.py # ASD special allowance for placed children
│   ├── prime_exceptionnelle_asd.py # ASD exceptional allowance after a CNSS declaration
│   ├── allocations_familiales.py # CNSS family allowances
│   ├── cotisations_sociales.py # CNSS and AMO contributions (employee & employer)
│   ├── enregistrement.py       # registration and conservation duties
│   ├── impot_revenu.py         # the IR pipeline
│   ├── ir_deductions_globales.py # article 28 deductions and rental option
│   ├── ir_patrimoine.py        # property, foreign capital and foreign income
│   ├── ir_regimes_professionnels.py # simplified, CPU, auto-entrepreneur and net-réel regimes
│   ├── impot_societes.py       # IS and cotisation minimale
│   ├── tva.py                  # monthly company TVA declaration
│   └── demographics.py         # birth, age
├── reforms/
│   ├── reforme_bareme_ir.py    # pre-2025 IR scale
│   └── reforme_tva.py          # normal VAT rate at 18 %
├── situation_examples/         # ready-to-post Web API situations
│   ├── salarie.json
│   ├── salarie_exonere.json
│   ├── salarie_impose.json
│   ├── couple_avec_enfants.json
│   ├── haut_revenu.json
│   ├── cout_employeur.json
│   └── menage_asd.json
└── tests/                      # YAML and Python tests
    ├── situations/             # the example families
    └── reforms/                # reform deltas vs baseline
scripts/
├── build_article99_attribution.py     # Article 99 effective dates + sub-items
└── build_tva_article91_92_catalog.py  # verbatim Article 91/92 projection
```

## Roadmap

The path to a complete, usable package — IR on all income categories,
CNSS/AMO contributions, TVA, family allowances, direct social support,
realistic situation and reform examples, PyPI publication — is tracked in the
[v1.0 milestone](https://github.com/MasterSwords1/openfisca-morocco/milestone/1).
Each issue states its goal, scope, acceptance criteria and the issues it depends
on.

## Publishing a release

The first public release is postponed; see the
[release issue](https://github.com/MasterSwords1/openfisca-morocco/issues/12).
Resolve the release blockers with the maintainers before changing repository
visibility or publishing.

1. Review the full Git history for secrets and check the licence and template
   attribution before making the repository public.
2. Configure PyPI Trusted Publishing for this repository, the `cd.yaml`
   workflow, and the `pypi` GitHub environment.
3. Once the release commit is on public `main`, run **Continuous deployment**
   from the Actions tab on that branch. Verify that the PyPI release is
   available and the Git tag matching `pyproject.toml` points to the release
   commit.
4. In a new project outside any checkout, verify installation from PyPI.

   ```sh
   uv init --bare
   uv add openfisca-morocco   # pin the published version if needed
   scenarios="$(uv run python -c 'from pathlib import Path; import openfisca_morocco; print(Path(openfisca_morocco.__file__).parent / "tests")')"
   uv run openfisca test --country-package openfisca_morocco "$scenarios"
   ```

5. After publication, add the `openfisca` topic to the repository, enable the
   PyPI badge below, and submit Morocco (`MA`) to the
   [OpenFisca packages listing](https://openfisca.org/en/packages/).

<!-- Enable after the first PyPI release:
[![PyPI](https://img.shields.io/pypi/v/openfisca-morocco)](https://pypi.org/project/openfisca-morocco/)
-->

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), open a pull request against `main`, and
follow the version and changelog rules described there.

## Licence

AGPL-3.0-or-later. See [LICENSE](../LICENSE).
