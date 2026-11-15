
## 0.5.0 - [#7](https://github.com/MasterSwords1/openfisca-morocco/issues/7)

* Tax and benefit system evolution.
* Impacted periods: 2019-07-01 onwards.
* Impacted areas:
  - `parameters.prestations_sociales.allocations_familiales` (new CNSS family allowances grid).
  - `variables.allocations_familiales` (new variables `nombre_enfants` and `allocations_familiales` on `Household`).
  - `tests` (new YAML and Python tests for CNSS family allowances).
* Details:
  - Model contributory CNSS family allowances (*allocations familiales*) on `Household` with monthly periodicity (`MONTH`), grounded in `morocco-holy-graph` module `ma_social_protection` (CSOC, PR #95) and primary legal instruments:
    - Dahir portant loi n° 1-72-184 du 27 juillet 1972 (articles 38 à 41).
    - Décret n° 2-19-461 du 19 juillet 2019 fixant les montants mensuels par enfant.
  - Implement statutory parameter grid:
    - `plafond_enfants`: statutory maximum of 6 eligible children per insured.
    - `montant_enfants_1_a_3`: 300 MAD / month per child for ranks 1 to 3.
    - `montant_enfants_4_a_6`: 36 MAD / month per child for ranks 4 to 6.
  - Implement variables:
    - `nombre_enfants`: computed from `household.nb_persons(Household.CHILD)` by default, or accept direct input overrides.
    - `allocations_familiales`: computed for `Household` over `MONTH` using the statutory tiered scale and legal 6-child cap.
  - Tested across 0, 1, 2, 3, 4, 6, 8, and 10 children scenarios in YAML (`allocations_familiales.yaml`) and pytest (`test_allocations_familiales.py`), including salary-independence and input override validation.

## 0.4.0 - [#5](https://github.com/MasterSwords1/openfisca-morocco/issues/5)

* Tax and benefit system evolution.
* Impacted periods: all.
* Impacted areas:
  - `parameters.prestations_sociales.cotisations` (new CNSS and AMO parameters).
  - `variables.cotisations_sociales` (new mandatory social contributions and employer charges).
  - `variables.impot_revenu` (formula for `cotisations_sociales_obligatoires`).
  - `tests` (new YAML and Python tests for social contributions).
* Details:
  - Model mandatory Moroccan social security contributions (CNSS) and mandatory health insurance (AMO) on `Person` with monthly periodicity (`MONTH`), grounded in `morocco-holy-graph` module `ma_social_protection` (CSOC, PR #95) and primary statutes:
    - Dahir portant loi n° 1-72-184 (sécurité sociale) et Décret n° 2-02-175 fixant le plafond des rémunérations soumises à cotisation CNSS à 6 000 MAD par mois.
    - Loi n° 03-14 et Décret n° 2-14-540 instituant l'indemnité pour perte d'emploi (IPE).
    - Loi n° 65-00 portant Code de la Couverture Médicale de Base et Décret n° 2-05-734 modifié par Décret n° 2-14-707 (AMO).
    - Prestations familiales (6,40 % patronale, Décret n° 2-19-461) et taxe de formation professionnelle (1,60 % patronale, Loi n° 30-97).
  - Add monthly variables: `salaire_brut`, `cotisation_cnss_salarie`, `cotisation_amo_salarie`, `cotisations_sociales_salarie`, `cotisation_cnss_employeur`, `cotisation_amo_employeur`, `cotisations_sociales_employeur`, and `cout_employeur`.
  - Provide a formula for `cotisations_sociales_obligatoires` on `YEAR` in the IR pipeline that aggregates monthly employee social contributions (CNSS + AMO), allowing gross-to-net salary and income tax simulations without requiring hand-entered social contributions.
  - Verified across monthly income levels below, at, and above the 6 000 MAD ceiling in `tests/cotisations_sociales.yaml` and `tests/test_cotisations_sociales.py`.

## 0.3.0 - [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6)

* Tax and benefit system evolution.
* Impacted periods: 2004-01-01 onwards.
* Impacted areas:
  - `entities` (new `Company` entity).
  - `parameters.tva` (new).
  - `variables.tva` (new).
  - `tva_article99` (snapshot-scoped Article 99 catalog listing and lookup).
  - `tva_article91_92` (snapshot-scoped exemption catalog listing and lookup).
  - `tva_article100` (date-scoped specific-rate history and tax calculation).
  - `tva_article15` (separate pre-CGI historical snapshot lookup).
  - `data` (Article 91/92 and 99 snapshots, Article 100 effective periods, and quote provenance).
  - `tests` (new YAML and Python tests).
* Details:
  - Add the `Company` entity and the monthly TVA declaration of CGI articles 98, 99, 101, 104 and 247-XXXXI: collectée per rate, deductible after prorata, net payable and carry-forward credit, plus `chiffre_affaires_taux_abroge` which isolates revenue declared on an abrogated rate.
  - Encode dated rates 2004-2026 from the verified corpus dataset (`morocco-holy-graph` PR #81): 20 / 14 / 10 / 7 % until 31 December 2023, then 20 / 10 % only. The 14 % and 7 % brackets stay declared for historical simulation but carry `en_vigueur = 0` from 2024-01-01, so they can never be applied silently.
  - Encode the seven transitional schedules of article 247-XXXXI (electricity 16/18/20, electricity meter 11/15/20, renewable electricity 12/10, sugar 8/9/10, transport excluding urban and road haulage 16/18/20, urban and road transport 13/12/10, insurance brokers 12/10), selected by the `tva_operation_transitoire` input. No transitional rate is declared before 2024: before that date the operations fell under the general rates.
  - Give `Company` a single `membres` role, because OpenFisca cannot instantiate a group entity without one; no formula reads it.
  - The rate figures are checked against the corpus by `tests/test_tva_taux.py`, and the declaration arithmetic reproduces the validated Catala test of the corpus (257 000 / 150 000 / 107 000) in `tests/tva.yaml` and `tests/test_tva_simulation.py`.
  - Add source-ordered Article 99 item listing and exact item lookup for consolidated snapshots 2007, 2010, 2014, 2018, 2021, 2024 and 2026. Each result retains its edition, item ID, rate, verbatim quote, corpus source path, parent context and available quote-backed citations to finance laws. The packaged quotes now exclude unrelated page-footer notes; a footer note is not assigned to a nearby item by position alone. Product descriptions are not classified, snapshot labels do not assert continuous validity, and the missing 2004 CGI Article 99 edition and broader history gaps remain open for issue #6 and `morocco-holy-graph#80`.
  - Add an explicit Article 99 item-ID turnover aggregator for callers that have selected a legal category. It sums bases by the rate documented in one snapshot and rejects items that cite Article 247 transitional schedules.
  - Add a separately named, fixed-snapshot API for the complete 2006 LAR Article 101 list. It retains all 38 quotes, rates, conditions, deduction treatment, source URLs and hashes, and the LAR Articles 212/213 date and repeal citations. This is not CGI Article 99 and does not fill the missing 2004–2005 Article 15 lists or claim continuous validity. The snapshot also names the enacting Bulletin officiel n° 5382 bis as a verified live primary source (fetched 2026-11-14, byte-identical SHA-256) and records that the 2006 text numbers the rate articles 99/100/101/102 where the 2007 and later editions number them 97/98/99/100, so a 2006 Article 100 is not the article exposed by `tva_article100`.
  - Add a separate API and packaged catalog for Loi n° 30-85 Article 15 lists as of 1 January 2004 (40 items) and 1 January 2005 (41 items), retaining source quotes, rates, deduction treatment, conditions, item IDs, available DGI endnotes, Gazette amendment citations and reviewed source-chain evidence. This pre-CGI data is independent of Article 99 and LAR Article 101 and makes no continuous-validity or product-classification claim. The available-source review found no additional non-finance Article 15 amendment, but the 2002 DGI baseline PDF is not pinned and the incomplete Gazette run prevents an exhaustive negative.
  - Add exact Article 91 and 92 exemption lookups for consolidated snapshots 2007, 2010, 2014, 2018, 2021, 2024 and 2026. Preserve quoted clauses and deduction rights while removing snapshot-date markers that could be mistaken for continuous validity.
  - Add CGI Article 100 per-unit rates for 2007–2019, including the 2011 metal-rate change and the 2020 repeal. Calculate monthly output TVA from explicitly supplied hectolitres/grams, include it in the company declaration total, and flag non-zero quantities outside the verified period.

## 0.2.2 - [#4](https://github.com/MasterSwords1/openfisca-morocco/issues/4)

* Tax and benefit system evolution.
* Impacted periods: all.
* Impacted areas:
  - `parameters` (provenance gate).
* Details:
  - Make the provenance gate match OpenFisca's semantics: `metadata` is not inherited, so a reference declared on a parent node is invisible on its children at runtime. Each leaf parameter must now carry its own `metadata.reference`, or attach one to each dated value (`values: {2025-01-01: {value: ..., metadata: {reference: ...}}}`).
  - A scale stays one legal object: a reference on the scale covers its brackets, and only an unsourced scale falls back to per-bracket checks.
  - Move the article 59 and article 74 references from the file roots to the four and two leaf parameters that actually carry the figures, so `parameters(...).impot_revenu.frais_professionnels.plafond.metadata` now names its article.
  - Accept the date-keyed reference form used when a figure's source changes over time.

## 0.2.1 - [#4](https://github.com/MasterSwords1/openfisca-morocco/issues/4)

* Tax and benefit system evolution.
* Impacted periods: all.
* Impacted areas:
  - `parameters` (provenance gate).
* Details:
  - Add `tests/test_parameter_provenance.py`: every parameter value must resolve a `metadata.reference` (title + href), declared on the value or on its closest ancestor. A parameter file with an untraceable number now fails `make test` and therefore CI.
  - The gate loads each file with the OpenFisca parameter loader, so a malformed parameter file fails here as well.

## 0.2.0 - [#16](https://github.com/MasterSwords1/openfisca-morocco/pull/16)

* Tax and benefit system evolution.
* Impacted periods: all.
* Impacted areas:
  - `benefits` (removed).
  - `housing` (removed).
  - `income` (removed).
  - `stats` (removed).
  - `taxes` (removed).
* Details:
  - Remove the country-template demo legislation, none of which modelled Moroccan law: `basic_income`, `housing_allowance`, `parenting_allowance`, `meal_price`, `swimming_pool_access`, `pension`, `housing_tax`, `income_tax`, `social_security_contribution`, `disposable_income`, `total_benefits`, `total_taxes`, the demo housing and income inputs (`rent`, `accommodation_size`, `housing_occupancy_status`, `postal_code`, `salary`, `capital_returns`) and the demo parameters under `benefits`, `taxes` and `general`.
  - The package now only models Moroccan legislation: the impôt sur le revenu of CGI articles 56 to 74, as reformed by the Loi de Finances 2025.
  - Remove the demo reforms and their tests; real Moroccan reform examples are tracked separately.
  - Replace the demo situation examples with a single Moroccan salaried example, used by the OpenFisca Web API specification.
  - Keep `birth` and `age` as factual demographics (no legal reference), since Moroccan age-based provisions will need them.

## 0.1.0 - [#1](https://github.com/MasterSwords1/openfisca-morocco/pull/1)

* Tax and benefit system evolution.
* Impacted periods: from 2025-01-01.
* Impacted areas:
  - `taxes` (impôt sur le revenu).
* Details:
  - Add the progressive annual IR barème of CGI article 73-I, as reformed by the Loi de Finances 2025 (0 / 10 / 20 / 30 / 34 / 37 %).
  - Add the article 59 professional-expense deduction (35 % up to 78 000 DH of gross pay, 25 % above, capped at 35 000 DH).
  - Add the article 74 family-charge deduction (500 DH per dependent, maximum 6).
  - Derive `salaire_net_imposable` and the net `impot_sur_le_revenu` from those inputs.

## 0.0.1 - [#0](https://github.com/openfisca/country-template/pull/0)

* Tax and benefit system evolution.
* Impacted periods: all.
* Impacted areas:
  - `benefits`.
  - `demographics`.
  - `housing`.
  - `income`.
  - `stats`.
  - `taxes`.
* Details:
  - Import model from template
