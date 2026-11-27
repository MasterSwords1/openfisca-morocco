# Code du travail: seniority bonus, severance and SMIG

This page documents the labour-code benefits computed on the `Person` entity
for **monthly** periods from **July 2004**:

- the statutory **seniority bonus** (*prime d'ancienneté*, art. 350);
- the statutory **severance pay** (*indemnité de licenciement*, arts. 52–53);
- the **SMIG** floor and a compliance check (art. 356).

The rules are encoded from Loi n° 65-99 portant Code du travail (BO n° 5167 du
8 décembre 2003, complété par le BO n° 5210). The SMIG series is taken from the
decrees fixing the non-agricultural minimum wage, including décret n° 2.24.1122
for 2025 (BO n° 7367) and décret n° 2.25.983 for 2026 (BO n° 7469).

## Seniority bonus

Article 350 sets step rates, not marginal rates. The rate applies to the whole
base once the threshold is reached:

| Service | Rate |
|---|---|
| less than 2 years | 0 % |
| 2 years | 5 % |
| 5 years | 10 % |
| 12 years | 15 % |
| 20 years | 20 % |
| 25 years | 25 % |

The base is `salaire_de_base`. Article 353 defines the legal base as salary,
accessories and overtime increases, excluding family allowances, tips (except
for employees paid only in tips), gratuities, profit sharing, expense
reimbursements and similar items. The package does not decompose those
elements: the caller aggregates the article 353 base in `salaire_de_base`.

`salaire_brut_global` is computed as:

```
salaire_brut_global = salaire_de_base + prime_anciennete_legale
```

so the bonus automatically enters the IR and monthly-withholding pipelines. If
the caller supplies `salaire_brut_global` directly, that input overrides the
formula and must already include the bonus. The bonus is not added to
`salaire_brut`, the CNSS/AMO base; include it there as well when it is subject
to contributions.

## Severance pay

Article 52 opens the right after **six months** in the same enterprise. Article
53 grants, for each year or fraction of a year of effective service:

| Service | Hours of salary per year |
|---|---|
| first 5 years | 96 |
| years 6 to 10 | 144 |
| years 11 to 15 | 192 |
| beyond 15 years | 240 |

A fraction of a year counts as a full year. The model uses:

```
heures = 96 × min(years, 5)
       + 144 × min(max(years − 5, 0), 5)
       + 192 × min(max(years − 10, 0), 5)
       + 240 × max(years − 15, 0)
indemnite_licenciement_legale = heures × max(salaire_brut_global, smig_mensuel) / 191
```

The right is conditioned on `licenciement_sans_faute`: a dismissal for grave
misconduct (art. 61) produces no statutory indemnity. Article 56 floors the
reference salary at the SMIG.

## SMIG

`smig_horaire` and `smig_mensuel` are dated from July 2004. The monthly amount
is the hourly rate × 191 hours. At the time of writing:

| From | Hourly (MAD) | Monthly, 191 h (MAD) |
|---|---|---|
| 2023-09-01 | 16.29 | 3 111.39 |
| 2025-01-01 | 17.10 | 3 266.10 |
| 2026-01-01 | 17.92 | 3 422.72 |

`salaire_conforme_smig` is a monthly boolean comparing `salaire_brut_global`
with `smig_mensuel`. At the exact centime the check allows a half-centime
numerical tolerance: an annual amount divided by twelve can be stored a
fraction below the published monthly SMIG in float32. The tolerance cannot
flip a verdict at a whole centime.

## Example

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tbs = CountryTaxBenefitSystem()
simulation = SimulationBuilder().build_from_dict(
    tbs,
    {
        "persons": {
            "Salarie": {
                "salaire_de_base": {"2025-01": 6000},
                "anciennete_annees": {"2025-01": 6},
                "licenciement_sans_faute": {"2025-01": True},
            }
        }
    },
)

print(simulation.calculate("prime_anciennete_legale", "2025-01"))  # [600.]
print(simulation.calculate("salaire_brut_global", "2025-01"))  # [6600.]
print(simulation.calculate("indemnite_licenciement_legale", "2025-01").round(2))
# [21562.3]
print(simulation.calculate("salaire_conforme_smig", "2025-01"))  # [ True]
```

An annual `salaire_de_base` is divided over the months like the other salary
inputs.

## Limitations

- **Article 353 base is caller-built.** The package does not sort salary
  components into the included and excluded categories; `salaire_de_base` is
  the caller's aggregation.
- **Severance reference is the current month.** The model uses the month's
  `salaire_brut_global`, not the average of the 52 weeks before termination
  (art. 55). With constant pay the two coincide.
- **Set the dismissal flag for the termination month.** `indemnite_licenciement_legale`
  is a normal monthly variable; `licenciement_sans_faute` should be true only
  for the month in which the contract ends, not for the whole employment.
- **Only the statutory indemnity.** Notice pay, damages for abusive dismissal
  and the loss-of-employment allowance (the art. 59 items, subject to the
  art. 60 retirement exclusion) and the 100 % increase for staff
  representatives (art. 58) are not modelled.
- **Seniority is an input.** `anciennete_annees` is supplied by the caller;
  service periods assimilated by arts. 351–352 are not reconstructed from
  hire dates.
- **Contractual seniority schemes.** Article 350 does not apply when the
  contract, internal rules or collective agreement already base pay on
  seniority. The model always applies the statutory steps, so a caller in that
  case should supply `salaire_brut_global` directly instead of
  `salaire_de_base`; the direct input overrides the bonus formula.
- **Non-agricultural SMIG only.** SMAG and part-time prorating are not
  modelled.
- **Monthly withholding is a payroll estimate.** The bonus feeds
  `salaire_brut_global`, but the annual IR assessment and the monthly
  withholding keep the limits described in [coverage](coverage.md).
