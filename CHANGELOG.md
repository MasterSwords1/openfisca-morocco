## 0.16.0 - [#45](https://github.com/MasterSwords1/openfisca-morocco/issues/45)

* Tax and benefit system evolution.
* Impacted periods: 2004-07-01 onwards.
* Impacted areas: `variables.code_travail`, `parameters.code_travail`, `variables.impot_revenu` (`salaire_brut_global`).
* Details:
  - Add `salaire_de_base`, `anciennete_annees`, `prime_anciennete_legale`,
    `licenciement_sans_faute`, `indemnite_licenciement_legale` and
    `salaire_conforme_smig`.
  - Encode the article 350 seniority bonus at 5/10/15/20/25 % after
    2/5/12/20/25 years, applied to the caller's article 353 base.
    `salaire_brut_global` now includes the bonus unless supplied directly.
  - Encode the article 53 severance after six months: 96, 144, 192 and
    240 hours of salary per year or fraction, with the reference salary
    floored at the SMIG.
  - Add the non-agricultural SMIG hourly and monthly series from July 2004
    to 2026 (191 hours per month), including 17.10/3 266.10 DH in 2025 and
    17.92/3 422.72 DH in 2026.

## 0.15.0 - [#44](https://github.com/MasterSwords1/openfisca-morocco/issues/44)

* Tax and benefit system evolution.
* Impacted periods: 2016-01-01 onwards.
* Impacted areas: `variables.impot_revenu`, `parameters.impot_revenu.bareme_mensuel`.
* Details:
  - Add the monthly payroll withholding (*retenue à la source*):
    `salaire_brut_imposable_mensuel`, `frais_professionnels_mensuel`,
    `salaire_net_imposable_mensuel`, `ir_brut_mensuel`,
    `deduction_charges_famille_mensuelle`, `ir_prelevement_source_mensuel`
    and `salaire_net_a_payer`.
  - The monthly scale is the annual art. 73-I scale divided by twelve; the
    professional-expense ceiling and the 78 000 DH switch are prorated, and
    the family deduction is the annual amount divided by twelve.
  - Withholding starts in 2016, when the AMO parameters start (the CNSS rates go back to 2002).
    The annual `impot_sur_le_revenu` remains the reference and no annual
    regularisation is modelled.

## Unreleased - openfisca-core 46

* Technical improvement.
* Details:
  - Require Python 3.11+ and `openfisca-core[web-api] >= 46.1.0` (previously
    Python 3.9+ and `openfisca-core >= 44.1.0`).
  - The tax and benefit calculations are unchanged. The full suite passes on
    Python 3.12, 3.13 and 3.14 with `openfisca-core` 46.1.0, including the
    Web API.

## 0.14.0 - [#43](https://github.com/MasterSwords1/openfisca-morocco/issues/43)

* Tax and benefit system evolution.
* Impacted periods: 2026-01-01 onwards.
* Impacted areas: `variables.impot_societes`, `parameters.impot_societes`.
* Details:
  - Add the corporate income tax on `Company`: 20 % normal (subject to the
    three-consecutive-years condition), 35 % at a net profit of 100,000,000 DH
    or more with the art. 19-I-B exclusions, and 40 % for credit institutions,
    Bank Al-Maghrib, CDG and insurers/reinsurers.
  - Add the cotisation minimale: 0.25 % on turnover and other operating,
    financial and subsidy products, 0.15 % on the listed products, with a
    3,000 DH floor; `exonere_cotisation_minimale` carries the start-up
    exemption.
  - Liquidate `is_du_brut = max(is_theorique, cotisation_minimale)` and
    `is_net_a_payer = max(0, is_du_brut - max(credit_impot, 0))`.
  - Add `benefice_atteint_100m` so the float32 storage at 100M can be
    overridden by the caller.
  - `benefice_fiscal` is an input; the fiscal profit is not reconstructed. The
    three-year condition, the 35 % exclusions, the CM exemption dates and the
    microfinance exclusion are caller assertions. The 4 % CM rate for IR
    professions is outside the `Company` scope.
  - Tests cover a standard PME, a 35 % large firm, a loss-making company at
    the 3,000 DH floor, a 40 % financial institution, reduced-rate products,
    the three-year crossing, the 35 % exclusion, credits, exemption and other
    products.

## 0.13.0 - Challenger review fixes

* Tax and benefit system evolution.
* Impacted periods: 2009-01-01 (employer family-allowance rate), 2010-01-01 (IR gating), 2016-01-01 (CNSS/AMO), 2019-07-01 (CNSS allocations), 2023-01-01 (4th–6th child amount), 2026-01-01 (registration duties), 2026-07-01 (2 % registration surcharge).
* Impacted areas: `variables.allocations_familiales`, `variables.impot_revenu`, `variables.ir_patrimoine`, `variables.ir_deductions_globales`, `variables.ir_regimes_professionnels`, `variables.enregistrement`.
* Details:
  - `nombre_enfants` now counts only `children`-role members who meet the
    statutory age and situation conditions: under 12; 12–20 and in studies
    (schooled or higher education); 12–17 and apprenticed; or disabled and
    without income, where the caller asserts that the disability dates from
    before the applicable age limit.
  - Add Person inputs `enfant_scolarise_cnss`, `enfant_apprenti_cnss`,
    `enfant_etudes_superieures_cnss`, `enfant_handicape_cnss` and
    `enfant_handicape_sans_revenu_cnss`.
  - Split the age bands per Décret n° 2-72-541, art. 6: apprenticeship ends
    before 18, studies before 21; the under-12 band remains unconditional.
  - Raise the 4th–6th child amount from 36 DH to 100 DH from 2023-01-01,
    following the retroactive effect of Décret n° 2-23-715 (BO n° 7453). The
    maximum for six children becomes 1,200 DH/month.
  - A child without a birth date defaults to 1970-01-01 and is excluded from
    the age-based bands; the disability branch can still apply. Supply a birth
    date for dependent children.
  - A child born during a month is counted for that month.
  - The 108-day affiliation condition, Moroccan residence, the under-12
    “charge exclusive et effective” condition, the 60 % SMIG/SMAG salary
    condition, the father-income condition of loi n° 07-92 art. 21 for a
    disabled child, proof of schooling or disability and the art. 6(e) case
    remain unmodelled.
  - Add `revenu_etranger_imposable`: foreign income now raises before 2026
    instead of being silently included in the global IR base. Foreign income
    is taken at its gross positive amount and remains outside the capital
    rates.
  - `impot_plus_values` now raises before 2026 for a nonzero amount on
    listed or unlisted securities, instead of silently returning zero.
  - `impot_capitaux_mobiliers` now sums the gated leaves, so offsetting
    capital gains and losses cannot net to zero and bypass the pre-2026 gate.
    The same per-input check now covers foreign capital income, property gains
    and article 28 deductions.
  - The registration-duty pre-2026 guards now check the acquisition type, the
    payment-traceability flag, the certificate request and both capital-apport
    inputs, so an auxiliary input alone raises instead of returning zero.
  - The 2 % registration surcharge now applies only to acts from 2026-07-01,
    through the new `date_acte_enregistrement` / `_societe` inputs, and a
    *fonds de commerce* is no longer subject to the 300,000 DH threshold.
  - Fix the company-formation threshold: the 1,000 DH fixed duty applies when
    total subscribed capital (cash + non-exempt) is ≤ 500,000 DH and a
    non-exempt apport is present; above that, 0.5 % applies to the non-exempt
    apport with a 1,000 DH minimum. A cash-only formation remains exempt.
  - The CPU and auto-entrepreneur liberatory leaves now raise before 2026 when
    a non-net-réel regime is selected, even with zero turnover, instead of
    returning a silent zero.
  - Disclose the registration 2 % first trigger, the bank-credit / article 193
    carve-outs and the unmodelled share premium.
  - Backdate the 6,40 % employer family-allowance contribution to 2009-01-01
    (Décret 2-01-2723 art. 1, as amended by Décret 2-08-359); the 2019-07 date
    belongs to the benefit amounts, not the rate. The employer CNSS/AMO chain
    is therefore usable from 2016-01, like the employee chain.

## 0.12.0 - [#46](https://github.com/MasterSwords1/openfisca-morocco/issues/46)

* Tax and benefit system evolution.
* Impacted periods: 2010-01-01 onwards.
* Impacted areas: `parameters.impot_revenu`, `variables.impot_revenu`.
* Details:
  - Backdate the progressive IR scale to 2010: 0 / 30 000 / 50 000 / 60 000 /
    80 000 / 180 000 DH with 0 / 10 / 20 / 30 / 34 / 38 % for 2010–2024
    (Loi de finances n° 48-09), keeping the 2025 scale from 2025-01-01.
  - Encode the historical professional-expense deduction: a uniform 20 %
    capped at 30 000 DH from 2010 to 2022, then 35 % up to 78 000 DH and 25 %
    above, capped at 35 000 DH, from 2023 (Loi de finances n° 50-22).
  - **Correct the professional-expense base:** the forfait is computed on gross
    taxable pay before social contributions (art. 59-I); contributions remain a
    separate deduction (art. 59-II). This changes 2025 and 2026 IR when the
    forfait is below its cap, for example 120 000 DH of pay with 5 937.60 DH of
    contributions: the tax falls from 7 664.04 to 7 218.72 DH.
  - Replace the pre-2023 zero-threshold encoding with an explicit `taux_2010_2022`
    parameter; the two-rate regime and its 78 000 DH threshold start in 2023.
  - Encode the historical family-charge deduction: 360 DH per dependent
    (2 160 DH maximum) from 2010 to 2024, 500 DH in 2025 and 600 DH from 2026.
  - Tests at 2010, 2018, 2022, 2023 and 2024 cover the scale, the expense cap,
    the 78 000/78 001 DH switch, the 2 160/3 000 DH family caps and the
    contribution-free base.
  - Add a `ValueError` for IR before 2010; the default CNSS/AMO chain starts in
    2016, so 2010–2015 simulations must supply contributions explicitly.
  - Historical IR remains limited to salarial income plus supplied net-réel
    professional income; rental, capital, property and foreign income are
    still 2026-only.

## 0.11.0 - [#42](https://github.com/MasterSwords1/openfisca-morocco/issues/42)

* Tax and benefit system evolution.
* Impacted periods: 2026-01-01 onwards.
* Impacted areas: `variables.enregistrement`, `parameters.enregistrement`.
* Details:
  - Add registration duties on real-estate acquisitions: 4 % for built premises
    (art. 133-I-F-1°), 5 % for vacant land or buildings to be demolished
    (art. 133-I-G-1°), 6 % for a fonds de commerce (art. 133-I-A-1°), with a
    100 DH minimum (art. 133-II) and a 2 % surcharge for untraceable payment
    above 300,000 DH (art. 133-III).
  - Company capital: cash contributions are exempt (art. 129-IV-23°); other
    contributions pay a 1,000 DH fixed duty up to 500,000 DH and 0.5 % above
    (art. 135-I-1° / 133-I-H).
  - Add conservation fees under Décret 2-16-375: 1.5 % ad valorem + 100 DH
    fixed, with a 500 DH minimum; the 100 DH certificate is a separate
    optional formality.
  - Expose the household amounts (`droits_enregistrement`,
    `frais_conservation_fonciere`, `frais_acquisition_immobiliere_totaux`) and
    the company equivalents, plus the capital-contribution duty.
  - Correct the issue's rates: built commercial premises are 4 %, not 6 %;
    vacant land is 5 %; company formation is not a flat 0.5 %.
  - No parameter value changed for existing taxes.

## 0.10.2

* Documentation.
* Impacted areas: `openfisca_morocco/parameters/` metadata.
* Details:
  - Point the parameter references at official government sources instead of a
    private consolidator: SGG Bulletin Officiel PDFs (BO 5487-bis for the CGI,
    BO 7362 for the 2025 finance law, BO 7253 for the 2024 finance law) and the
    ANSS/CNSS official pages.
  - Ship the legislation parameters, situation examples and YAML scenarios in
    the wheel, and verify the installed wheel outside the checkout in CI.
  - No parameter value changed.

## 0.10.1

* Documentation.
* Impacted areas: `openfisca_morocco/parameters/` metadata.
* Details:
  - Replace the private-corpus and DGI-homepage references with public,
    article-level sources: Ma Loi for the CGI, CNSS for social contributions and
    family allowances, ANSS for direct social support, and Ma Loi for the AMO
    code.
  - The parameter explorer deployed from this package can now render usable
    "Références législatives" links; no parameter value changed.

## 0.10.0 - [#10](https://github.com/MasterSwords1/openfisca-morocco/issues/10) [#11](https://github.com/MasterSwords1/openfisca-morocco/issues/11)

* Tax and benefit system evolution.
* Impacted periods: all; the examples use 2025 and 2026.
* Impacted areas: `situation_examples/`, `reforms/`, `tests/situations/`,
  `tests/reforms/`.
* Details:
  - Add five situation examples alongside `salarie.json`: below and above the
    IR exemption, a couple with two children, a high earner, an employer-cost
    case and an ASD household. Each requests its outputs and is simulated and
    asserted.
  - Add `ReformeBaremeIR`, restoring the pre-2025 IR scale (30,000 DH exemption,
    38 % top rate) for distributional analysis, and `ReformeTVA`, setting the
    normal VAT rate to 18 % from 2025 while preserving the 2004-2024 history.
  - Add YAML situation tests for the IR, CNSS and benefit families, mirroring the
    JSON examples, and pytest coverage for the examples and both reforms.
  - No template demo situations or reforms remained to remove.

## 0.9.0 - [#33](https://github.com/MasterSwords1/openfisca-morocco/issues/33) [#34](https://github.com/MasterSwords1/openfisca-morocco/issues/34) [#35](https://github.com/MasterSwords1/openfisca-morocco/issues/35)

* Tax and benefit system evolution.
* Impacted periods: 2026-01-01 onwards for the new rules; professional net income
  and the salarial pipeline remain supported from 2025-01-01.
* Impacted areas: `variables.impot_revenu`, `variables.ir_regimes_professionnels`,
  `variables.ir_deductions_globales`, `variables.ir_patrimoine`, and their
  parameter files.
* Details:
  - Add the professional regimes (art. 32–44): net simplifié with the 15 %
    centres-de-gestion abatement, *contribution professionnelle unique* with the
    art. 40-I coefficients and the art. 73-II-B-6° complementary-duty table, and
    the auto-entrepreneur rates and ceilings. CPU and auto-entrepreneur taxes are
    liberatory and are added to the household total.
  - Add professional loss carry-forward through
    `deficit_professionnel_reportable`, with the four-year limit of article 12
    documented and left to the caller.
  - Add the article 28 deductions: donations, housing-loan interest capped at
    10 % of global income, and retirement premiums capped at 10 % (or 50 % of net
    salary for salary-only taxpayers).
  - Add the 20 % liberatory option on gross rents (arts. 64-IV, 73-II-F-12°),
    removing rents from the barème and from the withholding credit.
  - Add property capital gains (arts. 61-II, 63, 65) with the 15 % acquisition
    forfait, the main-residence and 140,000 DH exemptions and the 20 % rate, and
    foreign-source income with the 15 % / 20 % capital rates.
  - Gate the new rules from 2026 and raise on earlier inputs; document the
    unmodelled revaluation coefficient, treaty relief and foreign tax credits.
  - 40 new YAML cases, 4 gating tests, 2 table-guard tests for the art. 40-I
    coefficients and the art. 73-II-B-6° duty table, and 3 unit tests for the
    art. 28-III-A retirement-premium election.

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
