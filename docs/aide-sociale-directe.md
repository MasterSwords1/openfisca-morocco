# Aide sociale directe (ASD)

This package models the published statutory ASD amounts as a monthly household
estimate. It does **not** decide whether a real household is enrolled in the
required registers or will be awarded support by the ANSS.

## Inputs and scope

- `score_rsu` is the household's externally supplied RSU socio-economic index.
  The model applies the published ceiling (`index <= 9.743001`); it does not
  calculate the index from household income or other attributes. A missing
  index defaults to a sentinel above the ceiling, so an unset score does **not**
  make the household eligible.
- `conditions_administratives_asd_remplies` must be explicitly set to `true`.
  It stands for the applicable residence, RNP/RSU enrollment, dossier and other
  administrative conditions, including the exclusion cases in article 7 of
  Loi 58-23. It defaults to `false`, so missing evidence does not silently
  become eligibility.
- `enfant_eligible_asd` represents the under-21 condition or an applicable legal
  exception. It is an input because age, school-attendance and exception
  evidence are not all represented by this module.
- `rang_enfant_asd` is supplied per child; OpenFisca member ordering is not
  assumed to reproduce the legal order in the administrative dossier. Ranks must
  be unique per child: a duplicated rank is counted twice and defeats the
  six-child cap. Rank `0` means unknown or not concerned and receives no base
  amount and no disability complement.
- `eligible_aide_forfaitaire_asd` explicitly identifies households for the
  flat allowance, including households with no currently eligible children.
- Schooling, under-six status, severe disability, paternal orphan status and
  birth grant rank are inputs. No income test is derived from the IR variables:
  the published targeting rule uses the RSU index, and the registry calculation
  and ANSS verification are outside this package.

The monthly formula covers the published child schedule, the household
minimum, the flat allowance when explicitly identified, and birth grants when
an event is supplied for that month.

### Amount rules represented

- Base child amount, ranks 1–6 only; a seventh child gets no base amount. Ranks
  1–3: 200 DH (Dec. 2023), 250 DH (2025), 300 DH (2026) when the child is
  schooled, under six or severely disabled; 150 / 175 / 200 DH when the child is
  6–20 and not schooled.
- Base child amount, ranks 4–6: 36 DH (schooled / under six / disabled) and
  24 DH (not schooled). These amounts are not revalorised in the published
  table.
- Paternal-orphan complement, ranks 1–3: 150 DH (Dec. 2023), 125 DH (2025),
  100 DH (2026), added to the base amount when the child is schooled or under
  six — the condition printed in the annex (`دون 6 سنوات أو يتابع دراسته`). A
  disabled child aged six or more and not schooled therefore receives the base
  rate and the disability complement, but not the orphan complement. For
  schooled children this reproduces the ANSS widow totals of 350 / 375 / 400 DH.
- Severe-disability complement: 100 DH per child at every supplied rank from 1,
  including the seventh child and beyond, where only this complement is due.
  The base-rate header of the annex does include disability
  (`أو في وضعية إعاقة`), which is why a disabled child keeps the schooled /
  under-six base rate.
- Where a child amount applies, a household total below 500 DH is raised to
  500 DH. The floor is documented in ANSS's published guidance; the annex page
  itself only carries the 500 DH flat allowance, so no primary article is cited
  for the floor. The flat allowance for households without a child amount is a
  separate 500 DH parameter (`aide_forfaitaire_mensuelle`), even though the two
  amounts are currently equal.
- Birth grants: 2,000 DH for the first birth and 1,000 DH for the second,
  added after the monthly calculation and only in the month supplied; they are
  not multiplied for multiple births.

Not modelled, and therefore not to be read as an exhaustive entitlement
calculation:

- the school-return allowance added by Décret 2-24-706 (200 DH in primary and
  lower secondary, 300 DH in upper secondary, September only, up to six
  children);
- the special allowance for orphans and abandoned children in protection
  institutions (article 16 of Loi 58-23, Décret 2-25-1064);
- the exceptional allowance for households that lost ASD after a CNSS
  declaration (articles 16 bis and 16 bis bis of Loi 58-23, inserted by Loi
  41-26; Décret 2-26-434 fixes its maximum duration at twelve months);
- the exemption from the age condition for a widow caring for a disabled
  child; the widow scenario must be encoded through the eligibility inputs;
- multiple births (the birth grant is not multiplied), cumulation rules,
  scholarship offsets, and institutional or protection cases.

## Legal sources

- [ANSS laws and decrees index](https://www.anss.gov.ma/fr/lois-decrets)
- [ANSS typologies of aid and published amounts](https://www.anss.gov.ma/fr/typologies-d-aides)
- [ANSS eligibility conditions](https://www.anss.gov.ma/fr/conditions-d-eligibilite)
- [Loi n° 58-23 (official ANSS PDF)](https://www.anss.gov.ma/sites/default/files/decrets/Loi_n58.23_AR.pdf),
  especially articles 1–4 and 7–12. Published in BO n° 7253 of 4 December 2023,
  p. 10223. Amended by Loi n° 41-26 (BO n° 7523 of 6 July 2026), which only
  inserts articles 16 bis / 16 bis bis and rewrites article 17.
- [Décret n° 2-23-1067 (official ANSS PDF)](https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1067_AR.pdf),
  article 2 and annex. Published in BO n° 7253 of 4 December 2023. The annex is
  completed by Décret n° 2-24-706 (BO n° 7321 of 29 July 2024); Décret
  n° 2-26-434 (BO n° 7530 of 30 July 2026) inserts article 10 bis into the
  decree body and does not change the annex.
- [Décret n° 2-23-1068 (official ANSS PDF)](https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1068_AR.pdf),
  article 1: the eligibility threshold is fixed at **9,743001** (BO n° 7253 of
  4 December 2023, p. 10239).

Parameter entries carry their own legal references in
`openfisca_morocco/parameters/prestations_sociales/aide_sociale_directe.yaml`.

## Verification notes

The full citation trail behind these statements is kept in
[`docs/aide-sociale-directe-notes/`](aide-sociale-directe-notes/): one note on
the threshold decree and one on the amending texts, including the sources that
could not be read and the points left unverified.

- The threshold value is an exact transcription of the Arabic text
  ("تحدد في 9,743001 عتبة الاستفادة"), not a rounding of the press figure 9.74.
  The decree does not itself use the words "score" or "index": it fixes the
  benefit threshold referred to in article 3(5) of Loi 58-23, which ANSS applies
  to the RSU socio-economic index.
- **The comparison operator is not settled by the decree.** The ANSS
  eligibility page states "inférieur ou égal", while an ANSS presentation of
  November 2024 states "inférieur". The model follows the ANSS page and treats
  `9.743001` as eligible and `9.743002` as not eligible; the boundary case is
  decided administratively, not by the text.
- The published parameters start in December 2023; a simulation for an earlier
  period raises a parameter error rather than returning zero.
- Amounts and scores are stored as single-precision floats. `9.7430014` rounds
  to the same value as the ceiling and is therefore eligible, so the effective
  boundary is about `9.74300145`; on the six-decimal grid the model still treats
  `9.743001` as eligible and `9.743002` as not. A NaN score is ineligible
  because the comparison is false.
- The 2025 column is labelled "à partir de 2025" by ANSS and already appears in
  the annex as published in BO n° 7253 (December 2023), so no separate
  revaluation instrument was identified. The first revaluation was nevertheless
  paid from the end of November 2025: the parameter uses `2025-01-01` as the
  schedule date, and historical outputs before that payment date should not be
  read as amounts actually paid. The exact 2026 payment month was not verified.
- The orphan complement is a separate line in section 2 of the annex
  (150 / 125 / 100 DH); ANSS publishes only the resulting totals, and the two
  reconcile: base plus complement gives the published widow totals
  (350 / 375 / 400 DH).
- Ranks 4–6 and the disability complement are not revalorised in the published
  table; the seventh-child disability amount is 100 DH, without a base amount.
- No amendment of Décret 2-23-1068 was published as of November 2026, and the
  ANSS list of legal texts annotates no modification of it. This is supported by
  the official list and the absence of any trace elsewhere, not by a formal
  certificate of non-amendment.
- The draft Décret n° 2.26.838, adopted by the Council of Government on
  12 November 2026, would raise the floor and the flat allowance from 500 to
  600 DH from 1 January 2027. It had no identified Bulletin Officiel
  publication at the time of writing and is deliberately **not** parameterised.
  A 2027 parameter set will need its own dated entries.

The rule tables are dates of legal effect, not a claim that registry membership
or the administration's operational decisions can be inferred.

## Tests

`openfisca_morocco/tests/aide_sociale_directe.yaml` covers the threshold
boundary, missing administrative confirmation, the flat allowance, child tiers,
explicit ranks, the orphan and disability complements (including ranks 4–6 and
7+), birth grants, and the dated December 2023, 2025 and 2026 schedules.
