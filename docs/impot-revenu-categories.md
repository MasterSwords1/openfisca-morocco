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
| Global IR | `impot_sur_le_revenu` | Barème on the global base, less the family deduction, less the rental withholding |
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
| 28 | out — deductions on global income (housing interest, retirement premiums) |
| 29 | out — assessment of living expenses |
| 30, 31 | partial — professional-income definition used, exemptions and reductions in 31 not modelled |
| 32–39 | modelled — net-réel/simplifié profit supplied as an input; regime thresholds and loss carryforward not computed |
| 40–42 bis, 42 ter | out — *contribution professionnelle unique* and *auto-entrepreneur* regimes |
| 43–55 | out — turnover options, agricultural regimes and related procedures |
| 56–60 | modelled — existing salarial pipeline |
| 61-I | modelled — definition of rental income |
| 61-II, 62, 63, 65 | out — property capital gains, exclusions and profit computation |
| 64 | modelled — 40 % abatement; the 20 % liberatory option in 64-IV is not modelled |
| 66, 69 | modelled — capital income definition and net amount |
| 67, 68 | out — taxable event and exemptions |
| 70, 70 bis | out — net profit on disposals |
| 71, 72 | out — tax period and place |
| 73 | modelled — barème and specific rates |
| 74 | modelled — family deduction; the dependent conditions in 74-II are inputs |
| 75–81 | out — reductions conditions, foreign pensions and related rules |
| 82–86 | out — declaration and payment procedure |

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

## Not modelled

- the *contribution professionnelle unique* and the *auto-entrepreneur* regimes
  (arts. 40–42 bis), which are separate turnover-based regimes;
- loss carryforward for professional income (art. 37) and the simplified-regime
  thresholds (arts. 38–39);
- the deductions on global income in art. 28 (housing-loan interest, retirement
  insurance premiums), including their 10 % ceilings;
- the option for a 20 % liberatory rate on rents (arts. 64-IV and 73-II-F-12°);
- agricultural rents, which fall under art. 64-III rather than the 40 % abatement
  of art. 64-II; OPCI distributions are treated as ordinary rents;
- the 20 % imputable rate on fixed-income products for taxpayers under the net
  réel or simplifié regime (art. 73-II-F-1°); the model always applies the 30 %
  liberatory rate of art. 73-II-G-3°;
- negative capital profits, which are floored to zero and not carried forward;
- property capital gains (art. 61-II), foreign-source income, OPCI/OPCC/plan
  d'épargne specifics, and the 2025 rates for the capital categories;
- the dependent conditions of art. 74-II (age, income ceiling) beyond the
  `nombre_personnes_a_charge` input;
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

`openfisca_morocco/tests/test_ir_categories_gating.py` checks that rental and
capital inputs raise before 2026, that professional income applies in 2025, and
that the 2026 rental rules apply.
