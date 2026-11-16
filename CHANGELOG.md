## 0.8.0 - [#15](https://github.com/MasterSwords1/openfisca-morocco/issues/15)

* Tax and benefit system evolution.
* Impacted periods: professional income from 2025-01-01; rental and capital
  categories from 2026-01-01; salarial IR from 2025-01-01.
* Impacted areas: `variables.impot_revenu`,
  `parameters.impot_revenu.revenus_categories`,
  `parameters.impot_revenu.deduction_charges_famille`.
* Details:
  - Add professional, rental and capital income to the global IR base. The
    professional net profit is an input; rental income applies the 40 %
    abatement of article 64-II and the 10 % / 15 % withholding of article
    73-II, imputed against the tax due without restitution.
  - Encode the liberatory capital rates of article 73-II: dividends 11,25 % in 2026
    (10 % from 2027), fixed-income interest 30 %, listed gains 15 %, unlisted 20 %.
  - Apply the barème to `revenu_global_imposable` and add
    `impot_sur_le_revenu_menage`, the sum of individual liabilities, since IR is
    assessed per taxpayer.
  - Raise the 2026 family deduction to 600 DH per dependent (Loi de finances
    n° 50-25, article 7), retaining the 2025 value.
  - Rental and capital rules are gated from 2026 and raise on earlier inputs;
    professional income applies from 2025.
  - Document the article coverage and the unmodelled regimes in
    `docs/impot-revenu-categories.md`.


## 0.7.0 - [#24](https://github.com/MasterSwords1/openfisca-morocco/pull/24)

* Tax and benefit system evolution.
* Impacted periods: Salary input conventions for all periods; IR calculations
  remain supported from 2025-01-01 onwards.
* Impacted areas: `variables.impot_revenu`, `variables.cotisations_sociales`.
* Details:
  - Enter `salaire_brut_global` and `elements_exoneres` as monthly amounts.
    The IR pipeline sums these amounts before applying annual expense
    deductions, caps, tax brackets and family deductions.
  - Annual totals remain accepted for both inputs and for the monthly CNSS/AMO
    salary base `salaire_brut`, using `set_input_divide_by_period`. Existing
    annual YAML scenarios and the bundled API example retain their results.
  - To read an annual gross-pay or exempt-remuneration total in Python, replace
    `calculate(variable, "2025")` with `calculate_add(variable, "2025")`.
    Annual IR outputs and annual contribution overrides are unchanged.
  - Document every variable family's period, the distinct IR and CNSS/AMO
    salary bases, missing-month defaults and the limits of evenly distributing
    contribution salaries. Monthly withholding is still not modelled.

## 0.6.0 - [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6)

* Tax and benefit system evolution.
* Impacted periods: 2007-01-01 onwards (Article 99 effective dates).
* Impacted areas:
  - `tva_article99` (dated segments, effective-date API, date-scoped aggregation, nested `Article99SubItem` rows).
  - `data.tva_article99_catalog` (schema version 2, hoisted instruments, per-row `effective_attribution`, `subitems`).
  - `tva_article91_92` (two-level itemization, `abrogated` status, cross-article handoff test for the 2021 solar water heater move).
  - `data.tva_article91_92_catalog` (schema version 2, verbatim projection: 606 items plus 603 sub-items).
  - `scripts.build_article99_attribution` and `scripts.build_tva_article91_92_catalog` (generators, both `--check`-able).
  - `tests` (Article 99 acceptance tests and evidence guards, Article 91/92 itemization tests, and four provenance regressions).
* Details:
  - Give every Article 99 row an `effective_attribution`: the dated rate segment it belongs to, with a start and an end that are dated **independently**. A boundary is `proven` only when a primary source names the instrument; it then carries the instrument, the witness artifact, a SHA-256 labelled by artifact kind (`pdf_sha256` vs `text_sha256`) and a verbatim quote. Otherwise it is `bracketed`, carries a machine-readable `reason` and a `validity_bracket`, and carries **no date at all**.
  - Attribution is per boundary, not per row. A renumber creates no boundary, a rate move is `superseded` rather than `repealed`, and a removal that lands in another article is `exempted` with a `successor_article`.
  - Derive the dates mechanically in `scripts/build_article99_attribution.py`: the baseline is the original enactment (Loi 43-06 art. 5); a later boundary is dated from the row's own consolidated endnote when exactly one in-interval instrument is named; an *introduction* may be dated from a verbatim reproduction in exactly one in-interval finance-law transcription. These routes prove 299 of 420 rows (71,2 %); the 121 others stay bracketed with `repeal_not_witnessed` (109), `ambiguous_instruments` (7) or `introduction_not_witnessed` (6). No date is guessed from the abolition of a rate class.
  - Replace the earlier all-or-nothing row guard: the loader now rejects `valid_from` / `valid_to` on the snapshot row itself (dates belong only inside `effective_attribution`), validates each boundary, and requires `valid_from` / `valid_to` to equal the named instrument's own effective date.
  - Add the `on_date` keyword to `aggregate_article_99_turnover`. When supplied, every item must be proven to cover that date, and `valid_to` is treated as exclusive (the first day the successor text applied). A bracketed row raises `Article99UndatedItemError` instead of being priced.
  - Record the solar water heater handoff explicitly: Loi 65-20 art. 6 removed *les chauffe-eaux solaires* from Article 99 and added them as item 8° of Article 91, so the Article 99 end is `exempted` with `successor_article = 91`, and a test pins the Article 91 end of the link. The item returned to Article 99 at 10 % from 2022-01-01 by Loi 76-21.
  - Repoint the 2007 `source_pdf`: the packaged entry named an SGG index volume (`BO_5487_2007_SGG_index.pdf`) that contains no Article 99. The volume is now `BO_5487-bis_fr.pdf`; every published hash was re-computed from its artifact, and a test does so on every run.
  - Itemize the nested sub-items of all three exemption catalogs (issue #6 box 6). Article 99's corpus splits a multi-product clause into `billable_leaf` rows; all 134 are now exposed as `Article99SubItem` rows with an explicit `parent_item_id` instead of being flattened into the clause quote. A sub-item has no independent effective date, so `effective_attribution` returns the parent's object by identity and the packaged artifact stores no copy.
  - Replace the Article 91/92 packaging with a verbatim projection. `scripts/build_tva_article91_92_catalog.py` copies each corpus row unchanged into `items` (article-level context and numbered clauses, addressed by corpus ID) and `subitems` (nested bullets and letters, addressed by `<parent>-sub-<n>` with the corpus ID kept as `source_item_id`). The projection is 606 + 603 rows, has no aliasing, and `--check` re-runs it and recomputes every quote. Three defects in the previous packaging are now impossible by construction:
    - two clauses were merged into their neighbours and the remaining IDs renumbered, so 24 packaged IDs named a different clause than the corpus row they claimed (2007 Article 92 `17°` *Fondation Cheikh Zaïd* and `31°` *Sala Al-Jadida*);
    - 45 clauses printed `(abrogé)` were published as `in_force_in_snapshot`;
    - 605 corpus rows were silently dropped (603 nested plus the two merged ones).
  - Keep `abrogated` rows and label them: `TVAExemptionItem.is_abrogated` reports the status the consolidated text prints, so a repeal stub is visible rather than dropped or mislabelled as in force.
  - Re-project each Article 99 item's `conditions` from its corpus row. Six clauses had lost their `exclusion` qualifier when first packaged, which silently widened the exemption; quote and rate are now asserted identical to the corpus at the same time.

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
