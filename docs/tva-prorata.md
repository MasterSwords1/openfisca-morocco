# TVA deduction prorata (CGI Article 104-I)

The annual prorata is derived from turnover declared for the calendar year:

```
(taxable turnover + Article 92 exempt turnover + Article 94 suspension turnover)
-----------------------------------------------------------------------------
(taxable turnover + Article 92 + Article 94 + Article 91 + out-of-scope turnover)
```

Taxable turnover includes the monthly turnover declared at the normal, 10%,
14%, 7% and transitional rates, plus `chiffre_affaires_taxable_autres`.
Declare Article 100 specific-rate sales and any other taxable turnover not
captured by those rate inputs in `chiffre_affaires_taxable_autres`. The
calculated ratio is limited to the range 0–1. If the denominator is zero, the
annual calculated value is 1.0, a neutral value.

The annual `Company` inputs are `chiffre_affaires_exonere_avec_deduction`
(Article 92), `chiffre_affaires_exonere_sans_deduction` (Article 91),
`chiffre_affaires_suspension` (Article 94), `chiffre_affaires_hors_champ`, and
`chiffre_affaires_taxable_autres`. All are amounts in MAD for the calendar
year. `chiffre_affaires_taxable_annuel` and
`chiffre_affaires_total_declare` expose the computed yearly totals, and
`prorata_deduction_calcule` exposes the annual ratio.

Article 104-I determines the prorata at the end of year N from year N's
operations and retains it for deductions during year N+1. Thus monthly
deductions use the previous calendar year's `prorata_deduction_calcule`, never
the current year's turnover. If the previous year has no positive declared
turnover total, `prorata_deduction` remains the monthly manual fallback. A
caller that provides no prior-year detail keeps the manual value; a caller that
declares only taxable turnover gets a calculated ratio of 1.0.

New companies may use `prorata_deduction` as the provisional value for their
creation year; once a calendar year has positive declared turnover, its
calculated ratio applies to the following year. The forecast and first-year
regularization rules of Article 104-I are not reconstructed from a creation
date.

The turnover categories are supplied by the declarant. The model does not
classify transactions automatically from the Article 91 or 92 catalogs.
`chiffre_affaires_taxable_autres` must include Article 100 specific-rate sales
and other taxable sales omitted from rate-bracket inputs. Turnover declared on
the abolished 14 %/7 % rates is still counted as taxable; do not duplicate it
under the transitional-rate input. Separate prorata by regulated sector
(Article 104-I) is not modelled: one ratio is computed per company. This
calculation does not implement the capital-goods regularization rules in CGI
Article 104-II.

Source: CGI Article 104-I, 2021 consolidated edition.
