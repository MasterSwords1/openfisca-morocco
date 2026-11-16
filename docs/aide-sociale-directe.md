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
an event is supplied for that month. Three related benefits are separate
variables: the September school-return allowance, the special allowance for
children in placement, and the exceptional allowance after a CNSS declaration.

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

### Related ASD benefits

#### School-return allowance — `aide_rentree_scolaire`

Paid only in September: 200 DH per child in primary or lower secondary and
300 DH per child in upper secondary, up to six schooled children (Décret
n° 2-24-706, BO n° 7321 of 29 July 2024). The annex row covers children
**schooled in a public education institution**, so `scolarise_etablissement_public`
is required and defaults to `false`; a private-school child pays nothing.

The six-child limit is applied to the **number** of eligible children, not to
their rank: the decree publishes no ordering rule. Because the two rates
differ, the model keeps upper-secondary children first (300 DH) and then
primary/lower-secondary ones (200 DH), the reading most favourable to the
household. A household with six primary and one upper-secondary child therefore
receives 1,300 DH, not 1,200 DH.

The aid is paid in September if the household is eligible that month **or in
August** — the ANSS describes an early-September payment for August
beneficiaries and an end-September payment for households first eligible in
September. The difference between those two payment dates is not reproduced.
`enfant_scolarise` governs the monthly schedule; `niveau_scolaire_asd` is the
reference input here, and the two can contradict each other if only one is set.

A child hosted in a protection institution is excluded from this aid. That is a
modelling choice to avoid double support: the no-cumulation rule of Décret
n° 2-25-1064 covers the monthly allowance and the complementary support, not
the school-return allowance.

#### Special allowance for children in placement — `aide_speciale_enfant_place`

500 DH per child per month for orphaned or abandoned children hosted in an
authorised protection institution (article 16 of Loi 58-23; Décret n° 2-25-1064,
BO n° 7468 of 25 December 2025). In force 25 March 2026. Because periods are
monthly, March 2026 pays nothing and April 2026 is the first paid month.

Two inputs separate hosting from acceptance: `enfant_place_institution` says the
child is hosted, and `aide_speciale_accordee` says the application was accepted.
The allowance is paid only when both are true, and the household's child
amounts and complements stop when a hosted child's application is accepted, as
article 9 provides. A hosted child whose application is pending therefore still
counts in the household's ASD, and an acceptance flag without hosting does not
stop anything.

A household whose only child is placed and accepted therefore has no child
amount: it receives no household ASD unless it qualifies for the flat
allowance, which still requires `eligible_aide_forfaitaire_asd`; the child
still receives the 500 DH special allowance. The institution's authorisation,
the CDG account in the child's name, the 10,000 DH floor at majority and the
other article 1 conditions (nationality, registry entry, absence of
family-allowance cover, scholarship offset) are administrative facts, not
computed.

#### Exceptional allowance — `prime_exceptionnelle_asd`

For households that lost ASD because the head of household or a spouse was
declared to the private-sector social-security scheme (Loi n° 41-26, BO n° 7523
of 6 July 2026; Décret n° 2-26-434, BO n° 7530 of 30 July 2026). The amount
equals the entitlement the household could have received, granted once for at
most twelve months, continuous or not. The reference amount and the remaining
months are inputs: the model does not decide the CNSS declaration, the loss of
entitlement or the involuntary end of employment.

The twelve-month ceiling is an input contract, not enforced state. The model
does not consume months, does not detect a caller who resets the counter, and
cannot enforce the "granted once" rule. A value above twelve is refused and pays
nothing; a decimal value is truncated by the integer type (12.9 becomes 12). The
model also does not prevent the exceptional allowance and the ordinary monthly
ASD from being computed in the same month, although the law's premise is that
the household lost ASD.

Monthly granularity means July 2026 pays nothing and August 2026 is the first
paid month; the exact entry-into-force day is not prorated.

Article 16 bis bis (re-entry into ASD after the declared employment ends
involuntarily, without the article 7(2) waiting period) has no dedicated rule.
The model applies no waiting period at all, so it cannot distinguish a
legitimate re-entry from a first entry: the re-entry path is not "supported",
it is simply not gated. This is a limitation, not a feature.

Not modelled, and therefore not to be read as an exhaustive entitlement
calculation:

- the exemption from the age condition for a widow caring for a disabled
  child; the widow scenario must be encoded through the eligibility inputs;
- multiple births (the birth grant is not multiplied), the cumulation rules of
  articles 5 and 6, scholarship offsets, and the authorisation of protection
  institutions;
- the article 7(2) waiting period on a first entry, and therefore any
  distinction between a re-entry and a first entry;
- the early/late September distinction within the school-return allowance, and
  any proration of the March and July 2026 entry-into-force months.

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
- Décret n° 2-24-706 of 25 July 2024 (BO n° 7321 of 29 July 2024), completing
  the annex of Décret n° 2-23-1067 with the school-return allowance.
- Décret n° 2-25-1064 of 23 December 2025 (BO n° 7468 of 25 December 2025),
  implementing article 16 of Loi 58-23 for children in protection
  institutions; in force three months after publication.
- Loi n° 41-26 of 25 June 2026 (BO n° 7523 of 6 July 2026), inserting articles
  16 bis and 16 bis bis into Loi 58-23, and Décret n° 2-26-434 of 23 July 2026
  (BO n° 7530 of 30 July 2026), fixing the exceptional allowance at twelve
  months.

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
- The published parameters start in December 2023; a September simulation
  before that date raises a parameter error rather than returning zero, while
  other months return zero before the parameter lookup.
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

The rule tables are dates of legal effect, except the school-return entries,
which carry its September payment dates (first in September 2024), not a claim
that registry membership or the administration's operational decisions can be
inferred.

## Tests

`openfisca_morocco/tests/aide_sociale_directe.yaml` covers the threshold
boundary, missing administrative confirmation, the flat allowance, child tiers,
explicit ranks, the orphan and disability complements (including ranks 4–6 and
7+), birth grants, and the dated December 2023, 2025 and 2026 schedules.

Three further YAML suites and a sequence harness cover the related
benefits:

- `aide_rentree_scolaire.yaml`: September-only payment (an October case pins the
  month), both school levels, the public-school condition, the six-child count
  cap (including ranks 7 and 8 and duplicated ranks), the mixed-level ordering,
  the August cohort, an unset level, a non-eligible child, missing
  administrative confirmation and the exclusion of hosted children;
- `aide_speciale_enfants_places.yaml`: the April 2026 amount, the March
  entry-into-force month, a non-placed child, the pending-application case, and
  the no-cumulation rule against household child amounts;
- `test_prime_exceptionnelle_asd.py` runs the consumption sequence itself: twelve
  continuous months, a thirteenth month at zero, a non-continuous sequence
  (six months paid, two paused, six resumed) and a value above twelve;
- `prime_exceptionnelle_asd.yaml`: payment at twelve remaining months, the July
  2026 non-payment, exhausted months over two consecutive months, an invalid
  value above twelve, a negative reference amount, an unset counter, and a
  household that moves from the prime back to the ordinary monthly ASD in the
  month the counter reaches zero.
