
## 0.2.0 - [#2](https://github.com/MasterSwords1/openfisca-morocco/issues/2)

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
