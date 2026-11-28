# Legislation Explorer reference links

Parameter `metadata.reference` links are public citations for the Legislation
Explorer. They must point to official public publishers only. The allowed hosts
are `www.sgg.gov.ma`, `www.anss.gov.ma`, `www.cnss.ma` and
`www.emploi.gov.ma`. Private research corpora, including `morocco-holy-graph`,
and corpus paths must never appear in parameter references.

When a reference list contains both an annual law/decree and a consolidated
Code Général des Impôts (CGI) or article text, place the annual law/decree
first, newest year first, and the consolidated CGI/article text after it. Other
SGG entries follow the annual law/decree entries, and non-SGG official agency
entries remain after the SGG entries. Lists with no SGG link keep the relevant
agency publisher first.

Put printed Bulletin Officiel page numbers (folios) in the citation title.
Use a `#page=N` fragment only when `N` is the actual 1-based page index in the
PDF. A printed folio is not necessarily the PDF page index. Do not invent
either number; omit a PDF fragment when the actual PDF page index is unknown.

Variable `reference` attributes follow the same no-corpus rule. They may cite
the competent public authority (SGG, DGI `tax.gov.ma`, ANSS, CNSS, emploi,
MALOI, ACAPS) when no gazette URL is encoded.

Current coverage: 159 SGG parameter references, one with a printed folio
(`p. 10239`); the other 158 cite the BO/PDF without a printed page. Adding the
remaining folios is a follow-up, not a claim of full page coverage.

Before deployment, check every reference URL and require an HTTP 200 response.
The reference tests enforce the host allowlist, block corpus links, check SGG
and annual law/decree ordering, and require any existing `#page=` fragment to
be a positive integer.
