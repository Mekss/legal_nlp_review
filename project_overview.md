# Faithful Question-Answering over a Multilingual Legal Corpus
### Project overview and reading guide (status: July 2026)

---

## 1. The thesis in one paragraph

This is a **computational-methods thesis**: it builds and — more importantly — **measures** a
retrieval-plus-extraction system over multilingual case law, asking *which classes of legal
questions such a system can answer faithfully, and which it must refuse*. The probe topic is
**parental alienation / child welfare** (Entfremdung, Kindeswohl, Obsorge, Obhut, Kontaktrecht)
— chosen deliberately because the concept does not map cleanly across languages and
jurisdictions, which stress-tests every component. The topic is the *test load*, not the
subject of a legal claim: **the system's measured behaviour is the finding**, not a doctrine
of alienation jurisprudence.

## 2. The corpus (all public, no paid APIs, all local/CPU)

| source | jurisdiction | language | documents | what it is |
|---|---|---|---|---|
| HUDOC via `echr-extractor` | ECHR | EN | 1,116 | Art.-8 judgments, admissibility decisions, communicated cases — **2000–2025**, incl. `kpthesaurus` (Registry concept codes), formation (Committee/Chamber/**Grand Chamber**), and `introductiondate` |
| RIS OGD API v2.6 | Austria (OGH) | DE | 38 + ~500 | Rechtssätze (distilled principles) + civil-senate full decisions (criminal senates excluded — the *Entfremdung* = misappropriation homonym) |
| entscheidsuche.ch | Switzerland | DE | 2,031 | full decisions, cantonal + federal (court annual reports filtered out; pre-2010 cantonal coverage is thin — a stated corpus fact) |

Shared index: **42,055 chunks — 64 % German** — one multilingual embedding space
(intfloat/multilingual-e5-base, exact cosine, CPU). Every chunk carries jurisdiction,
language, genre, section and a stable ID; citations never cross jurisdictions.

**The tool is generic by design**: the topic is one `KEYWORDS` dict in the importer;
everything from import through metadata analytics to retrieval-with-abstention transfers
unchanged (demonstrated twice: 2015–2025 and 2000–2025 corpora). What does *not* transfer
for free — per-topic homonym curation and per-field extraction labelling — is measured and
stated in `reusability.md`; the proof-of-concept is `src/ask.ipynb`.

## 3. The capability typology (the spine of the thesis)

Legal questions split into three buckets by *how* a system can answer them faithfully:

- **Bucket 1 — explanatory / comparative** → retrieval answers, with citations.
- **Bucket 2 — metadata aggregates** ("how many cases against Norway") → plain SQL over
  structured fields; no NLP, no uncertainty.
- **Bucket 3 — content aggregates** ("how many cases *allege alienation*") → the answer lives
  inside each judgment's prose. Top-k retrieval would *fabricate* a count; the faithful options
  are **honest abstention** or **validated extraction**.

Every result below measures one edge of that typology.

## 4. Headline results (all reproducible from the notebooks)

| claim | number | where |
|---|---|---|
| RQ1 — the router keeps aggregate questions away from generation | **accuracy 0.95**, fabrication risk 0.10, over-abstention 0.00 (frozen 60-question gold set, 30 DE / 30 EN) | `reports/router_evaluation_report.md` |
| RQ1/RQ4 — retrieval quality, measured **and replicated** | precision@6 **0.451** (2000–2025 index) vs 0.465 (2015–2025 index); **DE ≈ 0.60 vs EN ≈ 0.17 in both**; ECHR **LAW-section hits 0.73/0.69, all other sections 0.00 in both** — the genre finding replicates across a 40 % larger corpus | `reports/retrieval_evaluation_report.md` |
| RQ2 — extraction as boundary-mover, two methods on identical gold labels | transparent rules **F1 0.507** vs local LLM (llama3.2) **F1 0.593** | `reports/llm_vs_rules_extraction.md` |
| RQ3 — calibrated field-level uncertainty | ECE **0.179 raw → 0.068 calibrated**, validated 5-fold **out-of-fold** | `reports/extraction_validation_report.md`, `figures/alienation_reliability_diagram.png` |
| RQ4 — cross-lingual generality | German queries retrieve **exclusively** from AT/CH corpora, English exclusively from ECHR; extraction validated **ECHR-English only** (stated domain of validity) | `reports/retrieval_evaluation_report.md` |

Two findings worth a discussion on their own:

1. **The genre finding — replicated.** Precision is driven by document *genre*, not
   language: AT hits ≈ 0.6–0.7, Swiss reasoning sections ≈ 0.57–0.59, and ECHR hits are
   precise *only* when they land in the Court's own assessment (LAW = 0.69 on the 2015–2025
   index, 0.73 on the 2000–2025 index; FACTS/HEADER/PROCEDURE/OPERATIVE = **0.00 on both**).
   The known "recitals problem" is thereby quantified and causally closed: ECHR's low
   precision *is* its low LAW-share (0.27 / 0.23). Two independent judgment rounds over two
   index versions — the pattern is robust.
2. **The transparency/accuracy trade-off.** The rules extractor is fully auditable but weak
   (F1 0.51, and its confidence is non-monotonic — the ~0.7 band is *less* reliable than the
   ~0.45 band); the local LLM is stronger (F1 0.59, +0.13 recall) but opaque. Calibration
   repairs the probability meaning of both; neither clears the bar for hard counts — which is
   precisely why the query layer treats a confidence threshold as **field-level abstention**
   and always reports what was excluded.

## 5. Reading order — notebooks (all in `src/`, all CPU-only)

**Act 0 — the 5-minute demo (open this first):**
0. `ask.ipynb` — the whole typology as **one executable function**: `ask_anything(question)`
   routes any question (router → bucket) and answers it only in the way its bucket allows —
   grounded generation with citations (Bucket 1), guarded NL→SQL over metadata (Bucket 2:
   local coder model, few-shot, `EXPLAIN`-validated, generated SQL printed *above* its
   result), the calibrated extraction column with abstention audit (Bucket 3 extracted), or
   an explained refusal (Bucket 3 unextracted). Seven demo questions cover all four
   behaviours; every deeper notebook is the validation behind one branch.

**Act I — corpus (skim):**
1. `master_import.ipynb` — one orchestrator, four sources, per-source stable IDs +
   provenance, new/extend run modes. *Look at:* the final verification cell (every record has
   ID + provenance + full text).
2. `data_summary.ipynb` — read-only corpus statistics.

**Act II — retrieval and knowing-when-not-to-answer (the core):**
3. `rag_echr_ris.ipynb` — the multilingual index; genre-aware retrieval + MMR; **three
   abstention layers** (aggregate router · no-hits · boilerplate-only); grounded generation
   via local Ollama. *Look at:* §11 before/after — the old top-6 was 6/6 pending-case
   boilerplate at cosine 0.88; the fix routes it out and abstains honestly when nothing
   decided remains. Then the demo: a German aggregate question correctly triggers abstention.
4. `router_evaluation.ipynb` — turns the router from design into measurement (RQ1).
   *Look at:* the failure table — the three misses are exactly the phrasings without a lexical
   trigger ("most common", "more often than"); the known limit of a pattern router, stated.
5. `retrieval_evaluation.ipynb` — frozen 24-query set, automatic diagnostics + judged
   precision@6 under a written strict criterion. *Look at:* the jurisdiction-mix table and the
   per-section precision.

**Act III — moving the boundary (Bucket 3):**
6. `echr_extraction.ipynb` — Layer 1: a transparent rules extractor for one content field,
   `alienation_alleged` (a party's *allegation*, never the court's finding), every cell with
   confidence + provenance. *Look at:* the ~40-line rule cell — the entire "model" is readable.
7. `extraction_validation.ipynb` — Layer 2, run once: the only place hand-labels (n=120,
   stratified) are read. Precision/recall/F1 + **out-of-fold isotonic calibration + ECE**.
   *Look at:* the reliability diagram — raw vs calibrated bins.
8. `echr_extraction_llm.ipynb` — the RQ2 experiment: same cases, same gold labels, local LLM
   vs the rules. *Look at:* the agreement breakdown (18 cases only the LLM gets right, 14 only
   the rules).
9. `echr_query.ipynb` — Layer 3: DuckDB over the validated table; `min_confidence` is a
   user-set **abstention threshold**; excluded cells are counted, never silently dropped.
   *Look at:* **§6c — the handoff**: the exact question the RAG notebook abstains on
   ("Wie viele Urteile betreffen die Durchsetzung des Kontaktrechts?") answered here with
   deterministic SQL (276 contact judgments, 189 violations, caveat printed). Then the
   "same question at thresholds 0.5/0.7/0.9" abstention demo, **§6b — the Bucket-2 surface**:
   a per-source metadata coverage audit that *defines* what is quantitatively answerable,
   four registered relations (`echr_meta`, `ris_meta`, `ris_normen`, `swiss_meta`), and
   metadata-only findings — the ECHR importance gradient (importance-1 cases: 67 % separate
   opinions, 23 cited cases on average; importance-4: 5 % and 0.4), **the moved boundary**
   (proceedings duration — a Bucket-3 refusal example until `introductiondate` arrived:
   admissibility decisions median 2.9 years, n=307), the Registry's kpthesaurus concept
   codes, the *Entfremdung* homonym quantified, the most-applied Rechtssätze,
   statute-reference counts — and **§6d**: the NL→SQL spot-check.
   Three measured model-behaviour findings live in this layer: a *general* 3B model
   (llama3.2) copies few-shot answers and drops filters; a *coder* 3B model
   (qwen2.5-coder) translates entities, tables and composed conditions correctly but still
   invents plausible filters on harder questions; and offering the model a `CANNOT_ANSWER`
   escape makes it refuse anything requiring composition (the lazy-escape effect) — so
   refusal is handled by deterministic nets (deny-list + `EXPLAIN` validation), never
   delegated to the model. The observed reason the citable path is reviewed SQL, not
   generated SQL.

**Act III½ — structure and transfer (topic-agnostic result families, added July 2026):**
- `citation_network.ipynb` — the ECHR **precedent network** from `scl` (top precedents:
  Hokkanen, Kutzner, Elsholz — 18/14/13 % of citing cases; median precedent age 8 years;
  precedent base *diversifying*: top-10 concentration 13 % → 6 %) and **Austrian principle
  lifecycles** from `entscheidungstexte` (median active span 30 years, max 70; 71 % of
  principles are living law, applied since 2021).
- `trends_and_variation.ipynb` — Strasbourg **speed** (median 3.5y pre-2010 → ~2.8y after,
  Protocol-14-consistent), **violation-rate structure** (Committee formations 94.9 % vs
  Chamber 62.6 % — the well-established-case-law mechanism visible in metadata), Swiss
  **cantonal practice variation** (keyword layer, caveated).
- `principle_faithfulness.ipynb` — are Rechtssätze semantic surrogates for their case-law?
  Median cosine to own applying decisions 0.896 vs 0.863 to random decisions; **26/29
  principles specifically closer to their own case-law** — small margin because family-law
  text is homogeneous (independently explains the corpus's high baseline cosines).
- `extraction_domain_shift.ipynb` — the sample-frame caveat turned into an experiment:
  40 stratified pre-2015 cases, identical protocol; measures whether the 2015–2025-fitted
  extractor and calibration transfer two decades back (see report).
- **`reusability.md`** — the transfer matrix: component × cost-to-move-to-a-new-topic, with
  measured evidence per row and the six measured limits of the generic-tool idea.

**Act IV — worked examples on the probe topic (supporting, not headline):**
10. `echr_framing_analysis.ipynb` — lexicon-based framing prevalence: the ECHR frames these
    cases as **state enforcement-failure** (45 % of judgments) and **children's-rights**
    questions (29 %), almost never psychologically (1 %). Caveated as lexicon-dependent.
11. `diachronic_analysis.ipynb` — a Bucket-3-shaped question ("how did the vocabulary
    change?") handled the honest way: frequency/keyness produce *reading shortlists*, not
    findings — and the notebook demonstrates why the naive version misleads (a "14 % rise"
    that is a denominator artefact once coverage is checked).

## 6. Why extraction replaced "improve generation" (the evidence trail)

Three successive failures, each documented in the notebooks, forced the pivot:
(1) a diachronic frequency "rise" dissolved under length normalisation — pure denominator
artefact; (2) retrieval was being won by communicated-case boilerplate — high similarity,
zero answer value; after the genre fix, (3) the survivors were FACTS recitals rather than the
Court's reasoning — the same base-rate problem one layer deeper, now quantified at
LAW-share 0.27 / non-LAW precision 0.00. The lesson generalises: **the failure modes were
never the generator — they were unfaithful selection of what to generate from.** Hence the
contribution is retrieval + extraction + calibrated abstention; generation runs (local
llama3.2, fully offline) but is deliberately not a validated claim.

## 6½. Metrics glossary — how every number in this document is computed

- **Chunk** — the retrieval unit: documents are split into ~600-word windows with 80-word
  overlap (ECHR judgments are first split by section — LAW/FACTS/…; an Austrian Rechtssatz
  is one chunk by itself). Each chunk carries jurisdiction/genre/section/date metadata and
  one embedding vector; "the index has 42,055 chunks" means 42,055 such units.
- **Router accuracy** (RQ1) — 60 hand-written questions, each labelled with its gold bucket.
  The router maps a question to *retrieval* (no aggregate trigger) or *aggregate* (trigger
  fired); gold mapping: Bucket 1 → retrieval, Buckets 2/3 → aggregate. Accuracy = share of
  the 60 where the router's route equals the gold route (57/60 = 0.95).
- **Fabrication risk** (RQ1) — of the 20 Bucket-3 questions (content aggregates), the share
  wrongly routed to retrieval: 2/20 = 0.10. These are the *dangerous* errors: an answered
  content-aggregate question means the generator states a corpus-wide claim from ~6
  passages — a fabricated statistic. **Over-abstention** is the mirror error (Bucket-1
  questions wrongly refused): 0/20 — the router errs on the safe side by design.
- **Precision@6** (RQ1/RQ4) — for each of 24 frozen queries, the top-6 retrieved chunks are
  judged relevant (1) or not (0) under a written strict criterion: relevant only if the
  chunk contains the deciding court's *own rule or reasoning* on the query's legal question;
  facts recitals, quoted statutes, party submissions, captions and operative paragraphs
  count 0 regardless of topical overlap, judged on the full chunk text. Precision@6 = mean
  of those 144 judgments — the fraction of what the system returns that is actually usable.
  Subgroup numbers (per language, per jurisdiction, per ECHR section) are the same mean over
  the subset — e.g. "AT hits ≈ 0.6–0.7" = of the retrieved chunks that came from the
  Austrian corpus, 60–70 % were judged relevant (0.70 on the 2015–2025 index, 0.61 on the
  2000–2025 index). No recall claim is made anywhere: the set of all relevant documents
  cannot be enumerated.
- **Precision / recall / F1** (RQ2) — for the binary field `alienation_alleged` against 120
  hand labels: precision = of the cases the extractor flags as "alleged", the share that
  truly are; recall = of the truly alleged cases, the share the extractor finds; F1 = their
  harmonic mean (one number balancing both). F1 0.507 means roughly: half of flags are
  wrong and half of true cases are missed — which is why the count is only ever reported
  with confidence thresholds and abstention audits.
- **ECE — Expected Calibration Error** (RQ3) — groups predictions into 5 confidence bins and
  averages |stated confidence − observed accuracy| weighted by bin size. ECE 0 = "0.8 means
  80 %" exactly; 0.179 (raw) means stated confidences were off by ~18 points on average;
  0.068 after isotonic calibration. **Out-of-fold (OOF)** = every case is scored by a
  calibration fitted without that case (5-fold), so the number is an unseen-data claim.
- **Cosine similarity** — dot product of two normalised embedding vectors (1 = identical
  direction, ~0.85+ = very similar legal text in this corpus). *Faithfulness* of a
  Rechtssatz = max cosine between the principle and any chunk of its applying decisions;
  the *margin* subtracts the same measure against random decisions (specificity).
- **In-degree** (precedent network) — number of corpus cases citing a given precedent in
  their `scl` field; "Hokkanen 18 %" = 18 % of citation-bearing cases cite it.

## 7. Limitations (stated, not discovered by others)

- **Gold labels:** n=120, single annotator, labelled in a template that displayed the
  extractor's guess (anchoring possible; 37/120 labels do overrule the extractor). A
  double-labelled subsample for inter-annotator agreement is the natural next step.
- **Corpus extension (2026-07-07):** the corpus was widened from 2015–2025 to **2000–2025**.
  The 120-label sample was stratified over the *old* corpus — metrics remain valid for those
  cases, but pre-2015 judgments are outside the sample frame. The retrieval judgments were
  re-drawn and re-judged against the new index (old measurement archived); both rounds used
  the same written strict criterion.
- **One content field.** `alienation_alleged` is a proof-of-method, not a multi-field system.
- **Domain of validity:** extraction + calibration hold for ECHR Article-8 English cases only;
  transfer to AT/CH requires re-labelling (protocol already defined).
- **Relevance judgments** for precision@6: strict written criterion, full-chunk basis, drafted
  with LLM assistance and reviewed by the author; single-annotator like the rest.
- **Router** is lexical: aggregate intent without a trigger word escapes it (measured: 2/20).
- Corpus counts describe keyword-matched collections, never litigation rates.

## 8. Discussion points

1. Is the **measured system** (typology + router + retrieval + calibrated extraction +
   abstention) the thesis contribution, or a tool for a substantive legal analysis on top?
2. Bucket-3: is the rules-vs-LLM comparison at moderate F1 an acceptable *finding* (the
   boundary moves, but not far enough for hard counts), or should a stronger extractor /
   second field be in scope?
3. What weight to give the worked examples (framing, diachronic) in the write-up?
4. Priorities for the remaining time: inter-annotator agreement vs extending extraction to
   the German corpora vs a section-aware retrieval fix (the LAW-share lever).
