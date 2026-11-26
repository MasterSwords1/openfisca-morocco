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
(default `True`). The model does not inspect prior years: the years **after** a
crossing must set it to `False` for three consecutive exercises, which applies
35 % even below 100,000,000 DH.

The threshold itself is exposed as `benefice_atteint_100m`. It must not be
forced to `False` at or above the statutory 100,000,000 DH threshold; it exists
to correct the float32 rounding just below it. OpenFisca stores
money as float32, whose granularity at 100,000,000 DH is about 8 DH; the flag
defaults to the rounded comparison and can be set explicitly for a profit within
a few dirhams of the threshold. The same float32 quantization applies to the
amounts.

## Cotisation minimale

The base is the turnover plus other operating, financial and subsidy products
(`chiffre_affaires_annuel` + `produits_accessoires_financiers`), excluding VAT.

| Turnover | Rate |
|---|---|
| Ordinary sales | **0.25 %** |
| Sales of fuel, gas, butter, oil, sugar, flour, water, electricity and medicines, by commercial companies | **0.15 %** |
| Professional/agricultural income subject to IR | 4 % — **not applicable to `Company`**, not modelled |

`chiffre_affaires_produits_taux_reduit` is the part of turnover eligible for
0.15 %; it is clipped to the total turnover. The minimum is **3,000 DH** for
companies, even with no turnover. `exonere_cotisation_minimale` lets the caller
assert the 36-month start-up exemption (capped at 60 months from incorporation);
the dates themselves are not inputs.

## Liquidation

```
is_du_brut    = max(is_theorique, cotisation_minimale)
is_net_a_payer = max(0, is_du_brut − max(credit_impot, 0))
```

`benefice_fiscal` is an input: the model does not reconstruct the fiscal profit
from accounting. A negative profit produces zero IS but the CM floor still
applies unless the company is exempted.

The credit is subtracted from `is_du_brut` (the higher of IS and CM), so it can
reduce the amount below the 3,000 DH CM floor; the floor applies before
credits. This follows the issue's liquidation formula and is a deliberate
modelling choice, not a statement that every credit is legally imputable
against the CM.

## Variables

Inputs: `benefice_fiscal`, `chiffre_affaires_annuel`,
`produits_accessoires_financiers`, `chiffre_affaires_produits_taux_reduit`,
`est_etablissement_financier`, `benefice_sous_seuil_trois_ans`,
`exclusion_taux_35`, `exonere_cotisation_minimale`, `credit_impot`.

Outputs: `taux_is_applique`, `is_theorique`, `base_cotisation_minimale`,
`cotisation_minimale`, `is_du_brut`, `is_net_a_payer`; `benefice_atteint_100m`
is derived and overridable.

## What is not modelled

- reconstruction of the fiscal profit from accounting (depreciation, provisions,
  loss carry-forwards, tax credits' eligibility);
- the microfinance five-year exclusion from the 40 % rate (a caller can set
  `est_etablissement_financier=False` for the first five exercises);
- the art. 19-I-B final-paragraph carve-out for a threshold crossing caused by
  non-current asset-disposal gains (the `benefice_sous_seuil_trois_ans` flag can
  express it, but the prior-year rule is not computed);
- the 8 % forfaitary rate of art. 19-III-A for non-resident contractors awarded
  works, construction or assembly contracts, and the art. 144-I-A exclusion of
  companies taxed under that forfait;
- art. 144-I-C-1° (public-service concessionaires are excluded from the 36-month
  CM exemption) and art. 144-I-C-3° (temporary cessation waives only the 3,000 DH
  minimum); the `exonere_cotisation_minimale` flag is a caller assertion;
- carry-forward or refund of excess credits (they are floored at zero);
- the 4 % CM rate for IR professions (the `Company` entity is outside its scope);
- the 36/60-month CM exemption dates (the caller asserts the exemption);
- the three-year condition and the 35 % exclusions are caller assertions, not
  prior-year computations;
- the CM instalments and the IS withholding/instalment schedule;
- negative turnover/products are clamped to zero component by component, so a
  negative component cannot offset a positive one;
- the rate history before 2026.

## Sources

- [CGI, BO 5487 bis](https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5487-bis_fr.pdf)
  (articles 19 and 144, codification)
- [Loi de finances n° 50-22, BO 7154 bis](https://www.sgg.gov.ma/BO/FR/2873/2022/BO_7154-bis_Fr.pdf)
  (20 % / 35 % / 40 %, 100,000,000 DH threshold and the 0.25 % / 0.15 % CM
  rates)
- [Loi de finances n° 110-13, BO 6217 bis](https://www.sgg.gov.ma/BO/bo_fr/2013/BO_6217-bis_fr.pdf)
  (3,000 DH CM floor)

> The `morocco-holy-graph` Catala `cgi_is.catala_fr` file encodes an obsolete
> 10/20/35 scale and a 0.50 % CM that does not match the 2026 CGI; this module
> follows the 2026 CGI, not that stale oracle.
