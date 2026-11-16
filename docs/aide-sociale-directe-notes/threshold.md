# Décret n° 2-23-1068, article 1 — ASD eligibility threshold (RSU score)

**Scope note on evidence status.** Three tiers are used below and are labelled explicitly:
- **VERIFIED (primary, read directly)** — seen in the scanned image of the *Bulletin Officiel* page as published by ANSS, or in a full-text official PDF I retrieved.
- **VERIFIED (secondary/official-site)** — official agency or government website statement, read in full text, but not the decree itself.
- **NOT VERIFIED / INACCESSIBLE** — could not be read at source.

**Key metadata established (all VERIFIED against the scanned BO page unless noted):**
- Decree: **Décret n° 2.23.1068** (Arabic: مرسوم رقم 2.23.1068), signed Rabat, **17 Jumada I 1445 (1 December 2023)**.
- Title: *"بتحديد عتبة الاستفادة من نظام الدعم الاجتماعي المباشر"* — "fixing the threshold for benefiting from the direct social assistance regime".
- Published in **Bulletin Officiel n° 7253, 20 Jumada I 1445 (4 December 2023), page 10239** (header on the page reads: `عدد 7253 - 20 جمادى الأولى 1445 (4 ديسمبر 2023)`; folio `10239`).
- Deliberated in the Council of Government of **16 Jumada I 1445 (30 November 2023)**; signed by Head of Government Aziz Akhannouch, countersigned by Fouzi Lekjaa (Minister Delegate for the Budget).
- Text has **two articles only**; article 2 is the standard execution clause. The decree is therefore a single-value instrument.

---

## Q1. What exact value does article 1 of Décret 2-23-1068 set as the RSU score ceiling, and is 9.743001 exact?

### Takeaway
Article 1 sets the threshold at **9,743001** — written with a comma decimal separator and six decimal places. Converted to English notation this is **9.743001**, so the value used by the model is an **exact, unrounded transcription** of the official text. No rounding, no trailing-zero truncation, and no discrepancy of any kind was found.

### Cited Findings
- **Full text of article 1 as it appears in the BO (Arabic), read directly from the scanned page image:**
  > المادة الأولى
  > تحدد في 9,743001 عتبة الاستفادة من نظام الدعم الاجتماعي المباشر المنصوص عليها في البند 5 من المادة 3 من القانون المشار إليه أعلاه رقم 58.23.
  
  Literal translation: *"Article 1 — The threshold for benefiting from the direct social assistance regime, provided for in item 5 of article 3 of Law No. 58.23 referred to above, is set at 9,743001."* — [ANSS, scanned BO 7253 PDF, p. 10239](https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1068_AR.pdf)
- **The BO page header confirms the publication data:** `عدد 7253 - 20 جمادى الأولى 1445 (4 ديسمبر 2023)`, folio `10239` — same PDF as above.
- **Article 2 (full text):** `المادة الثانية — يسند تنفيذ هذا المرسوم الذي ينشر بالجريدة الرسمية إلى الوزير المنتدب لدى وزيرة الاقتصاد والمالية المكلف بالميزانية.` (execution delegated to the Minister Delegate for the Budget; publication in the Official Bulletin). — same PDF.
- **Preamble legal basis (full text):** the decree is based on Law 58.23 (dahir 1.23.87 of 16 Jumada I 1445 / 30 November 2023), *"ولا سيما المادة 3 منه"* ("in particular article 3 thereof"). — same PDF.
- **Signature block:** `وحرر بالرباط في 17 من جمادى الأولى 1445 (فاتح ديسمبر 2023)` — signed 1 December 2023. — same PDF.
- **Independent confirmation of the same figure, from the government's own communiqué of the Council of Government:** *"ويحدد مشروع هذا المرسوم عتبة نظام الدعم الاجتماعي المباشر في 9,743001"* — [Chef du Gouvernement, communiqué of 30 November 2023](https://www.cg.gov.ma/ar/node/11560)
- **Contemporary press confirmation (French), same value:** *"Le deuxième décret (décret 2.23.1068) fixe pour sa part le seuil d'éligibilité au régime des aides sociales directes à 9,743001, ce qui permet de couvrir environ 60% de la population…"* — [Médias24, 30 November 2023](https://medias24.com/2023/11/30/linscription-sur-la-plateforme-des-aides-sociales-directes-demarre-le-2-decembre)
- **Official ANSS slide deck (Nov 2024) states the same figure twice**, once as *"Satisfaire le score d'éligibilité : 9,743001"* and once as *"L'indice socio-économique du ménage, calculé au niveau du RSU doit être inférieur au seuil d'éligibilité du régime des ASD: 9,743001"* — [UNESCWA-hosted ANSS presentation, "Etat d'avancement du Régime de l'Aide Sociale Directe", 5 Nov 2024, PDF](https://www.unescwa.org/sites/default/files/event/materials/Status%20of%20the%20Direct%20Social%20Assistance%20Scheme%20in%20Morocco_FR.pdf)
- **Still the operative figure in 2026:** Minister Fouzi Lekjaa, written answer published 3 January 2026, lists among ASD conditions *"استيفاء شرط عتبة البرنامج المحددة في 9,743001"* — [Madar21, 3 January 2026](https://madar21.com/396719.html)
- **And as of November 2025:** *"un seuil d'éligibilité fixé à 9,743001 points"* — [Le360, 9 December 2025](https://fr.le360.ma/economie/aides-sociales-directes-124-millions-de-beneficiaires-a-fin-novembre_LIUD3NOSCFGEJOBHYALGC7J534)

### Inferences
- The comma in `9,743001` is a **decimal separator** (Moroccan/French typographic convention, also used for the dirham amounts in the same BO issue, e.g. `9,92` / `9,69`), not a thousands separator. The value is therefore 9 + 743001/1 000 000, i.e. **9.743001** — not 9,743,001 and not 9743.001.
- `9.743001` is the **shortest exact** representation: the source gives six decimal places and the final digits are `001`, so no alternative rounding (e.g. `9.7430`, `9.74`) is faithful to the text.
- Because the decree has only two articles and article 1 fixes a single number, there is no internal sub-threshold, no urban/rural split, and no age-dependent variant inside this decree.

### Gaps
- **The official French-language version of the decree was not retrieved.** SGG URLs tried (`sgg.gov.ma/BO/FR/2023/BO_7253_Fr.pdf` and three variants) all returned HTTP 404. The French wording "seuil d'éligibilité au Régime des Aides Sociales Directes" is ANSS's own French title for the decree ([ANSS FR list](https://anss.gov.ma/fr/lois-decrets)), **not** a verified quote of a French BO page. Any French quotation of article 1 in downstream writing must therefore be presented as a translation of the Arabic, not as the official French text.
- The ANSS-hosted PDF is a **pure scanned image** (2 pages, 1-bit JPEG at 300 dpi, `pdftotext` returns 2 bytes). There is **no text layer**; the article wording above comes from reading the page image, not from machine-extracted text. Machine OCR was not possible locally (no Arabic `tessdata` pack installed — only `afr` and `osd`).

---

## Q2. Does any later decree or law change the threshold?

### Takeaway
**No amendment to Décret 2.23.1068 was found.** The threshold appears unamended and still operative through late 2026. The 2024–2026 wave of texts (Loi 41.26, décrets 2.24.706, 2.25.1064, 2.26.434, draft 2.26.838) all amend **Law 58.23 itself** or **Décret 2.23.1067** (amounts, procedure, CNSS-declaration edge cases) — none touches the threshold decree.

### Cited Findings
- **ANSS's official list of the ASD legal framework, read in full (French and Arabic versions), enumerates every text through July 2026 and contains no amendment to 2.23.1068.** The list is: loi-cadre 09-21; loi 59-23; loi 58-23; **loi 041-26** (dahir 1-26-23, 9 Muharram 1448 / 25 June 2026); décret 2.23.1067; décret 2.23.1068 ("Fixant le seuil d'éligibilité au Régime des Aides Sociales Directes", listed with its original 1 December 2023 date and **with no "modifié par" annotation**); décret 2.23.1069; décret 2.24.706 (BO 7321, 29 July 2024); décret 2.25.1064 (BO 7468, 23 December 2025); décret 2-26-434 (8 Safar 1448 / 23 July 2026) — [ANSS, Lois & décrets (FR)](https://anss.gov.ma/fr/lois-decrets); [ANSS, المراجع (AR)](https://www.anss.gov.ma/ar/lois-decrets)
- **The scope of each later text, as described by ANSS:**
  - **Décret 2.24.706** — *"Complétant l'annexe du décret n° 2.23.1067"* (adds to the annex of the 1067 decree; i.e. amounts, not the threshold). — [ANSS FR](https://anss.gov.ma/fr/lois-decrets)
  - **Décret 2-26-434** — *"complétant le décret n° 2-23-1067 … pris pour l'application de la loi n° 58-23"* (again 1067, not 1068). — [ANSS FR](https://anss.gov.ma/fr/lois-decrets)
  - **Décret 2.25.1064** — *"relatif au bénéfice de l'aide spéciale"* (BO 7468, 23 December 2025); separate subject, not the ASD threshold. — [ANSS FR](https://anss.gov.ma/fr/lois-decrets)
- **Loi 041-26 (promulgated 25 June 2026) amends Law 58.23 only in three places**, per the bill text adopted by the Chamber of Councillors: it inserts **article 16 bis** (one-off exceptional allowance for families that lost ASD because a spouse/head of household was declared to CNSS) and **article 16 bis bis** (recovery of entitlement after job loss, without the waiting period), and amends **article 17** (management of the regime and the exceptional allowance). **Article 3 — the article that carries the threshold condition — is not amended.** — [Chambre des Conseillers, texte adopté, projet de loi 041.26, PDF](https://www.chambresdesconseillers.ma/docs/%D9%86%D8%B5%D9%88%D8%B5%20%D8%AA%D8%B4%D8%B1%D9%8A%D8%B9%D9%8A%D8%A9/lois_approuv%C3%A9es/%D9%85%D8%B4%D8%B1%D9%88%D8%B9%20%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%B1%D9%82%D9%85%20041.26.pdf) *(note: URL as indexed; the PDF text is OCR-noisy but the article structure is legible)*; corroborated by [La Vie Éco, 10 June 2026](https://www.lavieeco.com/au-royaume/parlement-adoption-du-projet-de-loi-relatif-aux-aides-sociales-directes)
- **Décret 2.26.434 (22–23 July 2026)** implements Loi 41.26 by amending **Décret 2.23.1067**: 12-month duration for the exceptional allowance, one-year cumul of ASD with employment income, removal of the 12-month waiting period before reinstatement. No threshold change. — [Le360, 23 July 2026](https://fr.le360.ma/societe/soutien-social-direct-suppression-du-delai-dattente-et-plafonnement-de-lallocation-exceptionnelle_LPQ54AB66JHEFBLGHOKHDQESU4)
- **Draft décret 2.26.838 (adopted by Council of Government 12 November 2026)** raises the **minimum monthly amount from 500 to 600 DH from 1 January 2027** (trajectory to 1,000 DH by 2031) and amends **Décret 2.23.1067**. It does not concern the eligibility threshold. — [Le360, 13 November 2026](https://fr.le360.ma/economie/aide-sociale-directe-le-montant-minimum-passera-a-600-dirhams-des-janvier-2027_YK2FO2DSIRBMRJ7QDRQS3M2YKQ); [Maroc.ma / MAP, 12 November 2026](https://maroc.ma/fr/actualites/conseil-du-gouvernement-adoption-dun-projet-de-decret-relatif-au-regime-des-aides-sociales-directes)
- **Positive confirmation that the value was still 9,743001 at the end of 2025 and again in January 2026** — [Le360, 9 December 2025](https://fr.le360.ma/economie/aides-sociales-directes-124-millions-de-beneficiaires-a-fin-novembre_LIUD3NOSCFGEJOBHYALGC7J534); [Madar21, 3 January 2026](https://madar21.com/396719.html)

### Inferences
- The threshold has been **stable since entry into force** and has survived three "reform waves" (2024 rentrée allowance, 2025 first amount increase, 2026 CNSS/exceptional-allowance reform) without change.
- The 2026 reform deliberately addressed the **"effet de seuil"** complaint by *adding* an exceptional allowance and cumul rules rather than by moving the threshold — consistent with Lekjaa's stated approach of correcting exclusion effects without repricing the targeting score.

### Gaps
- **No consolidated/annotated version of Décret 2.23.1068 was located on a primary portal.** The SGG site did not serve the BO 7253 PDF for me (404s), and Adala (Ministry of Justice) returned only navigation/listing pages in the responses I could retrieve — I could not confirm a "texte consolidé" page for 2.23.1068. The negative finding on amendment therefore rests on (a) ANSS's exhaustive official list, which is current to July 2026 and annotates amendments elsewhere, and (b) the absence of any press, parliamentary or governmental trace of an amendment. This is strong but is **negative evidence from sources consulted, not a certificate of non-amendment**.
- I did not locate the **BO issue number** for décrets 2.25.1064 (BO 7468 per ANSS) or 2.26.434 (BO number not stated by ANSS or Le360); irrelevant to the threshold but worth flagging as unconfirmed detail.
- **A separate 2026 reform of the targeting indicator itself** (headlined as *"le revenu réel comme indicateur"*) surfaced in a Le360 cross-reference during search but I did not open or verify it. It could, if real, affect *how* the score is computed (not the threshold value). **This is unverified and should be checked before asserting that the RSU score methodology is unchanged.**

---

## Q3. Is the threshold defined against the "score socio-économique" of the RSU, and how is it expressed/rounded?

### Takeaway
**Indirectly, yes — but the decree does not itself use the words "score" or "indice".** Article 1 fixes the value of the threshold that **item 5 of article 3 of Law 58.23** requires a family to meet; that threshold is applied in practice to the RSU socio-economic index. The decree states the value with **six decimal places and a comma separator, with no rounding rule and no stated comparison operator**.

### Cited Findings
- **The anchoring provision, quoted in full from Law 58.23 as published in the same BO issue.** Article 3 lists the conditions for childhood-risk benefits; item 5 reads:
  > 5. أن تستجيب للعتبة المحددة بنص تنظيمي.
  
  (*"5. that it meet the threshold set by regulatory text."*) — [ANSS, Loi n° 58.23, BO 7253 PDF](https://anss.gov.ma/sites/default/files/decrets/Loi_n58.23_AR.pdf)
- **The decree's own preamble cites only article 3 of Law 58.23** as its substantive basis, and article 1 cross-refers to *"البند 5 من المادة 3"* — so the decree is precisely the "نص تنظيمي" (regulatory text) contemplated by article 3(5). — [ANSS, scanned BO 7253 PDF](https://www.anss.gov.ma/sites/default/files/decrets/decret_n2.23.1068_AR.pdf)
- **Government communiqué framing:** the draft decree implements *"المادة 3"* of Law 58.23, *"التي تنص على ضرورة استجابة الأسر الراغبة في الاستفادة من النظام المذكور للعتبة الموضوعة له"*, and also implements **article 11 of Law 72.18**, *"التي نصت على أن لكل برنامج من برامج الدعم الاجتماعي المباشر عتبة محددة خاصة به"* (each social support programme has its own specific threshold). — [Chef du Gouvernement, 30 November 2023](https://www.cg.gov.ma/ar/node/11560)
- **ANSS, in its own operational guidance, identifies the object as the RSU socio-economic index and states the operator as "less than or equal":** *"si l'indice socio-économique obtenu est inférieur ou égal au seuil d'éligibilité fixé à 9,743001, la demande d'Aides Sociales Directes peut être déposée"* — [ANSS, "Application Steps"](https://anss.gov.ma/en/etapes-de-demande-de-benefice)
- **ANSS slide deck uses the word "score" explicitly:** *"Satisfaire le score d'éligibilité : 9,743001"*. The same deck elsewhere says *"doit être inférieur au seuil"* (strictly "less than"), which is **inconsistent with the ANSS website's "inférieur ou égal"** — [UNESCWA-hosted ANSS presentation, Nov 2024, PDF](https://www.unescwa.org/sites/default/files/event/materials/Status%20of%20the%20Direct%20Social%20Assistance%20Scheme%20in%20Morocco_FR.pdf)
- **How the index is produced, per the minister:** a scoring grid using **35 variables in urban areas and 28 in rural areas**, with the eligibility threshold at **9,743001 points** — [Le360, 9 December 2025](https://fr.le360.ma/economie/aides-sociales-directes-124-millions-de-beneficiaires-a-fin-novembre_LIUD3NOSCFGEJOBHYALGC7J534)
- **Direction of the scale is confirmed by ANSS/press:** a *lower* index means *greater* vulnerability, so the test is a ceiling, not a floor — *"Le seuil d'éligibilité … est de 9,743001 : un ménage est éligible si son indice socio-économique est inférieur ou égal à ce seuil"* — [Simul.ma, updated 14 August 2026](https://simul.ma/fr/aides-sociales/indice-social) *(secondary source, consistent with ANSS)*
- **Press habitually rounds the figure to 9.74** in prose (e.g. *"un score RSU inférieur ou égal à 9,74"*) — [Démarches Maroc, 8 April 2026](https://www.demarchesmaroc.com/aide-sociale-directe/) — which is why the six-decimal form must come from the BO, not from press.

### Inferences
- **Attribution chain, stated precisely:** BO 7253 → Décret 2.23.1068 art. 1 → value 9,743001 → applied to the "indice/score socio-économique" computed by the RSU under Law 72.18. Calling 9.743001 "the RSU score ceiling for ASD eligibility" is **accurate in substance**, but attributing the phrase *"score socio-économique"* to the decree's own wording would be **inaccurate**: the decree says "عتبة الاستفادة" (threshold of benefit) and cross-refers to Law 58.23 art. 3(5), which itself says only "العتبة المحددة بنص تنظيمي".
- **No rounding rule exists in the instrument.** The decree fixes one number to six decimals; there is no "rounded to", "arrondi à" or tolerance clause. The six-decimal precision (rather than 9.74) is presumably to place the cut exactly on a computable boundary of the index.
- **The boundary case (score exactly 9.743001) is decided by administrative guidance, not by the decree.** ANSS's own site says "≤", the ANSS slide says "<". The model's test fixture (`9.743001` eligible, `9.743002` not) follows the ANSS website reading; that is the better-supported reading but it is **not textually compelled by the decree**, and a downstream report should say so.

### Gaps
- **The comparison operator is not in the decree and the two ANSS sources conflict** ("inférieur ou égal" on the website vs "inférieur" in the Nov 2024 slide). No primary text resolves it. The decider, if one is needed, is the actual RSU/asd.ma platform behaviour, which cannot be observed without an eligible household account.
- **The index formula is not public.** ANSS/press state only that it is computed from declared household data (composition, income, housing/ living conditions) with 35 urban / 28 rural variables; no weighting or normalisation is published. No source gives the mathematical form of the index or why 9.743001 was chosen as the cut (the ~60% coverage figure is the only stated rationale).
- **Historic context is unverified.** One academic article states the RSU fixed cut-off was previously **9.72** and was raised by décret 2.23.1068, and that the RSU decree annex sets urban/rural constants of **9.92 / 9.69** — [Maghreb Law review, 25 November 2024](https://maroclaw.com/%D9%86%D8%B8%D8%A7%D9%85-%D8%A7%D9%84%D8%AF%D8%B9%D9%85-%D8%A7%D9%84%D8%A7%D8%AC%D8%AA%D9%85%D8%A7%D8%B9%D9%8A-%D8%A7%D9%84%D9%85%D8%A8%D8%A7%D8%B4%D8%B1-%D8%A8%D8%A7%D9%84%D9%85%D8%BA%D8%B1%D8%A8). I did **not** verify these against the RSU implementing decree (2.23.xxx under Law 72.18), so do not treat them as established.
- **The official French BO text of both Law 58.23 and Décret 2.23.1068 remains unread** (SGG PDF 404). All French quotes here are either ANSS's own French summaries or translations.
