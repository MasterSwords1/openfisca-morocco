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
| Non-exempt company capital contribution, capital ≤ 500,000 DH | **1,000 DH fixed** | CGI art. 135-I-1° |
| Non-exempt company capital contribution, capital > 500,000 DH | **0.5 %** | CGI art. 133-I-H |

Proportional duties have a **100 DH minimum** (art. 133-II). A **2 % additional
duty** applies to the **whole price** above **300,000 DH** when it is not paid by
a traceable means (art. 133-III); mixed cash/traceable payments are not
modelled, and the model assumes traceable payment unless
`paiement_par_moyen_tracable` is set to false.

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
`apport_capital_numeraires` (exempt), `apport_capital_non_exonere` and
`droits_enregistrement_constitution_societe`.

## What is not modelled

- notary fees, mortgage registration and other professional costs;
- the exemptions of CGI art. 129 other than the cash-capital exemption, and the
  exemptions listed in article 1 of Décret 2-16-375;
- the 5× built-area limit for land attached to built premises;
- merchandise inventory sold with a *fonds de commerce* (art. 133-I-B-10°);
- the liabilities affecting capital contributions (art. 133-I-H);
- multiple acquisitions in the same entity-year: one value and one type per
  entity and year;
- lease agreements and the other fixed or proportional duties of arts. 127–135;
- the rate history before 2026: the 2026 rules apply from 2026-01-01, and any
  pre-2026 input for a duty (acquisition value, type, payment method or
  certificate; capital apport, including exempt cash, for the constitution
  duty) raises an error;
- the conservation formalities other than the inscription (morcellement,
  bornage, duplicata, etc.).

## Sources

- [Loi de finances n° 73-16, BO n° 6577 bis](https://www.sgg.gov.ma/BO/bo_fr/2017/BO_6577-bis_Fr.pdf)
  (4 %, 5 % and 6 % rates, the 1,000 DH fixed duty and its 500,000 DH threshold)
- [CGI, BO 5487-bis](https://www.sgg.gov.ma/BO/bo_fr/2007/bo_5487-bis_fr.pdf)
  (0.5 % capital rate and the 100 DH minimum)
- [DGI, Droits d'enregistrement](https://tax.gov.ma/wps/portal/DGI/Vos-impots-procedures/Droits-d_enregistrement/)
  (0.5 % rate and the 2 % surcharge above 300,000 DH)
- [Décret n° 2-16-375, BO n° 6484](https://www.sgg.gov.ma/BO/bo_fr/2016/BO_6484_Fr.pdf)
  (conservation-foncière tariff)

## Tests

`openfisca_morocco/tests/enregistrement.yaml` covers built property with and
without the certificate, vacant land, a *fonds de commerce*, the 100 DH and
500 DH floors, the 2 % surcharge, an unset type and a zero acquisition;
`openfisca_morocco/tests/test_enregistrement.py` covers company acquisitions,
the certificate, the cash exemption, the fixed 1,000 DH band, the 0.5 % band
and the pre-2026 guard.
