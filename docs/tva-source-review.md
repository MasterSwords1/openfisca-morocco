# TVA source review

Reviewed 2026-11-13 for the company TVA model in issue #6.

## Parsed legal sources

### Ma Loi

Ma Loi publishes the current CGI article by article in French and Arabic. Its
Article 91, 92 and 99 pages identify the served edition as the 2026 CGI. The
2026 Article 91/92/99 wording was spot-checked against the package's 2026
consolidated snapshot. Ma Loi says its texts are reproduced from the Official
Bulletin and that the Arabic edition controls if versions diverge. It is a
useful current-text check, but these public pages do not provide the older
article editions needed to fill the package's historical gaps.

- [CGI Article 91](https://maloi.ma/fr/law/code-impots/article/91)
- [CGI Article 92](https://maloi.ma/fr/law/code-impots/article/92)
- [CGI Article 99](https://maloi.ma/fr/law/code-impots/article/99)
- [Ma Loi terms](https://maloi.ma/fr/legal/terms)

The terms allow ordinary consultation and professional use, but prohibit mass
data extraction. The review therefore used individual article pages only; it
did not crawl or copy the site in bulk.

### Legal IQ

Legal IQ advertises a fiscal corpus covering the CGI, finance laws, DGI notes
and CNRF decisions, with an article history and regime lookup by exercise. The
public product page describes those capabilities but does not provide the
underlying historical article records or a downloadable catalog. No account
was created and no account-only content was used.

- [Legal IQ fiscal research](https://www.legaliq.ma/produits/recherche-fiscale/)

An authorized export from Legal IQ could help fill item-level historical dates
and amendment attribution that are absent from the current snapshots.

### Corpus

Corpus documents that it reconstructs texts from official sources, including
the Official Bulletin, SGG, Adala and DGI, and segments them by disposition
with dates and amendment/repeal tracking. Its console requires an account for
access and an active subscription for full access. Its terms prohibit
systematic or automated extraction without prior written agreement. No
automated collection or bulk copying was performed.

- [Corpus source and extraction notes](https://corpus.ma/comment-ca-marche)
- [Corpus terms](https://corpus.ma/cgu)

## Data used by the package

The packaged Article 91/92/99 rows and Article 100 periods come from the
quote-backed catalog
`laws/ma_tax_law/data/consolidated/tva_article_lists.json`. That catalog keeps
the official consolidated source paths and SHA-256 hashes. The package now
exposes exact Article 91 and 92 snapshots for 2007, 2010, 2014, 2018, 2021,
2024 and 2026, plus the verified Article 100 rate periods from 2007 through
2019.

The Article 91/92 entries preserve numbered clauses, source context and
deduction treatment. They are itemized at two levels: the article-level context
and numbered clauses, and the nested bullets and letters printed beneath a
clause. The nested level is a genuine legal structure in the source, not an
extraction artefact: 603 rows carry `nesting_depth` 1–3 and an `item_role` of
`leaf` (565) or `container` (38). Article 91 has no nesting after the 2014
edition because the consolidated text prints none there — that is a property of
the source, not a missing extraction. Their edition dates are snapshot dates,
not continuous effective dates. Article 100 instead has continuous rate
intervals supported by the 2011 metal-rate amendment and the 2020 repeal. The
package does not reconstruct Article 100's predecessor regime before 2007 or
assign post-repeal transactions to a new category.

Article 99 rows differ: they carry a dated segment in `effective_attribution`,
derived per boundary from the seven consolidated editions and fifteen
finance-law transcriptions (see below). A row is dated only where a source names
the instrument, and an undated row refuses a date query.

### Enforced coupling to the corpus

Three package defects were found by verifying the packaged rows against the
corpus row each one names, and all three are now impossible by construction:

- two 2007 Article 92 clauses (`17°` *Fondation Cheikh Zaïd Ibn Soltan* and
  `31°` *Sala Al-Jadida*) had been merged into their neighbours and the
  remaining IDs renumbered, so 24 packaged IDs resolved to a different clause
  than the corpus row they claimed;
- 45 clauses the consolidated text prints `(abrogé)` were published as
  `in_force_in_snapshot`;
- 605 corpus rows were dropped (603 nested sub-items plus the two merged
  clauses), and six Article 99 clauses lost an `exclusion` qualifier that
  narrowed them.

`scripts/build_tva_article91_92_catalog.py` now copies each corpus row verbatim
and `scripts/build_article99_attribution.py` re-projects `conditions` from the
corpus, asserting quote and rate identity at the same time. Both support
`--check`, and tests re-derive the projection on every run rather than trusting
the artifact.

### Article 99 effective dates

`scripts/build_article99_attribution.py` regenerates
`openfisca_morocco/data/tva_article99_catalog.json` (schema version 2) and
`--check` fails when the artifact is stale. It uses three mechanical routes and
no hand-written rule table:

1. the seven anchor editions give the baseline (Loi 43-06 art. 5, 2007-01-01);
2. a later boundary is dated from the row's own consolidated endnote when
   exactly one instrument inside the interval is named;
3. an *introduction* may be dated from a verbatim reproduction in exactly one
   in-interval finance-law transcription.

Measured: 299 of 420 rows proven (71,2 %), 121 bracketed
(`repeal_not_witnessed` 109, `ambiguous_instruments` 7,
`introduction_not_witnessed` 6). Hand-asserted repeals were deliberately not
added: a repeal leaves no trace on any later edition, so guessing one from the
abolition of a rate class would have dated 109 boundaries no source supports.

Two provenance defects were found while verifying the hashes and are not
patched silently on the corpus side:

- the packaged 2007 `source_pdf` named an SGG index volume
  (`BO_5487_2007_SGG_index.pdf`) that contains no Article 99. The hash was
  correct for the wrong file. It is now `BO_5487-bis_fr.pdf` (4 453 162 B,
  `3e08e24d…`).
- the corpus records `source_sha256` values that are hashes of a *transcription*
  under a field that reads like a PDF hash (see
  `docs/work-packages/tva-article99-attribution.md` §3.3). The package keeps
  `pdf_sha256` and `text_sha256` separate for exactly this reason.

The current Article 91/92/99 pages on Ma Loi were used only as a spot check.
The package's numeric and historical claims remain tied to the pinned source
catalog and official CGI/finance-law references, not to a third-party page
without a source hash.

## 2006 primary-source corroboration

The 2006 snapshot was previously backed by a DGI consolidated edition (the
`Livre d'Assiette et de Recouvrement 2006`, which has a text layer) served from
a dead `finances.gov.ma` path and a third-party mirror. It now also cites the
enacting text.

- Bulletin officiel n° 5382 bis, 27 kaada 1426 (29-12-2005), promulgating
  loi de finances n° 35-05 pour l'année budgétaire 2006 (dahir n° 1-05-197).
- <https://www.sgg.gov.ma/BO/bo_fr/2005/BO_5382-bis_fr.pdf>
- Fetched 2026-11-14: HTTP 200, 16 561 566 bytes, SHA-256
  `2a5465d2…f615` — byte-identical to the corpus copy
  `laws/ma_fin_law/documents/BO_5382-bis_fr.pdf`.

The BO PDF is a scan with no text layer, so the rate pages (printed folios
1018–1019, PDF pages 46–47) were rendered at 300 dpi and OCR'd with
tesseract 5.5.3 (`fra`, `--psm 3`). The OCR text is kept as review evidence in
`docs/evidence/bo-5382-bis-2006-tva-rates.ocr.txt`.

Two results matter:

1. The BO text of Article 101 matches the packaged 38 `historical_2006_article101`
   rows item for item (37 rows at ≥95 % token coverage against the OCR, one row
   differing only by `rebia`/`rabii`). The 14/16/8 split across 7 %/10 %/14 % is
   confirmed.
2. The 2006 text numbers the TVA rate articles differently from the 2007+
   editions. In 2006: Article 99 = base by prior agreement, Article 100 = 20 %
   normal rate, **Article 101 = reduced rates**, Article 102 = specific rates.
   In 2007 and later the same four articles are 97, 98, 99, 100.

The second point is a live naming hazard: a 2006 "Article 100" is the normal
rate, not the specific-rate article exposed by `tva_article100`, and a 2006
"Article 101" is not a CGI Article 99 edition. Both facts are carried in the
packaged snapshot as `corroborating_source.article_numbering_note`.

The 2006 specific rates (100 MAD/hl wine and alcohol, 4 MAD/g gold and
platinum, 0,05 MAD/g silver) are therefore known, but are deliberately not
packaged as Article 100 rate periods; see the `gaps` entry in
`openfisca_morocco/data/tva_article100_rates.json`.

## Remaining source work

The company calculation accepts explicit rate-category inputs and exposes
source-backed exemption and rate catalogs; it does not infer a legal category
from free-form product descriptions. The gaps between consolidated editions
remain: the seven snapshots are anchors, not a continuous history, and
`tva_article_lists.json` still declares `schema_version` 1 while 1 763 of its
1 768 rows carry `valid_from == valid_to`. The Article 91/92 nested-list gap is
resolved for the seven editions the corpus covers — the package now projects
every corpus row — but the corpus's own
`article-91-92-subclauses-not-leaf-itemized` and
`nested-list-items-not-fully-normalized` entries have not been withdrawn, so the
upstream register and the packaged result disagree. To close the remaining gaps,
use an authorized article-history export from Legal IQ or Corpus, or reconstruct
the missing editions from official annual CGI publications and each controlling
finance-law amendment. Preserve the amendment text and effective date for each
change rather than extending a snapshot across intervening years.
