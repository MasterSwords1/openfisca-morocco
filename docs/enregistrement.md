# Droits d'enregistrement et conservation foncière

The package models registration duties on real-estate acquisitions and on
company capital contributions, plus land-conservation fees. Rates are those of
the 2026 CGI; the conservation tariff is Décret n° 2-16-375.

## Rates

| Operation | Duty | Source |
|---|---|---|
| Acquisition of built premises (residential, commercial, professional, administrative) | **4 %** | CGI art. 133-I-F-1° |
| Acquisition of vacant land or buildings to be demolished | **5 %** | CGI art. 133-I-G-1° |
| Sale of a *fonds de commerce* (going concern) | **6 %** | CGI art. 133-I-A-1° |
| Company formation, **total subscribed capital** ≤ 500,000 DH **and a non-exempt apport** | **1,000 DH fixed** | CGI art. 135-I-1° |
| Company formation, total capital > 500,000 DH **and a non-exempt apport** | **0.5 % on the non-exempt apport**, minimum 1,000 DH | CGI art. 133-I-H and 133-II |
| Cash-only formation | **0** (exempt) | CGI art. 129-IV-23° |

The 500,000 DH threshold is the amount of the capital increase for the
operation, not the post-increase share capital (DGI circular 721); cash apports
count toward it but are excluded from the taxable base.

Proportional duties have a **100 DH minimum** (art. 133-II), raised to **1,000 DH for company formations**. A **2 % additional
duty** applies from **1 July 2026** when the price is not paid by a traceable
means (art. 133-III). For immovable property it applies to the **whole price**
above **300,000 DH**; a *fonds de commerce* has no threshold. Mixed
cash/traceable payments are not modelled, and the model assumes traceable
payment unless `paiement_par_moyen_tracable` is set to false. The act date is
`date_acte_enregistrement`, which defaults to 2026-07-01; set an earlier date
for an act concluded before July 2026.

The land-conservation fee is **1.5 % ad valorem + 100 DH fixed**, with a
**500 DH minimum** on the inscription. The **100 DH certificate of ownership**
is a separate, optional formality exposed by `demande_certificat_propriete`;
it is not part of the inscription tariff.

> Two rates in issue #42 were incorrect: 6 % applies to a *fonds de commerce*,
> not to built commercial premises (4 %), and a company formation is not
> simply 0.5 % — cash contributions are exempt and small non-exempt
> contributions pay a 1,000 DH fixed duty.

## Variables

Household:

- `valeur_bien_acquis`, `type_acquisition_immobiliere` (built / vacant land /
  *fonds de commerce*; **no default**, an unset type yields 0);
- `paiement_par_moyen_tracable`, `demande_certificat_propriete`;
- `droits_enregistrement`, `frais_conservation_fonciere`,
  `frais_acquisition_immobiliere_totaux`.

Company: the same inputs and amounts with the `_societe` suffix, plus
`apport_capital_numeraires` (exempt but counted in the 500,000 DH threshold),
`apport_capital_non_exonere`, `apport_capital_total`,
`date_acte_enregistrement` / `date_acte_enregistrement_societe` and
`droits_enregistrement_constitution_societe`.

## What is not modelled

- notary fees, mortgage registration and other professional costs;
- the first 2 % trigger (a deed that does not state the payment modalities or
  references) and the bank-credit / article 193-deposit carve-outs: the model
  only reads `paiement_par_moyen_tracable`;
- the share premium (*prime d'émission*), which is excluded from the 500,000 DH
  threshold but included in the 0.5 % base under circular 721; no input is
  provided;
- the exemptions of CGI art. 129 other than the cash-capital exemption, and the
  exemptions listed in article 1 of Décret 2-16-375;
- the 5× built-area limit for land attached to built premises;
- merchandise inventory sold with a *fonds de commerce* (art. 133-I-B-10°);
- the liabilities affecting capital contributions (art. 133-I-H);
- multiple acquisitions in the same entity-year: one value and one type per
  entity and year;
- lease agreements and the other fixed or proportional duties of arts. 127–135;
- the rate history before 2026: the 2026 rules apply from 2026-01-01, except the
  2 % surcharge (acts from 2026-07-01). A lone pre-2026 act date is ignored; the
  value, type, payment or certificate input triggers the guard. Any pre-2026
  input for a duty (acquisition value, type, payment method or
  certificate; capital apport, including exempt cash, for the constitution
  duty) raises an error;
- the conservation formalities other than the inscription (morcellement,
  bornage, duplicata, etc.).

## Sources

- [Loi de finances n° 38-07, BO n° 5591 bis](https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5591-bis_fr.pdf)
  (6 % rate on a *fonds de commerce*, applicable from 1 January 2008)
- [Loi de finances n° 22-12, BO n° 6048](https://www.sgg.gov.ma/BO/bo_fr/2012/bo_6048_fr.pdf)
  (4 % rate on built premises)
- [Loi de finances n° 73-16, BO n° 6577 bis](https://www.sgg.gov.ma/BO/bo_fr/2017/BO_6577-bis_Fr.pdf)
  (5 % rate on vacant land, created in 2017)
- [Loi de finances n° 115-12, BO n° 6113 bis](https://www.sgg.gov.ma/BO/bo_fr/2012/BO_6113-bis_Fr.pdf)
  (1,000 DH fixed duty and 500,000 DH threshold)
- [Loi de finances n° 65-20, BO n° 6944 bis](https://www.sgg.gov.ma/Portals/0/BO/2020/BO_6944-bis_Fr.pdf)
  (0.5 % capital rate)
- [Loi de finances n° 50-25, BO n° 7465 bis](https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_fr.pdf)
  (2 % surcharge for acts from 1 July 2026; 300,000 DH threshold for immovable
  property, no threshold for a *fonds de commerce*)
- [CGI, BO 5487-bis](https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5487-bis_fr.pdf)
  (100 DH proportional minimum)
- [Décret n° 2-16-375, BO n° 6484](https://www.sgg.gov.ma/BO/bo_fr/2016/BO_6484_Fr.pdf)
  (conservation-foncière tariff)

## Tests

`openfisca_morocco/tests/enregistrement.yaml` covers built property with and
without the certificate, vacant land, a *fonds de commerce*, the 100 DH and
500 DH floors, the 2 % surcharge, an unset type and a zero acquisition;
`openfisca_morocco/tests/test_enregistrement.py` covers company acquisitions,
the certificate, the cash exemption, the fixed 1,000 DH band, the 0.5 % band,
the pre-2026 guards, the 1 July 2026 surcharge start, the absence of a
threshold for a *fonds de commerce* and the 300,000 DH boundary.
