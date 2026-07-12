# RQ Registry — research questions, evidence, and where each is answered

Successor to the bucket list in `26.06.md`, extended to the full three-corpus system
(ECHR EN · Austrian OGH DE · Swiss courts DE). Every RQ names the notebook/report that
answers it and the kind of evidence behind it. **The probe topic (parental alienation /
Kindeswohl) exercises the system; the system's measured behaviour is the finding.**

---

## Thesis-level research questions (the spine)

### RQ1 — Capability boundary
*Which classes of natural-language legal questions can a retrieval-plus-extraction system
answer faithfully over a multilingual case corpus, and which must it refuse?*

**Answer form:** the three-bucket typology + a **measured router**.

| Evidence | Where |
|---|---|
| Bucket routing accuracy **0.95** on a frozen 60-question gold set (20/bucket, 30 DE / 30 EN) | `src/router_evaluation.ipynb`, `reports/router_evaluation_report.md` |
| Fabrication risk (Bucket-3 sent to retrieval) **0.10**; over-abstention **0.00** | same |
| Known limit, stated: aggregate intent without a lexical trigger ("most common", "more often than") | failure table, same report |
| Ranking quality: frozen 24-query set, automatic diagnostics + precision@6 template | `src/retrieval_evaluation.ipynb`, `reports/retrieval_evaluation_report.md` |

### RQ2 — Structured extraction as boundary-mover
*Can Bucket-3 questions be answered by extracting auditable structured fields, at what
measured reliability?*

**Answer form:** a controlled comparison — transparent rules vs local LLM — on identical
frozen gold labels (n=120, stratified).

| Evidence | Where |
|---|---|
| Rules extractor: P 0.543 / R 0.475 / **F1 0.507** | `reports/extraction_validation_report.md` |
| LLM extractor (llama3.2, local, temp 0): same metrics, same sample | `src/echr_extraction_llm.ipynb`, `reports/llm_vs_rules_extraction.md` |
| Agreement breakdown: what the LLM adds vs what it loses in auditability | same |
| Per-cell provenance + confidence in the deployed table (1,116 rows, corpus 2000–2025) | `data/echr_extracted.parquet` |

### RQ3 — Faithful abstention / calibrated uncertainty
*Can the system know what it doesn't know — at the query level and the field level?*

| Evidence | Where |
|---|---|
| Query level: 3 abstention layers (aggregate router · no-hits · boilerplate-only), router measured under RQ1 | `src/rag_echr_ris.ipynb` |
| Field level: **ECE raw 0.179 → 0.068 after isotonic calibration, validated 5-fold out-of-fold** (the citable unseen-data claim) | `src/extraction_validation.ipynb`, `figures/alienation_reliability_diagram.png` |
| Finding, not hidden: the transparent rule confidence is **non-monotonic** (~0.7 band less reliable than ~0.45 band); calibration repairs probability meaning at the cost of ranking granularity | `reports/extraction_validation_report.md` |
| Threshold-aware SQL: `min_confidence` = field-level abstention, excluded cells always counted | `src/echr_query.ipynb` |

### RQ4 — Cross-lingual generality
*Does the approach hold across the German/English split?*

**Scoped honest answer:** retrieval is multilingual and measured; extraction is validated
ECHR-English only (stated domain of validity).

| Evidence | Where |
|---|---|
| Shared index: **42,055 chunks — 15,136 EN (ECHR) + 26,919 DE (1,931 AT, 24,988 CH)**, corpus 2000–2025 — one embedding space (multilingual-e5-base) | `src/rag_echr_ris.ipynb` |
| Jurisdiction mix of top-k per query language (do DE queries reach the DE corpora?) | `src/retrieval_evaluation.ipynb` |
| Router works in both languages (per-language accuracy table) | `reports/router_evaluation_report.md` |
| Extraction/calibration explicitly NOT transferred to DE corpora — re-labelling protocol stated | `extraction_validation.ipynb` §7 |

---

## Bucket registry — concrete questions the system now answers (or refuses)

### Bucket 1 — explanatory / comparative / framing → retrieval answers with citations
Existing (ECHR + AT principles), now extended by AT full decisions + Swiss corpus:

1. How does the ECtHR frame the State's positive obligations in contact-enforcement cases? *(ECHR)*
2. Wann ist von einer Vollzugsmaßnahme abzusehen, wenn sie dem Kindeswohl widerspricht? *(AT)*
3. **NEW** Unter welchen Voraussetzungen kann einem Elternteil die Obhut entzogen werden? *(CH — Swiss register now retrievable)*
4. **NEW** How do the three jurisdictions frame the child's refusal of contact — enforcement problem (ECHR), Kindeswohl limit (AT), or Anhörung/participation issue (CH)? *(cross-jurisdiction comparative — the strongest new Bucket-1 class)*
5. **NEW** Rechtssatz vs decision text: does the OGH's distilled principle match the reasoning in the underlying decisions? *(AT — possible now that both genres are indexed, `genre=principle` vs `genre=decision`)*
6. ECHR framing prevalence: state-failure ≫ psychological (45% vs 1% of judgments) — lexicon-based, caveated *(src/echr_framing_analysis.ipynb)*

### Bucket 2 — metadata aggregates → computed via SQL, no NLP
Existing (ECHR respondent/outcome/genre), now extended by Swiss + RIS metadata relations and
the 2026-07-07 HUDOC fields — kpthesaurus concept codes, formation
(Committee/Chamber/Grand Chamber), and `introductiondate` (`src/echr_query.ipynb` §6b):

- **The moved boundary:** "how long do proceedings last?" was a Bucket-3 refusal example;
  with `introductiondate` it became Bucket-2 metadata (admissibility decisions: median
  2.9 years application→decision, n=307). The bucket boundary is set by data availability —
  and it visibly moved.

7. Cases per respondent state; violation share per state where alienation is alleged *(ECHR, canned queries)*
8. **NEW** Corpus volume per year per jurisdiction 2015–2025 *(ECHR × AT × CH in one SQL)*
9. **NEW** Swiss decisions per canton / per court level *(CH metadata)*
10. **NEW** RIS records by document type (Rechtssatz vs decision) over time *(AT metadata)*
11. Standing caveat, always printed: counts describe the keyword-matched corpora, **not** litigation rates.

### Bucket 3 — content aggregates → extraction table or honest abstention
12. How many cases allege parental alienation? → answered from the calibrated table with a
    user-set confidence threshold; excluded cells reported *(ECHR only)*
13. Which parent is found responsible in most cases? → **refused** by the router (fabrication
    risk class; measured) unless a validated field exists
14. Custody-outcome / marital-status aggregates → named as extraction candidates; currently
    correctly refused *(future fields, same 3-layer pattern)*. Proceedings-duration left this
    list on 2026-07-07 — see the moved boundary above.
15. **NEW** Any Bucket-3 question against AT/CH corpora → refused with the domain-of-validity
    rationale (calibration is ECHR-English only) — the honest RQ4 boundary in action.

---

## New result families (July 2026 — all topic-agnostic, evidence per file)

| result | headline | where |
|---|---|---|
| ECHR precedent network | Hokkanen/Kutzner/Elsholz anchor the field; precedent base diversifying (top-10 share 13%→6%); median precedent age 8y | `reports/citation_network_report.md` |
| Austrian principle lifecycles | median active span 30y (max 70); 71% living law | same + `figures/ris_principle_lifecycles.png` |
| Strasbourg speed | median 3.5y (2000-09) → ~2.8y after 2010 | `reports/trends_variation_report.md` |
| Violation structure | Committee 94.9% vs Chamber 62.6% violation share (WECL mechanism in metadata) | same |
| Cantonal variation (CH) | practice-instrument mention rates per canton (keyword, caveated) | same + `figures/swiss_cantonal_variation.png` |
| Principle faithfulness | 26/29 Rechtssätze specifically closer to own case-law (0.896 vs 0.863) | `reports/principle_faithfulness_report.md` |
| Extraction domain shift | 2015-25-validated extractor + calibration tested on 2000-14 gold (n=40) | `reports/extraction_domain_shift_report.md` |
| Reusability matrix | component × cost-to-move-to-new-topic, measured | `reusability.md` |

## Explicitly out of scope (stated, not hidden)
- German (openlegaldata) corpus — cut (off-topic search results).
- Extraction/calibration on RIS/Swiss text — future work (needs a frozen labelled sample per
  corpus; protocol already defined in `extraction_validation.ipynb`).
- Generation quality evaluation — generation runs (local Ollama) but is not a validated
  contribution; retrieval + extraction + abstention are.
- Diachronic claims about doctrine — `src/diachronic_analysis.ipynb` produces reading
  shortlists, not findings (its internal RQ numbering is notebook-local).
