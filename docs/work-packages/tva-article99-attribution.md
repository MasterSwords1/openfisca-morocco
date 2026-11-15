# Work package: Article 99 effective dates and row-level attribution

Covers issue #6 acceptance boxes 4 and 5:

- [ ] Each Article 99 clause has its own effective date, so the lists can be
      used as a date-range classifier.
- [ ] Amendment attribution is complete at row level.

Status: method settled; intervals 2007 → 2010 and 2018 → 2021 analysed.
Source route: consolidated CGI editions (endnotes) + SGG Bulletin officiel
(diff text). Not `corpus.ma`, not `finances.gov.ma`.

Last checked against the corpus at `bbe45e1` → `bae3551` on 2026-11-15.

## 1. Why this is not a Holy Graph task

`morocco-holy-graph#80` carries the same gaps, but the work does not require it:

- the package has no runtime or build dependency on the corpus — the five
  catalogs load through `importlib.resources` from `openfisca_morocco/data/`;
- the seven consolidated CGI editions (2007, 2010, 2014, 2018, 2021, 2024, 2026)
  are already pinned locally with sha256, so no consolidated text needs to be
  re-acquired;
- what boxes 4 and 5 need is the **amending finance laws**, which SGG serves
  today and which verify byte-identical to the local copies.

`corpus.ma` is excluded. Its CGU (v. 26 October 2026) §5 forbids systematic or
automated extraction of the Service's answers and citations without prior
written agreement, and §1 states that its answers are AI-generated and must be
verified by the user. It is a research assistant, not a text repository, so it
is not an admissible provenance terminus for quoted legal text.

## 2. Evidence standard

Two statuses, `proven` and `bracketed`, and three proof methods. A row is
`proven` only when at least one method applies; otherwise it is `bracketed`.

| Method | Label | Proof required |
|---|---|---|
| M1 | `verbatim_reproduction` | The amending article reproduces the item text (allowing for the BO's ellipsis conventions) inside the paragraph for the stated rate. |
| M2 | `positional_abrogation` | The amending article prints an `(abrogé)` marker, and the items immediately before and after it in the amending text correspond, in the same order, to items that flank exactly **one** item in the amended snapshot. |
| M3 | `consolidated_endnote` | The consolidated edition published after the interval carries an endnote on that exact slot naming the amending law and article. |

M3 is the strongest and the cheapest, and it was the one I was not using. See
§2.2.

`bracketed` means neither applies. Record the bracket only — `valid_from` ≥
previous anchor, `valid_to` ≤ next anchor — and **never** promote it to a date.

### 2.1 Why "list completeness" is not a valid method

The obvious inference — *the amending law reproduces the paragraph in full, the
item is absent, therefore it was repealed* — does not hold. Both the 2009 and
2010 Article 99 fragments are elided **inside** the list, not only at its end:

- Loi 40-08 art. 7, 2°: `«— les opérations de vente de denrées ou de boissons.`
  (terminal period mid-list) and `«— les opérations effectuées. n: . à l'article
  89-1-12°-a) et c) ci-dessus ;`;
- Loi 48-09 art. 7, 1°: `«— l'eau livrée aux réseaux .` and
  `«— les produits pharmaceutiques...`.

An item missing from such a list may simply have been elided.

### 2.2 M3 is not the rejected method in disguise

Absence proves nothing. An **endnoted** absence does. When the consolidated
edition prints `- (abrogé)116 ;` in the middle of a list and footnotes it
`Article 8 de la loi de finances n° 38-07 pour l'année budgétaire 2008`, that is
a positive assertion by the tax administration, tied to a slot, tied to an
instrument — not an inference from silence. The difference is that M3 requires
the editor to have left a stub.

This matters because the CGI leaves such stubs **inconsistently**: Article 99
of the 2010 edition has six of them, but the three credit-sector items that
vanish in the same interval have none at all (§4.4). M3 is therefore a real but
partial witness, and its silences are not evidence.

## 3. Source register (verified 2026-11-14)

### 3.1 Amending laws

| Instrument | Budget year | Law article amending Art. 99 | BO | SGG URL | Local pin |
|---|---|---|---|---|---|
| Loi n° 38-07 | 2008 | art. 8 | 5591 bis, 31-12-2007 | `sgg.gov.ma/BO/bo_fr/2007/BO_5591-bis_fr.pdf` | **byte-identical**, 2 037 991 B, sha256 `1dfddf30…` |
| Loi n° 40-08 | 2009 | art. 7 | 5695 bis, 31-12-2008 | `sgg.gov.ma/BO/bo_fr/2008/BO_5695-bis_fr.pdf` | **byte-identical**, 12 920 996 B, sha256 `c0cd9fd3…` |
| Loi n° 48-09 | 2010 | art. 7 | 5800 bis, 31-12-2009 | `sgg.gov.ma/BO/bo_fr/2009/BO_5800-bis_fr.pdf` | local copy is the **Adala** scan (449 685 B); SGG scan is a different file, 3 450 060 B, sha256 `2493e36f…` |
| Loi n° 80-18 | 2019 | **none** — art. 7 amends Arts. 91 and 92 | 6736 bis, 21-12-2018 | `sgg.gov.ma/BO/bo_fr/2018/BO_6736-bis_fr.pdf` (200, 6 782 903 B, sha256 `4790a0d5…`, image-only) | transcription `FL_2019_80-18.txt` |
| Loi n° 70-19 | 2020 | art. 6 | 6838 bis, 14-12-2019 | `sgg.gov.ma/BO/bo_fr/2019/BO_6838-bis_fr.pdf` (200, 1 313 268 B, sha256 `4995be8c…`, 106 pp) | Adala scan, sha256 `622d2396…`; fragment identical |
| Loi n° 65-20 | 2021 | art. 6 | 6944 bis, 18-12-2020 | `sgg.gov.ma/BO/bo_fr/2020/BO_6944-bis_fr.pdf` (200, 1 581 901 B, sha256 `e545bd22…`, 110 pp) | Adala scan, sha256 `85ec22c8…`; fragment identical |

Article-number verification. Each law's own article boundaries were located:
`FL_2008_38-07.txt` art. 8 spans lines 324–2442 (Article 99 fragment at 1201);
`FL_2009_40-08.txt` art. 7 spans 334–2466 (fragment at 755);
`FL_2010_48-09.txt` art. 7 spans 560–2229 (fragment at 1079);
`FL_2019_80-18.txt` art. 7 spans 698–3182 and contains **no** Article 99
fragment (it prints `Article 99 sexies`, an unrelated income-tax provision);
`FL_2020_70-19.txt` art. 6 spans 511–2325 (fragment at 1167);
`FL_2021_65-20.txt` art. 6 spans 1426–2749 (fragment at 1767).

Consequence: the corpus's candidate list for 2018 → 2021 is
`[['80-18', 7], ['70-19', 6], ['65-20', 6]]`, but only **two** of the three
touch Article 99. `80-18` art. 7 belongs to the Articles 91/92 interval — it
adds `6° les pompes à eau qui fonctionnent à l'énergie solaire…` to Article 91
(`FL_2019_80-18.txt` line 1229) and rewrites Article 92.

**Open item:** the 2010 pin must be re-established against the SGG scan, or the
Adala scan documented as the pin with its own hash. Byte-identity is proved for
2008 and 2009 only.

Effective dates. All six laws are published in December of the preceding year
for the following budget year, none carries a provision delaying its TVA
changes, and each opens with Article premier ("*continueront d'être opérées,
pendant l'année budgétaire N…*"). Effective date = 1 January of the budget
year, the convention already used in `tva_article100_rates.json`.

### 3.2 Snapshot editions used as witnesses

| Edition | File | Date on page | Role |
|---|---|---|---|
| CGI 2007 | `CGI-2007-FR.pdf.txt` | BO 5487 bis, 01-01-2007 | baseline list order |
| CGI 2010 | `CGI-2010-FR.pdf.txt` | `Le 01-02-2010` | M3 witness for 2008–2010 |
| CGI 2018 | `CGI-2018-FR.pdf.txt` | — | baseline list order |
| CGI 2021 | `CGI-2021-FR.pdf.txt` | — | M3 witness for 2019–2021 |

The 2010 edition exists in two extractions, `CGI-2010-FR.pdf.txt` (1 140 643 B)
and `CGI-2010-FR-CCIS-RSK.pdf.txt` (1 141 904 B). They agree on every string
this work package relies on; both were checked for §4.4.

Text extraction. BO 5591 bis and BO 5695 bis carry a text layer in a shifted
font encoding (each codepoint offset by +29, so `4XDWUH` is `Quatre`); it
decodes mechanically and losslessly for ASCII. The 2010 SGG scan has no text
layer and needs OCR (`fra.traineddata`, 300 dpi) — the route already used for
BO 5382 bis. The 2020 and 2021 BOs are held as Adala scans with working text
layers.

### 3.3 Provenance defect in the corpus

`tva_article_lists.json` records, in `changes[*].item_citation_audit[*]
.direct_amendment_citations`, a `source_sha256` of
`7f971e6830cd856f86efe8aaf64cd0f8abc0b181359e17d44791e63dbcd156dd` for
Loi 70-19 art. 6. That hash is of **`FL_2020_70-19.txt`, the transcription** —
not of the BO PDF (`622d2396…`) and not of the Adala scan's text layer. The
field name suggests otherwise. Raise with Codex; do not silently patch.

## 4. Interval 1: 2007-01-01 → 2010-01-01

The corpus's `changes[2007→2010]`: 46 unchanged, 2 modified, 6 added,
14 removed. The 14 removals are 8 standalone rows plus two container groups
(`14pct-007` electricity/solar, `7pct-008` animal feed) carrying 2 leaves each.

Baseline order, CGI 2007 Article 99-2° (verified from the 2007 text): denrées
hôtels, denrées restaurants, restauration du personnel, location d'immeubles,
huiles fluides, sel, riz, pâtes, banque, valeurs mobilières, **crédit foncier**,
OPCVM, **crédit agricole**, **Fonds d'équipement communal**, **crédit-bail**,
professions libérales.

### 4.1 Dated

| Item | Change | Effective | Instrument | Method |
|---|---|---|---|---|
| `2010-art99-7pct-006` | added at 7 % | 2009-01-01 | Loi 40-08 art. 7, 1° | M1 — *aliments destinés à l'alimentation de bétail et des animaux de basse-cour à l'exclusion des autres aliments simples…* reproduced |
| `2010-art99-10pct-009` | added at 10 % | 2009-01-01 | Loi 40-08 art. 7, 2° | M1 — *les tourteaux servant à la fabrication des aliments…*; CGI 2010 endnote **111** = Loi 40-08 |
| `2010-art99-10pct-016` | added at 10 % | 2009-01-01 | Loi 40-08 art. 7, 2° | M1 — motorway toll inside the 10 % paragraph; CGI 2010 endnote **115** = Loi 40-08 |
| `2007-art99-7pct-014` | 7 → 10 % | 2009-01-01 | Loi 40-08 art. 7, 2° | M1 — same item as `10pct-016`; **not a repeal** |
| `2007-art99-7pct-008` + 2 leaves | split | 2009-01-01 | Loi 40-08 art. 7, 1° and 2° | M1 — feed stays 7 %, *tourteaux* move to 10 % |
| `2010-art99-10pct-010` | 7 → 10 % | 2010-01-01 | Loi 48-09 art. 7, 2° | M1 — *gaz de pétrole et autres hydrocarbures gazeux*; CGI 2010 endnote **112** = Loi 48-09 |
| `2010-art99-10pct-011` | 7 → 10 % | 2010-01-01 | Loi 48-09 art. 7, 2° | M1 — *huiles de pétrole ou de schistes*; CGI 2010 endnote **113** = Loi 48-09 |
| `2010-art99-10pct-012` | text expanded at 10 % | 2010-01-01 | Loi 48-09 art. 7, 2° | M1 — regains *sous réserve de l'exonération prévue à l'article 91-III-2°*; CGI 2010 endnote **114** = Loi 48-09 |
| `2007-art99-14pct-004` | **repealed** | 2008-01-01 | Loi 38-07 art. 8 | **M3 + M2** — CGI 2010 prints `- (abrogé)116 ;` between *le thé* and *transport de voyageurs*, endnote 116 = Loi 38-07; the BO prints `(abrogé)` in exactly that slot |
| `2007-art99-10pct-015` | **repealed** | 2008-01-01 | Loi 38-07 art. 8 | **M2** — BO 5591 bis p. 11 prints `(abrogé)` between *les opérations afférentes aux … audit fonds* and *les opérations effectuées dans le cadre de leur profession*; only *crédit-bail* sits between them in the 2007 order |

Four of these change the tax outcome rather than the wording:

- treating `7pct-014` as a repeal would tax motorway tolls at 7 % through 2009;
- treating the gaz/huiles rows as unchanged would tax them at 7 % from 2010;
- treating `7pct-008` as a repeal would lose feed and misplace *tourteaux*;
- treating `14pct-004` as a repealed-and-reintroduced row would misdate
  *travaux immobiliers*, which left the 14 % list on 2008-01-01.

### 4.2 No legal change (ID churn only)

| Before | After | Why |
|---|---|---|
| `2007-art99-14pct-007` + 2 leaves | `2010-art99-14pct-006` | identical text (*l'énergie électrique et les chauffe-eau(x) solaires*), 14 % in both snapshots; both intervening laws elide 3° as "la suite sans modification"; CGI 2010 carries no endnote on the slot |
| `2007-art99-10pct-012` | `2010-art99-10pct-014` | same OPCVM item; text differs only in the statute-reference style (`1-93-213` vs `1.93.213`); CGI 2010 carries **no endnote** on it, so no finance law touched it — this is a DGI typographic reset, not an amendment |

The catalog must separate *repealed* from *renumbered*, or a date-range
classifier will report phantom exemptions.

### 4.3 Undated

| Item | Bracket | Why undated |
|---|---|---|
| `2007-art99-10pct-011` (crédit foncier) | 2008-01-01 … 2010-01-01 | gone by CGI 2010; LF 2008 elides 002–013 without a marker; LF 2009 elides 010–015 without a marker; LF 2010 prints 010, 012, 016 consecutively with no marker |
| `2007-art99-10pct-013` (crédit agricole) | as above | as above |
| `2007-art99-10pct-014` (Fonds d'équipement communal) | as above | printed **as retained** in the LF 2008 fragment (`les opérations afférentes aux … audit fonds ;`), so LF 2008 did not repeal it; yet absent by 2010 |

### 4.4 The anomaly worth recording

CGI 2010 leaves four `(abrogé)` stubs in Article 99 — 108, 109, 110 in the 7 %
list and 116 in the 14 % list — each with an endnote naming a finance law. The
10 % list carries none. The three
credit-sector items vanish from the same article **without a stub and without an
endnote**, even though they were present in CGI 2007 in the same list.

That is either (a) an editorial omission by the DGI when the sentences were
deleted, or (b) evidence that the deletion was not made by a finance law at all.
The corpus's own `changes` diff already finds them removed. This work package
records the bracket and does not choose between (a) and (b).

Four of the five original grade-C rows were credit-sector items vanishing
together, which made a single Loi 38-07 repeal plausible. M2 has now confirmed
one of them (`crédit-bail`) — which makes the block-repeal reading *less*
likely, not more, because the BO printed a marker for one item and not for its
neighbours.

**Decisive acquisition:** CGI 2008 and CGI 2009. Their endnotes would settle
all three remaining rows. Neither the corpus nor SGG holds them; they are DGI
publications, so this needs a mirror search or a written request.

## 5. Interval 2: 2018-01-01 → 2021-01-01

Nine changes, all nine now dated. Zero `bracketed`.

### 5.1 Added — 2020-01-01, Loi 70-19 art. 6

| Item | Method | Text |
|---|---|---|
| `2021-art99-10pct-005` | M1 | *les huiles fluides alimentaires à l'exclusion de l'huile de palme* — reproduced verbatim |
| `2021-art99-10pct-004` | M1 | *les opérations de vente des billets d'entrée aux musées, cinéma et théâtre* — reproduced verbatim |
| `2021-art99-10pct-014` | M1 | *«Mourabaha», «Salam» et «Istisna'a»* — reproduced verbatim |
| `2021-art99-10pct-001` | M1 (delta) | the item is elided as `les opérations ....... restauration`, but the distinguishing clause *ainsi que les prestations fournies par les exploitants de cafés* is reproduced verbatim; CGI 2021 endnote 537 = Loi 70-19 |

### 5.2 Repealed

| Item | Effective | Instrument | Method |
|---|---|---|---|
| `2018-art99-10pct-045` (*tarières*) | 2020-01-01 | Loi 70-19 art. 6 | **M2** — BO 6838 bis p. 2410 prints `– les abreuvoirs automatiques ;` `– (abrogé)` `– les polymères…`; CGI 2018 has exactly one item between those two, and LF 2019 does not touch Article 99 |
| `2018-art99-10pct-008` (*chauffe-eaux solaires*) | 2021-01-01 | Loi 65-20 art. 6 | **M1 + M2 + M3** — the LF 2021 fragment prints `– les pâtes alimentaires ;` `– (abrogé)` `– les aliments destinés…`; CGI 2021 prints `(abrogé)542` at that slot and endnote 542 = Loi 65-20 |

The solar-water-heater repeal has an **independent third witness**: Loi 65-20
art. 6 simultaneously added `8° – les chauffe-eaux solaires` to Article 91
(exonérations sans droit à déduction), and CGI 2021 endnotes **444** on that new
item also names Loi 65-20 art. 6. The taxpayer outcome is a move from 10 %
taxation to full exemption, not a disappearance from the list.

This matters for the classifier: an Article 99-only view reports
*solar water heaters ceased to be a reduced-rate product*; the article-91 view
reports *solar water heaters became exempt*. Those are different facts, and the
second is the correct one. Box 4 must not be built as an Article 99-only
timeline.

### 5.3 Reworded, not repealed — 2020-01-01

| Before | After | Delta |
|---|---|---|
| `2018-art99-10pct-001` | `2021-art99-10pct-001` | + *ainsi que les prestations fournies par les exploitants de cafés* |
| `2018-art99-10pct-004` | `2021-art99-10pct-005` | + *à l'exclusion de l'huile de palme* |
| `2018-art99-10pct-014` | `2021-art99-10pct-014` | + *«Salam» et «Istisna'a»* |

All three are Loi 70-19 art. 6. Recording them as repeal + creation would make a
date-range classifier report three products leaving the 10 % band in 2021 when
they never left it.

### 5.4 What this interval proves about the method

The 2007 → 2010 interval produced 3 undated rows out of 11 and led me to expect
`bracketed` to dominate. This interval produced **none**. The difference is not
the luck of the interval: it is that M2 and M3 were applied. Positional
abrogation is available whenever the BO prints a marker between two items that
still exist, and the consolidated endnote is available whenever the editor left
a stub. Those two methods, not verbatim reproduction, carry most of the load.

### 5.5 Corpus corroboration (checked 2026-11-15)

`morocco-holy-graph` advanced from `bbe45e1` to `bae3551`. Commit `095319b`
("add Article 91 and 92 consecutive change attribution and retire gap") added
`article91_changes` / `article92_changes` to every interval and retired the
`article91-92-change-attribution-not-audited` gap.

That dataset independently reproduces this section's central finding: for
2018 → 2021 it records `2021-art91-clause-015` (`8°- les chauffe-eaux
solaires444.`, rate `exempt`) as **added**, with
`direct_primary_text_match` against Loi 65-20 art. 6 and endnote 444 — the same
endnote and the same instrument this work package derived independently from
the SGG scan. §5.2 is therefore not a lone reading.

Two limits remain, and both are reasons this work package still exists:

- **The two halves are not linked.** The corpus knows the Article 99 removal and
  the Article 91 addition, but nothing in `changes` says they are the same
  product moving between articles. `test_article91_handoff` (§7) is still the
  missing assertion.
- **The dates are still zero-length.** `2021-art91-clause-015` carries
  `valid_from == valid_to == "2021-01-01"`, and all 554 Article 99 rows have
  `valid_from == valid_to`. The `snapshot-dates-are-not-continuous-validity`
  gap is open, so these rows cannot be imported as intervals. The effective
  date has to come from `effective_attribution` (§6), not from these fields.

## 6. Deliverable contract

Add one field per Article 99 row and tighten the existing rejection guard:

```json
"effective_attribution": {
  "status": "proven | bracketed",
  "method": "verbatim_reproduction | positional_abrogation | consolidated_endnote | null",
  "valid_from": "2020-01-01",
  "valid_to": "2020-12-31",
  "instrument": {
    "law": "Loi n° 70-19",
    "law_article": 6,
    "budget_year": 2020,
    "bo": "6838 bis",
    "bo_date": "2019-12-14",
    "url": null,
    "pdf_sha256": "622d2396c001e20cf0289e81ef43901edb6f3b11ef53b5a91c45af6c031064d2",
    "quote": "verbatim fragment from the amending article"
  },
  "corroboration": {
    "edition": "CGI 2021",
    "endnote": 542,
    "file_sha256": "…"
  }
}
```

`corroboration` is optional and is present when a second witness exists.

Guard change in `tva_article99.py`: replace

```python
if {"valid_from", "valid_to"} & _row.keys():
    raise ValueError("Snapshot markers must not be exposed as validity periods")
```

with a rejection of any validity field **unless** `effective_attribution.status
== "proven"`, `method` is set, and `instrument.pdf_sha256` is 64 hex characters.
A `bracketed` row must carry no date at all — its bracket belongs in a separate
`validity_bracket` field, not in `valid_from` / `valid_to`.

## 7. Acceptance tests

1. `test_proven_rows_have_hash_and_method` — every row with `valid_from` carries
   a 64-hex `pdf_sha256`, a `method`, and a non-empty quote.
2. `test_bracketed_rows_carry_no_dates` — `status != "proven"` implies neither
   `valid_from` nor `valid_to`.
3. `test_article99_intervals_are_contiguous` — for each rate and product key the
   proven intervals tile without gaps or overlaps across 2007 → 2026.
4. `test_renumber_is_not_a_repeal` — a removed row and an added row with the
   same rate and equivalent quote are classified renumber, and neither is dated.
   Regression cases: `14pct-007 → 14pct-006`, `10pct-012 → 10pct-014`.
5. `test_repeal_is_not_a_rate_move` — regression case `7pct-014 → 10pct-016`
   (motorway tolls, 2009) must be a rate move, not a repeal.
6. `test_article91_handoff` — a row repealed from Article 99 in the same
   instrument that adds it to Article 91 is flagged `exempted`, not `removed`.
   Regression case: solar water heaters, 2021.
7. `test_aggregation_still_rejects_undated_rows` — `aggregate_article_99_turnover`
   refuses a `bracketed` row when asked for a specific month.

## 8. Remaining intervals

Same method, ordered by payload:

| Interval | Instruments touching Art. 99 | Change volume | Note |
|---|---|---|---|
| 2024 → 2026 | 1 | 7 added, 7 removed | start here; also touches Art. 100 rate structure |
| 2014 → 2018 | 3 | 11 added, 14 removed | |
| 2010 → 2014 | 2 | 40 added, 11 removed | the 14 % solar/electricity split lands here |
| 2021 → 2024 | 3 | **44 added, 25 removed** | LF 55-23 rewrite |

2021 → 2024 matters most but goes last: LF 55-23 restructures the article
instead of editing it, so M1 and M2 do not apply and it needs M3 alone plus its
own approach.

For each interval, run M3 first — read Article 99 of the consolidated edition at
the *end* of the interval and collect every endnote. That is a single file read
and it names the instrument for most changed rows. Only then go to the BO diff
for the rows M3 left bare.

## 9. Risks

- **BO elision.** Still the dominant risk for M1 and M2. M3 mitigates it.
- **M3 silence.** The DGI does not always stub an abrogation (§4.4). Absence of
  a stub is not evidence of absence of a repeal.
- **Article 99 is not the whole story.** The 2021 solar-water-heater case shows a
  repeal in Article 99 paired with an addition in Article 91. Any classifier
  built on Article 99 alone will misreport the outcome.
- **Scan quality.** 2010 needs OCR; 2008 and 2009 need the +29 decode.
- **Drift.** If this lands only in the package, the corpus's `amendment_intervals`
  and the package catalogs will disagree. Each completed interval should be
  offered back to the corpus as a dataset patch.
- **Over-claiming.** The single largest hazard is a plausible date becoming a
  shipped one. The guard in §6 exists to make that a test failure rather than a
  silent tax error.
