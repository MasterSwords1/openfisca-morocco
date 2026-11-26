# Impôt sur les sociétés (IS) et cotisation minimale (CM)

The package models the corporate income tax and the minimum contribution on
the `Company` entity for annual periods from **2026-01-01**, under CGI articles
19 and 144.

## IS rates

| Situation | Rate |
|---|---|
| Net profit below 100,000,000 DH, and the profit has stayed below that threshold for three consecutive years | **20 %** |
| Net profit **≥ 100,000,000 DH** | **35 %** |
| Credit institutions, Bank Al-Maghrib, CDG, insurance/reinsurance | **40 %** |

The 35 % rate is subject to the exclusions of art. 19-I-B: Casablanca Finance
City service companies, industrial acceleration zones, and companies bound by
an investment convention of at least 1.5 billion DH. The model exposes
`exclusion_taux_35`; the caller asserts the exclusion.

The three-year condition is exposed as `benefice_sous_seuil_trois_ans`
(default `True`). The model does not inspect prior years: a crossing year must
set it to `False`, which applies 35 % even below 100,000,000 DH.

## Cotisation minimale

The base is the turnover plus other operating, financial and subsidy products
(`chiffre_affaires_annuel` + `produits_accessoires_financiers`), excluding VAT.

| Turnover | Rate |
|---|---|
| Ordinary sales | **0.25 %** |
| Sales of fuel, gas, butter, oil, sugar, flour, water, electricity and medicines | **0.15 %** |
| Professional/agricultural income subject to IR | 4 % — **not applicable to `Company`**, not modelled |

`chiffre_affaires_produits_taux_reduit` is the part of turnover eligible for
0.15 %; it is clipped to the total turnover. The minimum is **3,000 DH** for
companies, even with no turnover. `exonere_cotisation_minimale` lets the caller
assert the 36-month start-up exemption (capped at 60 months from incorporation);
the dates themselves are not inputs.

## Liquidation

```
is_du_brut    = max(is_theorique, cotisation_minimale)
is_net_a_payer = max(0, is_du_brut − credit_impot)
```

`benefice_fiscal` is an input: the model does not reconstruct the fiscal profit
from accounting. A negative profit produces zero IS but the CM floor still
applies unless the company is exempted.

## Variables

Inputs: `benefice_fiscal`, `chiffre_affaires_annuel`,
`produits_accessoires_financiers`, `chiffre_affaires_produits_taux_reduit`,
`est_etablissement_financier`, `benefice_sous_seuil_trois_ans`,
`exclusion_taux_35`, `exonere_cotisation_minimale`, `credit_impot`.

Outputs: `taux_is_applique`, `is_theorique`, `base_cotisation_minimale`,
`cotisation_minimale`, `is_du_brut`, `is_net_a_payer`.

## What is not modelled

- reconstruction of the fiscal profit from accounting (depreciation, provisions,
  loss carry-forwards, tax credits' eligibility);
- the microfinance five-year exclusion from the 40 % rate;
- the 4 % CM rate for IR professions (the `Company` entity is outside its scope);
- the 36/60-month CM exemption dates (the caller asserts the exemption);
- the three-year condition and the 35 % exclusions are caller assertions, not
  prior-year computations;
- the CM instalments and the IS withholding/instalment schedule;
- the rate history before 2026.

## Sources

- [CGI, BO 5487 bis](https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5487-bis_fr.pdf)
  (articles 19 and 144, codification)
- [Loi de finances n° 50-22, BO 7154 bis](https://www.sgg.gov.ma/BO/FR/2873/2022/BO_7154-bis_Fr.pdf)
  (20 % / 35 % / 40 % and the 0.25 % / 0.15 % CM rates)
