# IR: professional, rental and capital income

This page documents the categories added to the `impot_revenu` pipeline for the
2026 rules. The salarial pipeline (2025 onward) is unchanged.

## Scope

| Category | Variable | Rule |
|---|---|---|
| Professional | `revenu_professionnel_net` | Net profit under the *résultat net réel* or *simplifié*, supplied as an input (CGI arts. 30–39) |
| Rental | `revenus_fonciers_bruts` | Gross rents; 40 % abatement gives `revenu_foncier_net` (art. 64-II) |
| Rental withholding | `retenue_fonciere` | 10 % below 120,000 DH gross, 15 % at or above; none at or below 40,000 DH (arts. 73-II-B-5°, C-4°, 160 bis) |
| Dividends | `dividendes_bruts` | 11.25 % liberatory in 2026, 10 % from 2027 (art. 73-II-B-7° and the art. 247-XXXVII-C schedule) |
| Fixed-income interest | `interets_bruts` | 30 % liberatory (art. 73-II-G-3°) |
| Listed shares | `plus_values_actions_cotees` | 15 % (art. 73-II-C-1°) |
| Unlisted securities | `plus_values_titres_non_cotes` | 20 % (art. 73-II-F-2°) |
| Global base | `revenu_global_imposable` | Salary net + professional net + rental net, floored at zero (arts. 22, 25) |
| Global IR | `impot_sur_le_revenu` | Barème on the global base after article 28 deductions, less the family deduction, less the rental withholding (none under the 20 % option) |
| Capital total | `impot_capitaux_mobiliers` | Sum of the four liberatory taxes |
| Household total | `impot_sur_le_revenu_menage` | Sum of members' global IR and capital taxes |

The barème is unchanged from 2025: 0 % up to 40,000 DH, then 10 %, 20 %, 30 %,
34 % and 37 % (art. 73-I). The family deduction is 600 DH per dependent, capped
at 3,600 DH, from 2026 (Loi de finances n° 50-25, art. 7; art. 74).

## Article coverage (arts. 21–86)

| Articles | Status |
|---|---|
| 21–24 | out — definitions, territoriality and general exemptions; no computation |
| 25 | modelled — global taxable income |
| 26, 27 | out — group and arrival-in-Morocco rules |
| 28 | partial — donations, housing interest and retirement premiums with their ceilings and the salary election; non-cumulation rules out |
| 29 | out — assessment of living expenses |
| 30, 31 | partial — professional-income definition used, exemptions and reductions in 31 not modelled |
| 32–39 | modelled — net réel input, net simplifié with the 15 % centres-de-gestion abatement, loss carry-forward supplied as an input; the art. 39 turnover ceilings are not checked |
| 40–42 bis | modelled — CPU coefficients, ceilings and annual duty table, auto-entrepreneur rates and ceilings; 42 ter out |
| 43–55 | out — turnover options, agricultural regimes and related procedures |
| 56–60 | modelled — existing salarial pipeline |
| 61-I | modelled — definition of rental income |
| 61-II, 63, 65 | partial — profit on disposal, 15 % forfait, main-residence and 140,000 DH exemptions; other transactions and exemptions of 61-II/63 and 62 out |
| 64 | modelled — 40 % abatement and the 20 % liberatory option of 64-IV |
| 66, 69 | modelled — capital income definition and net amount |
| 67, 68 | out — taxable event and exemptions |
| 70, 70 bis | out — net profit on disposals (the 65 computation is used for property) |
| 71, 72 | out — tax period and place |
| 73 | modelled — barème and specific rates |
| 74 | modelled — family deduction; the dependent conditions in 74-II are inputs |
| 75–81 | out — reductions conditions, foreign pensions and related rules |
| 82–86 | out — declaration and payment procedure |

## Professional regimes

`regime_professionnel` selects the regime (net réel by default):

- **net réel** — `revenu_professionnel_net` is reduced by
  `deficit_professionnel_reportable` (the caller supplies only the four
  preceding years, art. 12) and enters the global base;
- **net simplifié** — same base, with the 15 % abatement for members of an
  approved management centre (art. 38-III);
- **contribution professionnelle unique** — turnover × the art. 40-I
  coefficient for the selected category, taxed at 10 % (art. 73-II-B-6°), plus
  the annual complementary duty read from the published table. The art. 41-II-A
  ceiling follows the category: 500,000 DH for the eleven service categories,
  2,000,000 DH for the commercial, industrial and artisanal ones;
- **auto-entrepreneur** — 0.5 % of turnover up to 500,000 DH for commercial,
  industrial or artisanal activity, 1 % up to 200,000 DH for services, plus the
  complementary duty. Above the ceiling the regime does not apply and the tax is
  zero; the taxpayer must select another regime.

Above its art. 41-II ceiling the CPU regime does not apply and the tax is zero,
as for the auto-entrepreneur. Both taxes are liberatory: they are reported
separately and added to the household total, not to the global base.

## Article 28 deductions and the rental option

`deductions_revenu_global` sums donations (no ceiling in art. 28-I), housing-loan
interest capped at 10 % of global income, and retirement premiums. For a
taxpayer with only salary income the premium cap is 50 % of net salary; with
salary and other income the taxpayer may elect between 50 % of net salary and
10 % of global income, and the model keeps the more favourable; with no salary
the cap is 10 % of global income. The barème applies to the income after these
deductions.

`option_foncier_liberatoire` moves gross rents out of the global base and taxes
them at 20 % (arts. 64-IV and 73-II-F-12°); the 10 %/15 % withholding is then not
imputed. The request procedure is not modelled.

## Property gains and foreign income

The taxable profit on a property disposal is the sale price less sale costs,
less the acquisition price increased by the 15 % acquisition-cost forfait and by
investment expenses (art. 65). Disposals totalling at most 140,000 DH in the
year are exempt (art. 63-II-A), as is a main residence held for at least five
years (art. 63-II-B). The rate is 20 % (art. 73-II-F-6°). The annual
revaluation coefficient is not applied.

Foreign income other than capital is included in the global base at gross
(art. 25). Foreign capital income and profits are taxed at 15 % and 20 %
(art. 73-II-C-2° and F-5°) and are not added to the base.

## Individual taxation

Moroccan IR is assessed per taxpayer, not per household: each person has their
own global income and family deduction. `impot_sur_le_revenu_menage` is therefore
a **sum of individual liabilities**, not a joint barème. It is informational and
matches what the household owes in total, but it cannot be used to derive a
marginal rate for the household.

## 2025 and earlier

- Rental and capital rules are encoded **from 2026 only**. A 2025 or earlier
  simulation that supplies rental or capital income **raises an error** instead
  of applying a 2026 rate to an earlier year.
- Professional net income is accepted from 2025, because the net-réel regime and
  the barème exist in 2025; no category rate is involved.
- The 2026 family deduction replaces the 2025 value from 2026-01-01.

## Rental withholding

The withholding is a prepayment, not a final tax: rental income stays in the
global base and the withholding is imputed against the IR due. The model caps the
credit at the tax otherwise due, so it never produces a refund; restitution of
excess withholding is not modelled. The 40,000 DH dispensation is applied to the
gross rents of each person, although art. 160 bis grants it per payer: two
payers each paying 30,000 DH are dispensed by law but produce a 6,000 DH
withholding here, which is lost because no restitution is modelled.

## Order of operations

1. each category is determined separately: salary net, professional net (with
   loss carry-forward and the simplified abatement), rental net or 20 % option,
   foreign income;
2. the global base sums the categories that are not taxed at a liberatory rate;
3. the article 28 deductions are applied to that base, then the barème;
4. the family deduction reduces the tax, then the rental withholding is imputed;
5. liberatory taxes (capital, CPU, auto-entrepreneur, 20 % rents, property
   gains, foreign capital) are computed separately and added to the household
   total.

## Not modelled

- the art. 40-I last paragraph and art. 42 bis: the surplus of service turnover
  above 80,000 DH for a single client, withheld at 30 % (art. 73-II-G-8°); the
  model taxes the whole turnover at the regime rate;
- a taxpayer with several activities: the model takes one
  `categorie_professionnelle`, whereas art. 40-I requires each activity to be
  determined at its own coefficient and then summed;
- the art. 41-II-B condition of membership of the compulsory health insurance
  and the art. 43/44 option procedure, including the two-consecutive-year rule;
- professional loss history: the caller supplies the reportable deficit and is
  responsible for the four-year limit of art. 12, including the exception for
  booked depreciation;
- the art. 28 non-cumulation rules with arts. 59-II-A, 59-V and 65-II;
- the art. 65-II acquisition-loan interest (and its Mourabaha/Ijara
  equivalents) added to the cost base;
- the once-per-five-years condition of the main-residence exemption
  (art. 63-II-B);
- the request procedure for the 20 % rental option, and its reservation to
  rents subject to the art. 160 bis withholding;
- the property-gain transaction list of art. 61-II (expropriation, exchange,
  contribution in kind, gratuitous transfers), the art. 62-II exclusions, the
  co-heir and social-housing exemptions of art. 63-II-C/D, the justification of
  acquisition costs above the 15 % forfait, and the revaluation coefficient;
- treaty relief, the credit mechanism of arts. 77 and 173/174, and exchange
  rates for foreign income;
- agricultural rents (art. 64-III), OPCI/OPCC/plan d'épargne specifics, and the
  2025 rates for the capital categories;
- the dependent conditions of art. 74-II (age, income ceiling) beyond the
  `nombre_personnes_a_charge` input;
- under a turnover regime, a supplied `revenu_professionnel_net` is ignored, and
  the auto-entrepreneur activity defaults to commercial when not set;
- the float32 storage of the turnover can move a duty just across a band edge
  (for example a computed 1,000.00003 falls in the 1,001–2,500 band);
- the dividend schedule after 2027 and the extension of the 2026 rates to later
  years, which are not separately justified.

The rates encoded are those of the CGI 2026 edition. The reviewed text is the
2026 consolidated edition in the project corpus
(`morocco-holy-graph/laws/ma_tax_law/data/consolidated/CGI-2026-FR.pdf.txt`),
which reproduces the *Bulletin Officiel* and states that the Arabic edition
controls in case of divergence.

## Sources

- [Code Général des Impôts, article 25](https://maloi.ma/fr/law/code-impots/article/25)
  (global income)
- [Article 30](https://maloi.ma/fr/law/code-impots/article/30) to
  [article 39](https://maloi.ma/fr/law/code-impots/article/39) (professional income)
- [Article 61](https://maloi.ma/fr/law/code-impots/article/61) and
  [article 64](https://maloi.ma/fr/law/code-impots/article/64) (rental income and
  40 % abatement)
- [Article 66](https://maloi.ma/fr/law/code-impots/article/66) and
  [article 69](https://maloi.ma/fr/law/code-impots/article/69) (capital income)
- [Article 73](https://maloi.ma/fr/law/code-impots/article/73) (barème and specific
  rates)
- [Article 74](https://maloi.ma/fr/law/code-impots/article/74) (family deduction,
  as amended by Loi de finances n° 50-25 for 2026)
- [Article 160 bis](https://maloi.ma/fr/law/code-impots/article/160%20bis) (rental
  withholding)

## Tests

`openfisca_morocco/tests/impot_revenu_categories.yaml` covers the professional
base, the two rental withholding rates with the 120,000 DH boundary, the
40,000 DH exemption and its 42,000 DH edge, a professional deficit that cannot
offset rental income, a credit that binds, the 2026 family deduction and its
six-person cap, the four liberatory capital taxes (including the 2027 dividend
rate), and a two-person household with mixed professional, rental and dividend
income.

`ir_regimes_professionnels.yaml` covers both CPU coefficient bands, the
complementary duty, both auto-entrepreneur ceilings, the simplified abatement
and the loss carry-forward. `ir_deductions_globales.yaml` covers each art. 28
ceiling and the 20 % rental option. `ir_patrimoine.yaml` covers the property
profit computation, both exemptions, the foreign-income base and the two foreign
capital rates.

`openfisca_morocco/tests/test_ir_categories_gating.py` checks that the
2026-only rules raise before 2026 and that professional net income applies in
2025.
