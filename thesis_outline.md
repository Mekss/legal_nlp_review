# Thesis outline — detailed, section-level (v2: framing-analysis center of gravity)

**Working title:** *A Faithful, Auditable Pipeline for Comparative Framing Analysis of Legal Corpora — How Three Jurisdictions Frame Parental Alienation and Child Welfare*

**Discipline:** computational social science / digital humanities.

**Center of gravity (decided):** the measured faithfulness pipeline is the **method**; a theory-grounded **comparative framing analysis** across ECHR / Austria / Switzerland is the **substantive contribution**. The faithfulness work is *why the framing findings can be trusted and audited*.

**Thesis statement (lock this in before drafting prose):**
> Reliable social-scientific framing analysis over legal corpora requires a retrieval-and-extraction pipeline that knows what it cannot answer. This thesis builds and *measures* such a pipeline (faithful retrieval, calibrated extraction, honest abstention), then uses it to characterise — comparatively and diachronically — how the ECtHR, the Austrian OGH, and the Swiss courts frame parental alienation and child-welfare disputes. The methodological contribution (a measured capability boundary) and the substantive contribution (a comparative framing analysis) are two halves of one argument: the second is credible only because the first is measured.

**Evidence tags:** `[HAVE]` evidence exists, job is exposition · `[WRITE]` prose that exists nowhere yet · `[BUILD]` new analysis/code needed · `[ADD]` small addition to existing code.

---

## Ch. 1 — Introduction  `[WRITE]`

- **1.1 Motivation.** Two motivations, joined: (a) LLM legal QA fabricates — faithfulness, not fluency, is the bottleneck; (b) legal corpora are a rich but under-analysed site of *framing* — how courts define a problem, attribute cause, and prescribe remedy. You cannot do (b) at scale without solving (a).
- **1.2 The problem.** Characterise *how* three jurisdictions frame parental alienation / child welfare — and build the faithful machinery that makes such a characterisation trustworthy rather than a hallucinated summary.
- **1.3 The probe topic, and why it is the right one.** Entfremdung ≠ alienation; Kindeswohl, Obsorge, Obhut, Kontaktrecht do not map cleanly. That non-correspondence is not a nuisance — it *is* the framing phenomenon under study, and it stress-tests the pipeline. (Forward-ref the construct critique §2.7.)
- **1.4 Research questions.** Split into method RQs and substantive RQs:
  - **Method (does the pipeline earn trust?):** M1 capability boundary/router · M2 extraction as boundary-mover · M3 calibrated abstention · M4 cross-lingual generality. (Source: `rq_registry.md`.)
  - **Substantive (what does it reveal?):** S1 How does each jurisdiction dominantly frame these disputes? · S2 How does framing differ *across* the three? · S3 How has framing shifted over time? · S4 Where do the frames fail to translate, and what does that reveal?
- **1.5 Contributions.** Method: measured router + three-layer abstention + calibrated extraction; a reusable pipeline. Substance: a theory-grounded, reliability-tested, cross-jurisdiction framing analysis. The coupling: extraction+calibration reused to *scale a validated framing codebook* (§6.5).
- **1.6 Roadmap.**

---

## Ch. 2 — Background and Related Work  `[WRITE — biggest gap]`

*Two literature strands, because the thesis has two halves.*

**Strand A — the method:**
- **2.1 Legal information retrieval and legal NLP.**
- **2.2 RAG and its failure modes.** Retrieving boilerplate/recitals over reasoning — forward-ref your *genre finding* (§5.2) as an empirical instance.
- **2.3 Faithfulness, groundedness, hallucination.** *Define faithfulness here* — load-bearing for the whole thesis; distinguish from factuality/groundedness.
- **2.4 Calibration, selective prediction, abstention.** ECE, reliability diagrams, isotonic regression, reject-option — your field-level abstention as an instance.
- **2.5 Multilingual dense retrieval.** Single multilingual-e5 space across DE/EN.

**Strand B — the substance:**
- **2.6 Framing theory and framing analysis.** Entman's four functions (define problem / diagnose cause / moral evaluation / prescribe remedy); framing in media and in *legal/judicial discourse*; computational framing analysis and its pitfalls (lexicon validity, denominators). This is what makes the thesis *social analysis* rather than keyword counting.
- **2.7 The parental-alienation construct as contested.** Scholarly and institutional criticism (incl. WHO's handling of "parental alienation syndrome"). Justify use-as-probe **without endorsing** the construct — examiner-critical for CSS/DH.
- **2.8 Gap statement.** No prior work jointly (i) measures a faithful capability boundary over a multilingual legal corpus and (ii) uses it for a reliability-tested comparative framing analysis.

---

## Ch. 3 — Corpus and Data  `[HAVE — expository]`

- **3.1 Source selection.** ECHR (HUDOC/echr-extractor, EN, Art.-8, 2000–2025) · RIS OGD v2.6 (Austria/OGH, DE, Rechtssätze + civil full decisions) · entscheidsuche.ch (Switzerland, DE). All public, no paid APIs, local/CPU. (`master_import.ipynb`; `project_overview.md` §2.)
- **3.2 Collection and provenance.** Stable IDs, provenance, new/extend modes, verification cell.
- **3.3 The probe-topic keyword design and the homonym problem.** One `KEYWORDS` dict; *Entfremdung* misappropriation homonym; criminal senates excluded. This is itself a first framing observation (the word carries two frames). (`echr_query.ipynb` §6b quantifies it.)
- **3.4 Corpus statistics.** 42,055 chunks, ~64% German; chunking (~600-word windows / 80 overlap; ECHR split by section first). (`data_summary.ipynb`; `corpus_audit_report.md`; glossary `project_overview.md` §6½.)
- **3.5 Coverage limits as corpus facts.** Thin pre-2010 CH cantonal coverage; counts = keyword-matched collections, **not** litigation rates (a framing-analysis denominator caveat).
- **3.6 Data ethics.** Public court record; pseudonymisation posture; GDPR. `[WRITE — partly new]`

---

## Ch. 4 — The Faithful Pipeline (System Design)  `[HAVE — expository]`

- **4.1 The three-bucket capability typology.** Bucket 1 explanatory/comparative→retrieval+citations; Bucket 2 metadata→SQL; Bucket 3 content aggregates→abstention *or* validated extraction. (`ask.ipynb`; `project_overview.md` §3.)
- **4.2 Genre-aware multilingual retrieval.** multilingual-e5-base, exact cosine, CPU; chunk metadata; MMR; citations never cross jurisdictions. (`rag_echr_ris.ipynb`.)
- **4.3 The router.** Lexical aggregate-intent detection. (`rag_echr_ris.ipynb` Layer-1.)
- **4.4 Three abstention layers.** Aggregate router · no-hits · boilerplate-only; the §11 before/after (6/6 pending-case boilerplate at cosine 0.88 → routed out).
- **4.5 Structured extraction.** The transparent ~40-line rules extractor for `alienation_alleged` (a party's *allegation*, never the court's finding); per-cell confidence + provenance. (`echr_extraction.ipynb`.)
- **4.6 Calibration and threshold-as-abstention.** Isotonic; `min_confidence` = field-level abstention; excluded cells counted. (`extraction_validation.ipynb`; `echr_query.ipynb` Layer 3.)
- **4.7 Guarded NL→SQL.** Coder model, EXPLAIN-validated, SQL printed above result; deterministic refusal nets, not the model (the *lazy-escape* observation). (`echr_query.ipynb` §6d.)
- **4.8 The unified interface.** `ask_anything()` / `ask_web.py` — the typology as one function; the working chatbot.

---

## Ch. 5 — Method Evaluation: Does the Pipeline Earn Trust?  `[HAVE — + rigor additions]`

- **5.1 Gold sets and metric definitions.** Router 60Q (`router_gold_questions.csv`); retrieval 24Q + `retrieval_judgments.csv`; extraction 120 labels. Lift the glossary from `project_overview.md` §6½.
- **5.2 M1 + the genre finding (headline).** Router acc 0.95, fabrication 0.10, over-abstention 0.00; precision driven by *genre* not language (ECHR precise only in LAW = 0.69/0.73; FACTS/HEADER/PROCEDURE/OPERATIVE = 0.00 on both indexes). (`router_evaluation_report.md`; `retrieval_evaluation_report.md`.)
- **5.3 M2 extraction as boundary-mover.** Rules F1 0.507 vs llama3.2 F1 0.593 on identical gold; agreement breakdown; transparency/accuracy trade-off. (`llm_vs_rules_extraction.md`.) *Fig:* `echr_alienation_class_balance.png`.
- **5.4 M3 calibrated abstention.** ECE 0.179→0.068 OOF; non-monotonic raw confidence; threshold demo. (`extraction_validation_report.md`.) *Fig:* `alienation_reliability_diagram.png`.
- **5.5 M4 cross-lingual generality.** DE→AT/CH only, EN→ECHR only; extraction validated ECHR-EN only. (`retrieval_evaluation_report.md`.)
- **5.6 The moved boundary.** Proceedings duration: Bucket-3 refusal → Bucket-2 metadata once `introductiondate` arrived (admissibility median 2.9y, n=307). (`echr_query.ipynb` §6c.)
- **5.7 Threats to validity + rigor additions.** `[ADD]` inter-annotator κ on a double-labelled subsample; bootstrap CIs on precision@6 / F1 / ECE. `[WRITE]` baselines: BM25 retrieval floor + vanilla-LLM ceiling, so the numbers read as *value*.

---

## Ch. 6 — Framing Coding Scheme and Reliability (the substantive method)  `[BUILD + WRITE — new core]`

*This is the new intellectual center. It converts the ad-hoc lexicon into a defensible instrument and connects method to substance.*

- **6.1 From lexicon to codebook.** The current `LEXICONS` (state_failure / psychological / cultural-religious) in `echr_framing_analysis.ipynb` become *hypotheses*, not the instrument. Derive a codebook from framing theory (§2.6): per frame, its problem-definition / causal-attribution / moral-evaluation / remedy signature. `[BUILD]`
- **6.2 Unit of analysis and sampling frame.** What is coded (the reasoning/assessment section per case — already isolated as `_section` in the framing notebook), the population, and the **denominators** for every prevalence claim. `[WRITE]`
- **6.3 Human coding and inter-coder reliability.** Double-code a stratified sample across all three jurisdictions; report Krippendorff's α / Cohen's κ per frame. This is the reliability the current notebook explicitly lacks ("clusters are not definitive framings"). `[BUILD]`
- **6.4 Scaling the codebook with the faithful pipeline — the coupling.** Reuse the §4.5–4.6 extraction+calibration machinery to apply the validated codebook at corpus scale: each case gets a frame label + calibrated confidence, low-confidence cases *abstain* rather than guess. Validate machine-coding against the human codes exactly as extraction was validated (P/R/F1, ECE). **This is where "faithful method enables framing findings" becomes concrete.** `[BUILD]`
- **6.5 Validated summarisation.** For the qualitative "how does court X interpret this" output, measure summary faithfulness against the retrieved passages (not just retrieval precision), so the chatbot's summaries are a claim, not a disclaimer. `[BUILD]`

---

## Ch. 7 — Comparative Framing Findings (the payoff)  `[BUILD — partly HAVE]`

- **7.1 Framing prevalence per jurisdiction.** ECHR: state-failure 45% ≫ psychological 1%, children's-rights 29% — now re-derived under the §6 codebook with reliability, not the raw lexicon. `[HAVE→re-derive]` AT and CH: **built for the first time** — the current framing notebook never touches them. `[BUILD]` *Fig:* `echr_framing_prevalence.png` (+ new AT/CH figures).
- **7.2 Cross-jurisdiction comparison (S2 — the headline substantive result).** How the *same* dispute is framed differently: enforcement-failure (ECHR) vs Kindeswohl-limit (AT) vs Anhörung/participation (CH). The strongest new deliverable; does not exist yet as an analysis. `[BUILD]`
- **7.3 Diachronic framing shift (S3).** EN active in `diachronic_analysis.ipynb`; DE "wired, deferred" — activate it. Apply denominator discipline (the "14% rise" that dissolved under length normalisation is a *methods demonstration* to include, not hide). `[HAVE (EN) + BUILD (DE)]` *Fig:* `diachronic_en.png` (+ DE).
- **7.4 Where frames fail to translate (S4).** The homonym and the non-mapping concepts read as *findings about framing*, not just data-cleaning notes.
- **7.5 Qualitative illustrations.** KWIC / worked examples per frame per jurisdiction, retrieved faithfully with citations — the human-readable texture behind the counts.

---

## Ch. 8 — Discussion  `[WRITE]`

- **8.1 What the measured boundary means for social analysis of legal text.** Faithful answerability is set by *how* an answer is grounded, not by topic — and that is precisely what lets a framing analyst trust the output.
- **8.2 The genre lesson generalises.** The failure was never the generator — it was unfaithful *selection*; implication for computational discourse analysis broadly.
- **8.3 Substantive reading of the framing findings.** What the cross-jurisdiction and diachronic patterns say about how these legal cultures construct the child-welfare problem — interpreted, cautiously, as discourse.
- **8.4 Reusability / generality.** Component × cost-to-move-to-new-topic; the pipeline as a reusable framing-analysis instrument. (`reusability.md`.)
- **8.5 Return to the gap (§2.8).**

---

## Ch. 9 — Limitations  `[HAVE — sharpen]`

Gold labels (n=120, single annotator, anchoring); corpus-extension sample frame; framing codebook reliability bounds; extraction domain-of-validity (ECHR-EN, though §6.4 extends the *coding* cross-jurisdiction — state the distinction carefully); lexical router; counts ≠ litigation rates; lexicon/codebook validity as the ceiling on framing claims. Pair each with its §5.7/§6.3 mitigation. (Base: `project_overview.md` §7.)

---

## Ch. 10 — Conclusion and Future Work  `[WRITE]`

- Restate the two coupled contributions.
- Future work: extend calibrated extraction to AT/CH content fields; second/third frame dimensions; a second probe topic to test the reusable instrument.

---

## Appendices  `[HAVE]`

- **A. Reproducibility** — notebook reading order (`project_overview.md` §5); CPU-only; `data_registry.json`, `value_registry.json`.
- **B. Prompts and model configs** — NL→SQL few-shot; LLM extractor prompt (temp 0, llama3.2).
- **C. Framing codebook** — full definitions, decision rules, coded examples; reliability tables.
- **D. Gold sets and judgments** — `router_gold_questions.csv`, `retrieval_judgments.csv`, extraction + framing labels.
- **E. Corpus-structure supporting analyses** (demoted from headline): precedent network (`citation_network_report.md`, `echr_precedent_network.png`), Austrian principle lifecycles (`ris_principle_lifecycles.png`), Strasbourg speed / violation structure (`trends_variation_report.md`), principle faithfulness (`ris_principle_faithfulness.png`), extraction domain shift (`extraction_domain_shift_report.md`), cantonal variation (`swiss_cantonal_variation.png`).

---

## Pre-writing / pre-analysis checklist

*Prose (do while writing):*
1. **Write Ch. 2 both strands** — method + framing theory; the highest-leverage missing piece.
2. **Define faithfulness** (§2.3) and **ground the frame categories in framing theory** (§2.6) before using either downstream.
3. **Foreground the construct critique** (§2.7).

*Analysis/code (the new build, in priority order):*
4. **The framing codebook + inter-coder reliability** (§6.1–6.3) — the substantive method; nothing in Ch. 7 is defensible without it.
5. **Extend framing analysis to AT and CH** (§7.1–7.2) — the comparative payoff; currently ECHR-only.
6. **Scale the codebook via extraction+calibration and validate it** (§6.4) — the method↔substance coupling.
7. **Activate DE diachronic** (§7.3) and **validate summarisation** (§6.5).
8. **Method-side rigor** (§5.7) — κ subsample, bootstrap CIs, BM25 + vanilla-LLM baselines.
