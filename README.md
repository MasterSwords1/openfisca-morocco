# OpenFisca Morocco

[![CI](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml/badge.svg)](https://github.com/MasterSwords1/openfisca-morocco/actions/workflows/ci.yaml)

[OpenFisca](https://openfisca.org) model of Moroccan tax and benefit law, as
code. The project was started from the [OpenFisca Country Template](https://github.com/openfisca/country-template).

**Status: early.** The package models: the **impôt sur le revenu (IR)** on
salarial income for **annual** periods from **1 January 2010**, with the
historical scales and deductions of 2010–2024 and the 2025 reform (before 2016,
pass `cotisations_sociales_obligatoires` explicitly), professional income from
2025 (net-réel input accepted from 2010), and rental, capital,
professional-regime, property and foreign income from 2026 (see
[`docs/impot-revenu-categories.md`](docs/impot-revenu-categories.md)), the **cotisations sociales obligatoires (CNSS + AMO)** and
charges patronales for **monthly** periods, the contributory **allocations familiales (CNSS)**
for **monthly** periods, **aide sociale directe (ASD)** under the published
statutory schedules for **monthly** periods, including the September
school-return allowance and the placement and exceptional allowances, and the
**taxe sur la valeur ajoutée (TVA)**
declared by an enterprise for **monthly** periods, with dated rates running **2004–2026**, and **registration duties and land-conservation fees** on real-estate acquisitions and company capital from 2026.
ASD eligibility inputs and registry limitations are documented in
[`docs/aide-sociale-directe.md`](docs/aide-sociale-directe.md).

| | |
|---|---|
| Country | Morocco |
| Currency | dirham (MAD), `currency-MAD` |
| Entities | `Person`, `Household`, `Company` |
| Periods | `YEAR` (IR), `MONTH` (TVA, Cotisations sociales, Allocations familiales, Aide sociale directe) |
| First modelled period | 2004-01-01 (TVA), 2010-01-01 (IR with supplied contributions), 2016-01-01 (CNSS/AMO employee and employer), 2019-07-01 (Allocations familiales amounts), 2023-12-01 (Aide sociale directe) |
| Licence | AGPL-3.0-or-later |

## What is modelled

The IR pipeline of the Code Général des Impôts (CGI), in the order the law
applies it:

```
salaire_brut_global − elements_exoneres            (art. 56, 57)
    = salaire_brut_imposable
    − cotisations_sociales_obligatoires             (art. 58)
    − frais_professionnels                          (art. 59)
    = salaire_net_imposable
    + revenu_professionnel_net                      (arts. 30–39)
    + revenus_fonciers_bruts × (1 − 40 %)           (art. 64-II)
    + revenu_etranger_imposable (gross, 2026+)       (art. 25)
    = revenu_global_imposable
    → ir_brut via the progressive scale             (art. 73-I)
    − deduction_charges_famille                     (art. 74)
    − retenue_fonciere (capped at the tax due)      (arts. 73-II, 160 bis)
    = impot_sur_le_revenu  (floored at 0)
```

The professional-expense forfait is computed on `salaire_brut_imposable`
(art. 59-I), not on the balance after social contributions; the contributions
are a separate deduction (art. 59-II).

Dividends, fixed-income interest and capital gains are taxed at liberatory rates
outside this barème; `impot_capitaux_mobiliers` reports them and
`impot_sur_le_revenu_menage` sums the individual liabilities.

### Coverage table

| CGI article | Provision | Variables | Parameters | From |
|---|---|---|---|---|
| 56 | Salaries, wages, benefits in cash or in kind | `salaire_brut_global` (input) | — | 2010-01-01 |
| 57 | Exempt elements of pay | `elements_exoneres` (input) | — | 2010-01-01 |
| 58 | Compulsory social contributions borne by the employee | `cotisations_sociales_obligatoires` (input) | — | 2010-01-01 |
| 56–58 | Gross taxable pay | `salaire_brut_imposable` | — | 2010-01-01 |
| 59 | Forfaitary professional-expense deduction | `frais_professionnels` | `impot_revenu.frais_professionnels` | 2010-01-01 |
| 58–59 | Net taxable pay (the scale's base) | `salaire_net_imposable` | — | 2010-01-01 |
| 73-I | Progressive annual scale | `ir_brut` | `impot_revenu.bareme` | 2010-01-01 |
| 74 | Family-charge deduction | `deduction_charges_famille` | `impot_revenu.deduction_charges_famille` | 2010-01-01 |
| 74 | Net income tax payable | `impot_sur_le_revenu` | — | 2010-01-01 |

The figures, for reference:

- **Scale, 2010–2024 (art. 73-I, LF 2010):** 0 % up to 30 000 DH, then 10 %
  (30 001–50 000), 20 % (50 001–60 000), 30 % (60 001–80 000), 34 %
  (80 001–180 000), 38 % above.
- **Scale, from 2025 (art. 73-I, LF 2025):** 0 % up to 40 000 DH, then 10 %
  (40 001–60 000), 20 % (60 001–80 000), 30 % (80 001–100 000), 34 %
  (100 001–180 000), 37 % above.
- **Professional expenses (art. 59):** 20 % of gross taxable pay before social
  contributions, capped at 30 000 DH, from 2010 to 2022; 35 % up to 78 000 DH
  and 25 % above, capped at 35 000 DH, from 2023. The 78 000 DH threshold is a
  switch, not a progressive band: 78 001 DH moves the whole forfait to 25 %.
- **Family charges (art. 74):** 360 DH per dependent from 2010 to 2024, 500 DH
  in 2025 and 600 DH from 2026, at most 6 dependents (2 160 DH maximum to 2024,
  3 000 DH in 2025, 3 600 DH from 2026).

`birth` and `age` are also available: they are factual demographics, not
legislation, and carry no legal reference. Moroccan age-based provisions will
build on them.

## What is modelled — TVA

The VAT declaration of an enterprise, on the `Company` entity, for **monthly**
periods (CGI article 112):

```
chiffre_affaires × taux par taux déclaré        (art. 98, 99, 247-XXXXI)
    + tva_collectee_article100
    = tva_collectee_totale
(tva_deductible_charges + tva_deductible_immobilisations)
    × prorata_deduction                          (art. 101, 104)
    + credit_tva_anterieur
    = tva_deductible_autorisee
tva_collectee_totale − tva_deductible_autorisee
    = tva_nette_a_payer / credit_tva_a_reporter  (floored at 0)
```

### Dated rates, not a flat triple

| Period | General rates | Legal basis |
|---|---|---|
| 2004-01-01 → 2023-12-31 | 20 % · 14 % · 10 % · 7 % | Loi n° 30-85, then CGI arts. 98–99 (loi n° 43-06) |
| 2024-01-01 → 2026-12-31 | 20 % · 10 % | CGI art. 99 rewritten by loi de finances n° 55-23; art. 98 abrogated |

The four-rate structure ends on **1 January 2024**, not in 2026: the 2024
finance law rewrites article 99 as `A) 20 %` / `B) 10 %` and abrogates article
98. The 7 % and 14 % parameters therefore stay declared (so 2004–2023 can be
simulated) but carry `en_vigueur = 0` from 2024-01-01, and a chiffre d'affaires
declared on those brackets is reported separately in
`chiffre_affaires_taux_abroge` instead of being taxed at an abrogated rate.

### Article 100 specific rates

The model also computes the Article 100 taxes for quantities that the caller
has already classified under that article. It uses hectolitres for wines and
alcoholic beverages sold otherwise than for consumption on the premises, and
grams of gold/platinum or silver contained in the relevant articles. The amount is included in
`tva_collectee_totale`.

| Effective period | Wine/alcohol | Gold/platinum | Silver |
|---|---:|---:|---:|
| 2007-01-01 → 2010-12-31 | 100 DH/hl | 4 DH/g | 0.05 DH/g |
| 2011-01-01 → 2019-12-31 | 100 DH/hl | 5 DH/g | 0.10 DH/g |
| From 2020-01-01 | Article 100 repealed | Article 100 repealed | Article 100 repealed |

The exact rate periods and amendment quotes are available from
`openfisca_morocco.tva_article100`. `quantites_article100_hors_periode` flags
non-zero quantities before 2007 or from 2020 onward. The catalog does not
reconstruct the pre-CGI regime or decide how a transaction is taxed after the
2020 repeal; use the law in force for that transaction.

### Transitional rates, 2024–2026

Article 247-XXXXI gives seven operation categories their own glide path. They
are selected by the `tva_operation_transitoire` input, and they are *not*
general rates:

| Operation (`tva_operation_transitoire`) | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| `electricite` | 16 % | 18 % | 20 % |
| `compteur_electricite` | 11 % | 15 % | 20 % |
| `electricite_renouvelable` | 12 % | 10 % | 10 % |
| `sucre` | 8 % | 9 % | 10 % |
| `transport_hors_urbain_et_routier` | 16 % | 18 % | 20 % |
| `transport_urbain_et_routier` | 13 % | 12 % | 10 % |
| `courtier_assurances` | 12 % | 10 % | 10 % |

Water and sanitation have no glide path: 10 % from 1 January 2024
(art. 247-XXXXI-A). Before 2024 no transitional rate exists, and
`tva_taux_transitoire` returns 0 rather than an invented value.

### What the TVA module does not do

It does **not** choose an exemption or rate from an arbitrary product
description. Quote-backed Article 91, Article 92 and Article 99 catalogs are
available for the consolidated editions 2007, 2010, 2014, 2018, 2021, 2024 and
2026. Each entry must be requested by its exact edition year and item ID. The
returned quote, rate or exemption treatment, item ID and source path let a
caller inspect the clause. The catalogs do not classify a transaction.

Both exemption catalogs are itemized. Article 91 and 92 expose two levels: the
article-level context and numbered clauses (`list_article_91_items`,
`list_article_92_items`), and the nested bullets and letters printed beneath a
clause (`list_article_91_subitems`, `list_article_92_subitems`). Each sub-item
names the clause it sits under through `parent_item_id`, so a leaf is addressed
directly instead of being flattened into a parent quotation. Article 99 exposes
its `billable_leaf` rows the same way through `list_article_99_subitems`. A
clause the consolidated text prints as `(abrogé)` is retained with
`is_abrogated` true rather than dropped.

`aggregate_article_99_turnover` maps caller-selected exact Article 99 item IDs
to summed taxable bases by rate. It does not take product descriptions as
input. Items that cite a separate Article 247 transitional schedule are
rejected so their turnover can be entered through `tva_operation_transitoire`.

Article 91 entries preserve exemptions without a right to deduct, while
Article 92 entries preserve exemptions with a right to deduct. They are
provided for explicit caller review and do not automatically calculate
`prorata_deduction`.

The CGI Article 99 catalog has **no 2004 edition**. Article 91 and 92 remain
snapshot-only: their rows carry no effective dates, so an edition year must
never be read as a validity period. A separate pre-CGI Article 15 catalog below
records the lists as of 1 January 2004 and 1 January 2005; it is not part of
Article 99 or the 2006 LAR Article 101 snapshot.

Article 99 rows **do** carry effective dates, but only where a primary source
names the instrument. Each row exposes `effective_attribution`: a rate segment
whose start and end are dated independently. A boundary is either `proven`
(amending instrument, artifact, SHA-256 and a verbatim quote) or `bracketed`
with a machine-readable reason and no date at all. 299 of the 420 rows
(71,2 %) are fully proven; the other 121 cannot be priced on a specific day and
a date query refuses them rather than guessing.

To enumerate the documented clauses for an exact snapshot, then retrieve one
item directly:

```python
from datetime import date
from decimal import Decimal

from openfisca_morocco.tva_article99 import (
    aggregate_article_99_turnover,
    get_article_99_item,
    list_article_99_items,
)

items = list_article_99_items(2024)
print([(item.item_id, item.rate) for item in items])
item = get_article_99_item(2024, "2024-art99-general-20pct")
print(item.rate)  # "20%"
print(item.quote)  # verbatim clause from the 2024 edition
print(item.corpus_file)  # source text path in morocco-holy-graph
print(item.source_endnote_labels)  # tuple of catalog labels, or None
print(item.amendment_citations[0].law)  # cited finance law, when available
print(item.amendment_citations[0].amending_law_corpus_file)

# The dated segment this row belongs to.
attribution = item.effective_attribution
print(attribution.status)  # "proven" or "bracketed"
print(attribution.valid_from, attribution.valid_to)  # valid_to is exclusive
print(attribution.covers(date(2024, 6, 1)))

turnover_by_rate = aggregate_article_99_turnover(
    2024,
    {
        "2024-art99-general-20pct": Decimal("1000"),
        "2024-art99-10pct-001": Decimal("500"),
    },
    on_date=date(2024, 6, 1),  # optional: price only proven-to-apply items
)
print(dict(turnover_by_rate))  # 20%: 1000 MAD; 10%: 500 MAD
```

Article 91 and 92 have separate exact-snapshot lookups:

```python
from openfisca_morocco.tva_article91_92 import (
    get_article_92_item,
    get_article_92_subitem,
    list_article_91_items,
    list_article_92_subitems,
)

exemptions_without_deduction = list_article_91_items(2026)
export = get_article_92_item(2026, "2026-art92-clause-001")
print(export.right_to_deduct)  # True
print(export.quote)  # source quotation for the clause itself

leaves = list_article_92_subitems(2007)
leaf = get_article_92_subitem(2007, "2007-art92-clause-020-sub-1")
print(leaf.parent_item_id)  # the clause the bullet sits under
print(leaf.nesting_depth)  # 1 for a bullet directly under a clause
print(leaf.quote)  # the bullet's own text, not the parent's
```

The package-local source catalog is
`openfisca_morocco/data/tva_article91_92_catalog.json` (schema version 2). It is
a verbatim projection of one Holy Graph dataset: 606 article-level and numbered
clause rows plus 603 nested sub-item rows across the seven snapshots, each row
keeping its corpus `item_id` and quote byte-for-byte. Sub-items get a stable
ASCII ID of the form `<parent>-sub-<n>`; the corpus ID they came from is kept as
`source_item_id`. 45 of the 606 top-level rows and 11 of the 603 sub-items are
printed `(abrogé)` in their edition and are retained as `abrogated`. Snapshots
mark an edition, never a validity period, and the Articles are re-checked by
`scripts/build_tva_article91_92_catalog.py --check`, which recomputes the
projection and fails if the artifact is stale or a quote no longer matches the
corpus.

`list_article_99_items` preserves the source order and returns an immutable
tuple. The package-local catalog is
`openfisca_morocco/data/tva_article99_catalog.json`.
It retains source quotes and provenance but omits the source's one-day
`as_of`, `valid_from` and `valid_to` snapshot markers, which are not validity
periods. Real dates live only inside `effective_attribution`, never on the
snapshot row. When the source quote or parent qualification contains a
verifiable endnote marker, the returned `amendment_citations` includes the named
law/article, citation scope, pinned source hashes, and the amending-law excerpt.
Page-footer notes with ambiguous item association are not linked by proximity.
A clause that the corpus splits into several `billable_leaf` rows is exposed
through `list_article_99_subitems`; a sub-item has no date of its own and
returns its parent's `effective_attribution` object rather than a copy.
`conditions` are projected verbatim from the corpus, including the six
`exclusion` qualifiers that narrow a listed clause.
The catalog is generated by `scripts/build_article99_attribution.py`; `--check`
fails when the packaged artifact is stale.

### Historical Loi 30-85 Article 15 snapshots

The package also provides distinct Article 15 lists from the former TVA law,
Loi n° 30-85, as of **1 January 2004** and **1 January 2005**. The API preserves
the catalog's 40 and 41 source-ordered quoted items, rates, deduction flags,
conditions, item IDs, source paths, and available endnote and Gazette
amendment citations. These are point-in-time lists; the dates do not imply
continuous validity before, between, or after the snapshots. The API does not
classify products from descriptions or decide which rate applies to a
transaction.

The 2002 DGI compilation used as the baseline is available in this project as
a text-layer transcription from a Scribd-hosted copy, not as locally pinned
DGI or SGG PDF bytes. The 2004 and 2005 amendment excerpts are transcribed from
locally pinned Official Gazette scans and visually checked. The source catalog
records a review of the 2003 Finance Law amendment list and the DGI 2014
reference table; neither identifies an additional non-finance Article 15
amendment. Because the project does not contain the complete 2002–2005 Gazette
run, this search cannot establish an exhaustive negative. The catalog exposes
the reviewed sources and their limitations for callers.

```python
from openfisca_morocco.tva_article15 import (
    get_article_15_item,
    get_article_15_snapshot,
    list_article_15_items,
)

snapshot = get_article_15_snapshot(2005)
print(snapshot.as_of)  # "2005-01-01", a snapshot date
print(len(list_article_15_items(2005)))  # 41
item = get_article_15_item(2005, "2005-art15-10pct-deduct-007")
print(item.article, item.rate, item.quote)  # Article 15, not Article 99
print(item.amendment_citations[0].source_url)
```

The package-local catalog is
`openfisca_morocco/data/tva_article15_catalog.json`. It retains the source
chain audit and acquisition caveats alongside the quoted lists.

The Article 15 lists document two historical snapshots but do not provide a
continuous history. The absence of continuous validity and the other open
corpus gaps remain blockers for issue
[#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6); the corpus work is tracked in
[morocco-holy-graph#80](https://github.com/MasterSwords1/morocco-holy-graph/issues/80).

### Separate 2006 LAR Article 101 snapshot

The package also contains the complete quoted Article 101 list from the
*Livre d’Assiette et de Recouvrement 2006*. It is exposed through a separate,
fixed-snapshot API and is never included in the CGI Article 99 catalog. The
LAR states in Article 212 that its provisions apply from 1 January 2006, and
Article 213 repeals Loi n° 30-85. This remains a distinct source from the 2004
and 2005 Article 15 snapshots and does not establish continuous item validity.

The snapshot contains 38 items: 14 at 7%, 16 at 10%, and 8 at 14%. It retains
the verbatim quotes, Article 101 rate headings, item conditions, deduction
treatment, corpus path, source PDF and extracted-text SHA-256 hashes, source
and retrieval URLs, and the Article 212/213 citations. The retrieval note
states that the local mirror is incomplete at the tail (235 of 241 printed
folios), while the complete Article 101 pages 95–98 were visually checked and
the DGI-hosted edition was also checked. The package does not claim that the
mirror bytes are identical to the DGI-hosted PDF.

The same snapshot now names a live primary source: Bulletin officiel n° 5382
bis (27 kaada 1426 / 29 December 2005), which promulgated loi de finances
n° 35-05. Fetched on 2026-11-14 from
`https://www.sgg.gov.ma/BO/bo_fr/2005/BO_5382-bis_fr.pdf`, the served PDF is
byte-identical to the corpus copy, so the Article 101 wording is checkable
against the enacting text. That comparison also confirms the item list: 37 of
38 rows match the bulletin OCR at 95% token coverage or better, and the last
differs only by `rebia`/`rabii`.

One naming hazard is recorded in the artifact: the 2006 text numbers the TVA
rate articles 99 (base by prior agreement), 100 (20% normal rate), 101
(reduced rates) and 102 (specific rates), whereas the 2007 and later editions
number the same four articles 97, 98, 99 and 100. A 2006 "Article 100" is
therefore *not* the specific-rate article exposed by `tva_article100`.

```python
from openfisca_morocco.tva_article101 import (
    get_lar_2006_article_101_item,
    get_lar_2006_article_101_snapshot,
    list_lar_2006_article_101_items,
)

snapshot = get_lar_2006_article_101_snapshot()
print(snapshot.effective_from)  # "2006-01-01", cited to LAR article 212
print(snapshot.source_pdf_sha256)
print(len(list_lar_2006_article_101_items()))  # 38
print(snapshot.corroborating_source.url)  # live Bulletin officiel PDF
print(snapshot.corroborating_source.article_numbering_note)
item = get_lar_2006_article_101_item("2006-art101-7pct-001")
print(item.article, item.rate, item.quote)  # Article 101, not CGI Article 99
```

The package-local source artifact is
`openfisca_morocco/data/tva_lar_2006_article101.json`.

For a transaction already assigned to an Article 100 category, the monthly
calculation accepts physical quantities directly:

```python
from datetime import date

from openfisca_morocco.tva_article100 import calculate_article_100_tax

tax = calculate_article_100_tax(date(2011, 1, 1), gold_platinum_g=3, silver_g=10)
print(tax)  # Decimal('16.00')
```

The OpenFisca variables are `volume_vins_boissons_alcoolisees_article100`,
`grammes_or_platine_article100`, and `grammes_argent_article100`. These inputs
should only contain quantities the caller has determined fall under Article
100. The total declaration includes their calculated tax for the verified
2007–2019 period.

## Provenance

Every modelled figure is traceable to a published text, and every input variable
names the article it comes from.

| Piece | Source |
|---|---|
| Code Général des Impôts (arts. 1–248) | Loi n° 43-06, Dahir n° 1-06-232 of 31 December 2006, *Bulletin Officiel* n° 5487 bis of 31 December 2006, pp. 4153–4210 |
| Art. 73-I scale in force in 2025 | Loi de finances n° 60-24 for the 2025 budget year, Dahir n° 1-24-65 of 13 December 2024, *Bulletin Officiel* n° 7362 bis of 19 December 2024 |
| Art. 73-I scale for 2010–2024 | Loi de finances n° 48-09 for the 2010 budget year, *Bulletin Officiel* n° 5800 bis of 31 December 2009; the same scale appears in the 2010, 2014, 2018, 2021 and 2024 consolidated CGI editions |
| Arts. 59 and 74 figures | CGI arts. 59 and 74, read in the 2010, 2014, 2018, 2021 and 2024 consolidated editions and in Lois de finances n° 40-08 (BO n° 5695 bis), n° 48-09 (BO n° 5800 bis), n° 50-22 (BO n° 7154 bis), n° 60-24 (BO n° 7362 bis) and n° 50-25 (BO n° 7465 bis) |
| TVA rates 2004–2026 | `morocco-holy-graph`, verified dataset `laws/ma_tax_law/data/tva_rate_history.json` (PR #81), where every rate carries a literal quote from the finance-law text layer; cross-checked by `openfisca_morocco/tests/test_tva_taux.py` |
| Article 99 catalog entries | Consolidated snapshots in `laws/ma_tax_law/data/consolidated/tva_article_lists.json`; the package artifact preserves each selected item's quote, rate, ID and corpus path for snapshots 2007, 2010, 2014, 2018, 2021, 2024 and 2026. It has no CGI Article 99 edition for 2004. Effective dates are derived per boundary by `scripts/build_article99_attribution.py` from the seven consolidated editions and the fifteen finance-law transcriptions, and each dated boundary names its instrument, artifact, SHA-256 and verbatim quote. |
| Articles 91 and 92 exemption entries | Consolidated snapshots from the same parsed source catalog for 2007, 2010, 2014, 2018, 2021, 2024 and 2026; 606 article-level and numbered-clause rows plus 603 nested sub-item rows retain their quotes, deduction treatment and printed `(abrogé)` status. Projected verbatim by `scripts/build_tva_article91_92_catalog.py`; snapshots do not establish continuous validity. |
| Article 100 specific rates | Five source-backed rate periods from the same catalog, with the 2011 metal-rate amendment and 2020 repeal cited. The model applies the per-unit rates only for 2007–2019 and flags non-zero quantity inputs outside that coverage. |
| Historical Loi 30-85 Article 15 | `historical_article15_2004_2005` in the same corpus dataset; the separate package artifact preserves the 2004/2005 snapshot items, quotes, conditions, available amendment citations and reviewed source-chain evidence. The available-source review found no additional non-finance amendment, but the 2002 DGI baseline PDF is not pinned and the incomplete Gazette run prevents an exhaustive negative. |
| 2006 LAR Article 101 snapshot | `historical_2006_article101` in the same corpus dataset; the separate package artifact retains all 38 quotes, conditions, deduction flags, PDF and text hashes, source URLs, checked pages, and LAR Articles 212/213 citations. It remains a separate 2006 source and does not extend the Article 99 catalog. |
| TVA declaration arithmetic | CGI arts. 98, 99, 101, 104 and 247-XXXXI as encoded in the validated Catala model `laws/ma_tax_law/catala/cgi_tva.catala_fr` and its test `test_tva_multi_rate_and_deductions` (257 000 / 150 000 / 107 000). Article 100 is separately checked against its historical consolidated text and amendment citations. |
| Social contributions (CNSS & AMO) | `morocco-holy-graph`, module `ma_social_protection` (CSOC), dataset `laws/ma_social_protection/data/social_security_rates.json` citing Dahir 1-72-184, Décret 2-02-175, Loi 03-14, Loi 30-97, Loi 65-00 et Décrets 2-05-734 / 2-14-707 |
| Allocations familiales (CNSS) | Dahir portant loi n° 1-72-184 (articles 40 et 41), Décret n° 2-72-541 art. 6 (âges), Décret n° 2-08-358 modifié par les décrets n° 2-19-750 et n° 2-23-715 (montants) |
| Registration duties and conservation fees | CGI 2026 arts. 127–155 (BO n° 5487 bis codification) with rates from Lois 38-07 (BO n° 5591 bis), 22-12 (BO n° 6048), 73-16 (BO n° 6577 bis), 115-12 (BO n° 6113 bis), 65-20 (BO n° 6944 bis) and 50-25 (BO n° 7465 bis); Décret n° 2-16-375 (BO n° 6484) for conservation; 4 % built, 5 % vacant land, 6 % fonds de commerce, 0.5 %/1,000 DH capital, 1.5 % + 100 DH conservation (500 DH minimum) |
| IR categories | CGI 2026 arts. 12, 25, 28, 30–44, 61–65, 66–69, 73 and 160 bis, read in the 2026 consolidated edition; category parameters start in 2026, professional net-réel income whenever the barème exists (2010 onward) |
| Aide sociale directe (ASD) | Loi n° 58-23 (BO n° 7253), Décrets n° 2-23-1067 / 2-23-1068, 2-24-706 (BO n° 7321), 2-25-1064 (BO n° 7468), Loi n° 41-26 (BO n° 7523) and Décret n° 2-26-434 (BO n° 7530), with the ANSS published schedules; parameter references carry the BO number and date |
| Parameter values | `metadata.reference` (title + href) on each parameter, or on each of its dated values, under `openfisca_morocco/parameters/` — enforced by `openfisca_morocco/tests/test_parameter_provenance.py` |

The corpus is the source of truth for this package: figures are taken from
`morocco-holy-graph`, not from memory or from unversioned web pages. Where a
controlling text has not been captured (for example IR before 2010, or the
pre-2025 amendments to other IR categories), the limitation is stated below
rather than guessed.

## Limitations

Stated plainly, because they determine what you may conclude from a simulation:

- **Partial IR categories (IR).** The model covers the professional regimes,
  art. 28 deductions, property gains and foreign income from 2026, but the
  per-client 80,000 DH withholding, the regime option procedures, treaty relief
  and foreign tax credits are not modelled, so this is still not a complete IR.
  See [`docs/impot-revenu-categories.md`](docs/impot-revenu-categories.md).
- **Annual assessment only (IR).** Salary inputs are monthly and are summed
  before applying the annual IR scale. Monthly withholding (retenue à la
  source) is not modelled; annual tax divided by twelve is not a withholding
  calculation.
- **Historical IR covers salarial income, plus any professional net-réel
  income you supply.** The 2010–2024 scale, professional-expense deduction and
  family-charge deduction are encoded. The historical professional-regime
  deductions and ceilings are not, and rental, capital, property and foreign
  income remain 2026-only; those categories raise before 2026.
- **Historical payroll contributions start in 2016.** The employee and
  employer CNSS/AMO chains need parameters from 2016-01-01. For 2010–2015,
  supply `cotisations_sociales_obligatoires` explicitly; otherwise the
  contribution layer raises before the IR is calculated. The family-allowance
  benefit amounts start in 2019-07; the 6.40 % employer contribution rate is
  encoded from 2009-01-01.
- **CNSS family-allowance eligibility is input-driven.** The model pays only
  for `children`-role members with a known birth date who are under 12; 12–20
  and declared `enfant_scolarise_cnss` (or its subset
  `enfant_etudes_superieures_cnss`, a study variant); 12–17 and declared `enfant_apprenti_cnss`;
  or disabled (`enfant_handicape_cnss`, asserted by the caller to date from
  before the applicable age limit) and without income
  (`enfant_handicape_sans_revenu_cnss`). The 108-day affiliation condition,
  Moroccan residence, the under-12 “charge exclusive et effective” condition,
  the **60 % SMIG/SMAG salary condition** and the art. 6(e) girl/sister case
  are not modelled. A child without a birth date defaults to 1970 and is
  excluded from the age-based bands; the disability branch can still apply.
  Dependent adults and disabled children must be placed in the `children`
  role.
- **CNSS family-allowance amounts before 2019-07 are not modelled.** The package starts
  with the 2019-07 parameters (300 DH for ranks 1–3, 36 DH for ranks 4–6); the
  1972–2019-06 schedule, including the former 200 DH first-tier amount, is not
  encoded.
- **CNSS family-allowance amounts changed in 2023.** The 4th–6th child amount
  is 36 DH/month from 2019-07 to 2022-12 and 100 DH/month from 2023-01-01,
  following the retroactive effect of Décret n° 2-23-715 (BO n° 7453); the
  maximum for six children is therefore 1,200 DH/month from 2023.
- **Professional-expense special categories and benefits in kind are not
  modelled.** Every salaried person gets the general 20 % / 35 % / 25 % rate;
  the art. 59 B/C rates for casino staff, journalists, sales representatives,
  merchant navy and similar categories are absent. The forfait base is the
  whole gross taxable pay, although art. 59 excludes benefits in cash or in
  kind from that base.
- **IR before 2010 is not modelled.** Earlier scales, rates and thresholds are
  not encoded; an IR simulation for 2009 or before raises an error.
- **TVA category history is snapshot-scoped.** Articles 91, 92 and 99 support
  exact item IDs for editions 2007, 2010, 2014, 2018, 2021, 2024 and 2026; they
  do not classify descriptions or fill the periods between snapshots. The
  separate Article 15 snapshots cover 2004 and 2005, and the LAR Article 101
  snapshot covers 2006. These sources do not establish a continuous
  transaction-to-category history for every month from 2004 onward. See
  [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6) and
  [morocco-holy-graph#80](https://github.com/MasterSwords1/morocco-holy-graph/issues/80).
- **Article 100 has bounded coverage.** The model applies its verified specific
  rates from 2007 through 2019. Its pre-2007 predecessor regime is not encoded:
  the 2006 text does contain the same specific rates but numbers them Article
  102, with 99/100/101/102 where 2007+ has 97/98/99/100, so exposing them as
  Article 100 would conflate the two numberings (see
  `docs/evidence/bo-5382-bis-2006-tva-rates.ocr.txt`). Article 100 was repealed
  in 2020 and later treatment is not inferred from its former rates. Non-zero
  quantities outside the verified interval are flagged.
- **TVA before 2004 is not modelled.** The rate dataset starts on 1 January
  2004; before that date the parameters return the 2004 regime.
- **No import or export VAT.** Domestic VAT is modelled; import/export
  procedures are not. Registration duties and the Article 100 specific rates
  are modelled, with the coverage limits stated above. See issue
  [#6](https://github.com/MasterSwords1/openfisca-morocco/issues/6).
- **Aide sociale directe models published rules, not registry membership.** The
  package takes the RSU index and the administrative conditions as inputs; it
  does not compute the index, decide RNP/RSU registration, or reproduce an ANSS
  award. The September, placement and exceptional allowances are separate
  variables, and their entry-into-force months are not prorated. See
  [`docs/aide-sociale-directe.md`](docs/aide-sociale-directe.md).
- **No microdata.** The package computes on situations you provide; it ships no
  survey or administrative dataset.
- **Not published on PyPI yet.** Install from source (below) until issue
  [#12](https://github.com/MasterSwords1/openfisca-morocco/issues/12) is closed.

## Install

Requires Python 3.9 or later (CI runs 3.13) and
[uv](https://docs.astral.sh/uv/).

The package is not on PyPI yet, so install it from source:

```sh
git clone https://github.com/MasterSwords1/openfisca-morocco.git
cd openfisca-morocco
uv sync --locked --all-extras --dev
```

Check that it works:

```sh
make test
# openfisca test --country-package openfisca_morocco openfisca_morocco/tests
# 494 passed (plus 306 pytest tests; 489/301 without the corpus)
```

The five TVA corpus tests run when `../morocco-holy-graph` exists or
`MOROCCO_HOLY_GRAPH` points to it; a bare clone skips them and reports
484 OpenFisca / 296 pytest tests.

Once published, installation will be `uv add openfisca-morocco`.

## Use it

### From Python

```python
from openfisca_core.simulations import SimulationBuilder
from openfisca_morocco import CountryTaxBenefitSystem

tax_benefit_system = CountryTaxBenefitSystem()
monthly_pay = {f"2025-{month:02d}": 10_000 for month in range(1, 13)}

simulation = SimulationBuilder().build_from_dict(
    tax_benefit_system,
    {
        "persons": {
            "Salarie": {
                "salaire_brut_global": monthly_pay,
                "salaire_brut": monthly_pay,
                "nombre_personnes_a_charge": {"2025": 0},
            }
        },
        "households": {"_": {"adults": ["Salarie"]}},
    },
)

print(simulation.calculate("salaire_brut_global", "2025-01"))  # [10000.]
print(simulation.calculate_add("salaire_brut_global", "2025"))  # [120000.]
print(simulation.calculate("impot_sur_le_revenu", "2025").round(2))  # [7218.72]
```

All monetary amounts are in Moroccan dirhams (MAD). Monthly salary inputs
are summed over the requested calendar year; the annual expense thresholds,
caps, tax brackets and family deduction are applied once to that total.

### Period conventions

The periods of every variable family are:

| Variables | Definition period | Convention |
|---|---|---|
| `birth` | `ETERNITY` | A fixed birth date. |
| `age` | `MONTH` | Age at the start of the month, in completed years. |
| `salaire_brut_global`, `elements_exoneres` | `MONTH` | Gross remuneration and exempt elements for that month, used for IR. |
| `salaire_brut` | `MONTH` | The salary base subject to CNSS/AMO contributions for that month. |
| All other variables in `variables/cotisations_sociales.py` | `MONTH` | Monthly employee/employer contributions and employer cost; CNSS ceilings apply separately each month. |
| `cotisations_sociales_obligatoires` | `YEAR` | Sum of monthly employee contributions, or an explicit annual deduction override (including other mandatory contributions). |
| `nombre_personnes_a_charge` | `YEAR` | Count of spouse and dependent children used for the annual IR deduction; never divided by twelve. |
| `salaire_brut_imposable`, `frais_professionnels`, `salaire_net_imposable`, `ir_brut`, `deduction_charges_famille`, `impot_sur_le_revenu` | `YEAR` | Annual IR bases, deductions and tax. |
| `nombre_enfants`, `allocations_familiales` | `MONTH` | Eligible child count and monthly allowance. |
| `enfant_scolarise_cnss`, `enfant_apprenti_cnss`, `enfant_etudes_superieures_cnss`, `enfant_handicape_cnss`, `enfant_handicape_sans_revenu_cnss` | `MONTH` | CNSS eligibility flags; declare them for every month they apply, because a one-month value does not carry over. |
| All variables in `variables/tva.py` | `MONTH` | Company declaration amounts, physical quantities, category choices and calculated TVA for that month. |

The two gross salary inputs are **distinct bases**. `salaire_brut_global`
feeds IR; `salaire_brut` feeds CNSS/AMO. Supply both when both apply, as in the
example above. Supplying only `salaire_brut_global` does not infer contribution
liability. Without an annual override, `cotisations_sociales_obligatoires`
sums the contributions calculated from `salaire_brut`.

**Compatibility with annual inputs:** `salaire_brut_global`,
`elements_exoneres` and `salaire_brut` use `set_input_divide_by_period`.
For example, `"salaire_brut_global": {"2025": 120_000}` means an **annual
total** distributed over twelve months (10,000 each), not 120,000 per month.
Quarter or multi-month totals are likewise distributed over their months.
When monthly details and a larger-period total are supplied together, the
larger-period total's remainder is divided over the unspecified months.
Supply actual monthly contribution salaries when they vary: splitting an
annual total evenly can change the effect of the monthly CNSS ceiling.

The existing annual YAML scenarios and the bundled `salarie.json` example
remain valid without migration. Python callers that previously read
`simulation.calculate("salaire_brut_global", "2025")` (or
`elements_exoneres`) should now use `calculate_add(..., "2025")` for an
annual total, or `calculate(..., "2025-01")` for one month. Annual IR outputs
still use `calculate(..., "2025")`. Missing monthly salary inputs default
to zero; entering one month does not repeat it across the year.

For VAT, the entity is the company and the period is a month:

```python
simulation = SimulationBuilder().build_from_dict(
    tax_benefit_system,
    {
        "persons": {"Gerant": {}},
        "companies": {
            "Entreprise": {
                "membres": ["Gerant"],
                "chiffre_affaires_taux_normal": {"2024-06": 1_000_000},
                "chiffre_affaires_taux_reduit_10": {"2024-06": 500_000},
                "tva_deductible_charges": {"2024-06": 120_000},
                "tva_deductible_immobilisations": {"2024-06": 30_000},
            }
        },
    },
)

print(simulation.calculate("tva_collectee_totale", "2024-06"))  # [250000.]
print(simulation.calculate("tva_deductible_autorisee", "2024-06"))  # [150000.]
print(simulation.calculate("tva_nette_a_payer", "2024-06"))  # [100000.]
```

`membres` is the single role `Company` declares; it only records that a person
is attached to the company, and no formula reads it.

### From the Web API

```sh
make serve-local   # openfisca serve --country-package openfisca_morocco
```

Then, in another terminal:

```sh
curl "http://localhost:5000/spec"          # OpenAPI specification

curl -X POST -H "Content-Type: application/json" \
  -d @./openfisca_morocco/situation_examples/salarie.json \
  http://localhost:5000/calculate
```

The bundled example answers `"impot_sur_le_revenu": {"2025": 25800.0}`.

### Situation examples

`openfisca_morocco/situation_examples/` holds ready-to-serve situations. Each
file requests its outputs, so the Web API computes them:

- `salarie.json` — the original single-salaried example (25,800 DH of IR);
- `salarie_exonere.json` — below the exemption threshold, IR 0;
- `salarie_impose.json` — above the threshold, with one dependent;
- `couple_avec_enfants.json` — two earners and two children;
- `haut_revenu.json` — a high earner at the top bracket;
- `cout_employeur.json` — salary, CNSS/AMO and employer cost;
- `menage_asd.json` — a household receiving the direct social support.

Every file is simulated by `tests/situations/`.

### Reform examples

```python
from openfisca_morocco import CountryTaxBenefitSystem
from openfisca_morocco.reforms import ReformeBaremeIR, ReformeTVA

baseline = CountryTaxBenefitSystem()
old_scale = ReformeBaremeIR(baseline)  # pre-2025 IR scale
vat_18 = ReformeTVA(baseline)  # normal VAT rate at 18 % from 2025
```

Both are tested against the baseline in `tests/reforms/`.

### Run the tests

```sh
make test          # YAML tests under openfisca_morocco/tests/
pre-commit run --all-files
```

The YAML tests in `openfisca_morocco/tests/impot_revenu.yaml`,
`openfisca_morocco/tests/cotisations_sociales.yaml`,
`openfisca_morocco/tests/allocations_familiales.yaml`,
`openfisca_morocco/tests/aide_sociale_directe.yaml`,
`openfisca_morocco/tests/impot_revenu_categories.yaml`,
`openfisca_morocco/tests/ir_regimes_professionnels.yaml`,
`openfisca_morocco/tests/ir_deductions_globales.yaml`,
`openfisca_morocco/tests/ir_patrimoine.yaml`,
`openfisca_morocco/tests/enregistrement.yaml`,
`openfisca_morocco/tests/test_ir_categories_gating.py`,
`openfisca_morocco/tests/test_ir_parameter_tables.py`,
`openfisca_morocco/tests/test_ir_deductions_election.py` and
`openfisca_morocco/tests/tva.yaml` document the expected law at the boundaries
(each bracket, each ceiling, each dated rate, each transitional step).
`aide_sociale_directe` is completed by
`aide_rentree_scolaire.yaml`, `aide_speciale_enfants_places.yaml` and
`prime_exceptionnelle_asd.yaml` for the three related allowances, with
`test_prime_exceptionnelle_asd.py` running the twelve-month consumption
sequences. `openfisca_morocco/tests/age.yaml` covers the `age` formula.
`openfisca_morocco/tests/test_cotisations_sociales.py` checks CNSS and AMO
contributions across salary levels and validates integration into the annual IR,
`openfisca_morocco/tests/test_ir_periods.py` checks monthly salary aggregation,
varying pay, partial years, annual input compatibility and monthly CNSS ceilings,
`openfisca_morocco/tests/test_tva_taux.py` checks every declared TVA rate and
period against the verified corpus dataset,
`openfisca_morocco/tests/test_tva_simulation.py` checks the public simulation
path with a `Company`, and
`openfisca_morocco/tests/test_tva_article99.py`,
`openfisca_morocco/tests/test_tva_article101.py`, and
`openfisca_morocco/tests/test_tva_article15.py` check snapshot item lookups,
source-order preservation and quote provenance across all catalogs.
`test_tva_article99.py` additionally checks the effective-date contract: proven
rows carry a method, an instrument and a matching hash, bracketed rows carry no
date, a renumber is not a repeal, a rate move is not a repeal, and a date query
never reaches an undated row.

`openfisca_morocco/tests/situations/` mirrors the bundled examples for the IR,
CNSS and ASD families, and `openfisca_morocco/tests/reforms/` checks both
reforms against the baseline.

## Repository layout

```
openfisca_morocco/
├── entities.py                 # Household (adults/children), Company, Person
├── tva_article15.py            # pre-CGI Loi 30-85 Article 15 snapshots
├── tva_article99.py            # snapshot item listing, exact lookup and dated segments
├── tva_article91_92.py         # exemption snapshot listing and exact lookup
├── tva_article100.py           # specific-rate periods and tax calculation
├── tva_article101.py           # fixed 2006 LAR Article 101 snapshot
├── data/
│   ├── tva_article15_catalog.json # historical Article 15 catalog and audit
│   ├── tva_article91_92_catalog.json # quoted exemption snapshots
│   ├── tva_article100_rates.json # specific-rate periods and amendments
│   ├── tva_article99_catalog.json # quoted Article 99 snapshots, provenance and effective dates
│   └── tva_lar_2006_article101.json # separate LAR Article 101 snapshot
├── parameters/
│   ├── impot_revenu/           # barème, frais professionnels, charges de famille
│   ├── prestations_sociales/   # cotisations CNSS, AMO, allocations familiales, ASD
│   ├── enregistrement/         # registration and conservation duties
│   └── tva/                    # dated rates 2004-2026, transitional schedules
├── variables/
│   ├── aide_sociale_directe.py # ASD monthly household estimate
│   ├── aide_rentree_scolaire.py # ASD September school-return allowance
│   ├── aide_speciale_enfants_places.py # ASD special allowance for placed children
│   ├── prime_exceptionnelle_asd.py # ASD exceptional allowance after a CNSS declaration
│   ├── cotisations_sociales.py # CNSS and AMO contributions (employee & employer)
│   ├── enregistrement.py       # registration and conservation duties
│   ├── impot_revenu.py         # the IR pipeline
│   ├── tva.py                  # monthly company TVA declaration
│   └── demographics.py         # birth, age
├── reforms/
│   ├── reforme_bareme_ir.py    # pre-2025 IR scale
│   └── reforme_tva.py          # normal VAT rate at 18 %
├── situation_examples/         # ready-to-post Web API situations
│   ├── salarie.json
│   ├── salarie_exonere.json
│   ├── salarie_impose.json
│   ├── couple_avec_enfants.json
│   ├── haut_revenu.json
│   ├── cout_employeur.json
│   └── menage_asd.json
└── tests/                      # YAML and Python tests
    ├── situations/             # the example families
    └── reforms/                # reform deltas vs baseline
scripts/
├── build_article99_attribution.py     # Article 99 effective dates + sub-items
└── build_tva_article91_92_catalog.py  # verbatim Article 91/92 projection
```

## Roadmap

The path to a complete, usable package — IR on all income categories,
CNSS/AMO contributions, TVA, family allowances, direct social support,
realistic situation and reform examples, PyPI publication — is tracked in the
[v1.0 milestone](https://github.com/MasterSwords1/openfisca-morocco/milestone/1).
Each issue states its goal, scope, acceptance criteria and the issues it depends
on.

## Publishing a release

The first public release is postponed; see the
[release issue](https://github.com/MasterSwords1/openfisca-morocco/issues/12).
Resolve the release blockers with the maintainers before changing repository
visibility or publishing.

1. Review the full Git history for secrets and check the licence and template
   attribution before making the repository public.
2. Configure PyPI Trusted Publishing for this repository, the `cd.yaml`
   workflow, and the `pypi` GitHub environment.
3. Once the release commit is on public `main`, run **Continuous deployment**
   from the Actions tab on that branch. Verify that the PyPI release is
   available and the Git tag matching `pyproject.toml` points to the release
   commit.
4. In a new project outside any checkout, verify installation from PyPI.

   ```sh
   uv init --bare
   uv add openfisca-morocco   # pin the published version if needed
   scenarios="$(uv run python -c 'from pathlib import Path; import openfisca_morocco; print(Path(openfisca_morocco.__file__).parent / "tests")')"
   uv run openfisca test --country-package openfisca_morocco "$scenarios"
   ```

5. After publication, add the `openfisca` topic to the repository, enable the
   PyPI badge below, and submit Morocco (`MA`) to the
   [OpenFisca packages listing](https://openfisca.org/en/packages/).

<!-- Enable after the first PyPI release:
[![PyPI](https://img.shields.io/pypi/v/openfisca-morocco)](https://pypi.org/project/openfisca-morocco/)
-->

## Contributing

Read [CONTRIBUTING](CONTRIBUTING.md), open a pull request against `main`, and
follow the version and changelog rules described there.

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
