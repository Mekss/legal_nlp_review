# Reusability — what it costs to point this tool at a new topic

The system was always meant as a **generic instrument**: same four sources, same pipeline,
same question typology — the topic is a parameter (`KEYWORDS` in `master_import.ipynb`).
Parental alienation is the probe load, not the product. This document is the contribution
that framing implies: a component-by-component account of **what transfers unchanged, what
needs re-running, and what needs new human input** — with the measured evidence for each
claim. The proof-of-concept is `src/ask.ipynb` (one entry point, four answer behaviours)
plus the reports it rests on.

## Transfer matrix

| component | topic input | cost to move to a new topic | evidence |
|---|---|---|---|
| **Import** (`master_import.ipynb`) | the `KEYWORDS` dict — nothing else | edit one dict; re-run | same code ran the 2015–2025 and 2000–2025 imports unchanged; per-source stable IDs + provenance survive both |
| **Corpus curation** (noise filters) | topic-specific homonym/noise audit | **verify a 40-row auto-ranked shortlist** (`corpus_audit.ipynb`): metadata structure scan + embedding outlier ranking flag candidates; the human only marks YES/NO — blind validation: 100 % of this topic's known noise in the bottom decile of the ranking, plus previously missed noise families surfaced | measured examples: *Entfremdung* = criminal misappropriation (17 records excluded via senate codes); "estranged wife" = separated-spouse false positive; Swiss court annual reports flooding top-k (14 excluded) — the *pattern* (audit → printed exclusion) generalises, the filters themselves do not |
| **Chunk → embed → index** | none | CPU hours only (measured: ~21k chunks ≈ 5 h on a 2015 laptop; per-chunk-id cache makes re-runs incremental) | two full corpus versions built on the same cache |
| **Retrieval** (genre routing, MMR, section tags) | none — genre/section mechanics are *source-structural*, not topical | zero | genre fix + precision pattern replicated across two index versions |
| **Router** (Bucket 1 vs 2∪3) | none — keys on question *form* ("how many", "wie viele") | zero; gold set's topic nouns swappable for re-measurement | accuracy 0.95, fabrication risk 0.10 (n=60, EN+DE) |
| **Bucket-2 layer** (metadata relations, canned SQL, NL→SQL) | 1–2 topic-flavoured few-shot examples; canned queries that mention topic columns | minutes | metadata relations (respondent, canton, formation, duration, citations) exist for *any* corpus from these sources; coverage audit prints the answerable surface per corpus |
| **Citation / lifecycle / trends analyses** (new) | none | zero — run unchanged | `citation_network.ipynb`, `trends_and_variation.ipynb`, `principle_faithfulness.ipynb` consume only importer metadata + cached vectors |
| **Theme layer** (`echr_theme_classify.py`) | keyword lexicons | ~an hour to draft; **stays unvalidated by design** (stated caveat) | lexicons are one editable dict |
| **Bucket-3 extraction field** | rules/prompt for the field **and** a frozen labelled sample (~120, stratified) **and** a calibration run | **the expensive step: ~1 day of labelling per field per domain** | the alienation field end-to-end: rules F1 0.507, LLM F1 0.593, ECE 0.179→0.068 (5-fold OOF) |
| **Calibration** | bound to field × domain | re-freeze + re-run per new domain (protocol written) | **temporal transfer holds**: 2015–25-fitted isotonic on 2000–14 gold → ECE 0.084 (vs 0.068 in-domain); rules F1 0.60, LLM F1 0.68 on the transfer sample — the 'label once' claim extends two decades back |
| **Deny-list of unextracted concepts** | small topic-specific list | minutes; failure direction is refusal, never fabrication | duration left the list when `introductiondate` arrived — the Bucket 2/3 boundary is data, and it moved |
| **Framing / diachronic analyses** | concept-cluster + lexicon config cells | ~an hour; outputs are *reading shortlists*, not findings, regardless of topic | config-driven by construction |

## What limits the idea (measured, not hypothesised)

1. **Recall at import is unknowable.** The corpus is whatever the keyword search returns;
   no component downstream can repair missing documents. Inherent to the design; stated
   everywhere counts are reported ("describes the keyword-matched corpus, never rates").
2. **Every topic has homonyms.** Three were found and excluded *for this topic*; a new topic
   needs its own audit. The tool makes the audit cheap (printed counts, senate/court
   metadata) but cannot skip it.
3. **Bucket 3 is where generality ends.** Content aggregates cost a labelled sample per
   field per domain — measured at F1 ≈ 0.5–0.6 for one field even after that investment.
   The honest generic behaviour is the refusal branch, which transfers for free.
4. **Section parsing is source-format-bound.** ECHR heading regexes, RIS principle layout,
   Swiss `content` field — each source needed one format discovery; parse rates are printed
   so degradation is visible, not silent.
5. **Small local models translate, they don't judge.** Measured: a general 3B copies
   few-shot answers and drops filters; a coder 3B maps entities/tables correctly but invents
   plausible filters on hard questions; offered an escape hatch, it over-refuses
   (lazy-escape effect). Consequence baked in: models never refuse and never get cited —
   deterministic nets refuse, printed SQL is the trust boundary.
6. **Evaluation itself has a per-topic cost.** Retrieval precision needs ~144 judged rows
   per index (protocol + criterion written; two rounds done); router and extraction gold
   sets are reusable in form but their content words are topical.

## The one-sentence version for the meeting

> The pipeline from import to metadata analytics to retrieval-with-abstention is
> **topic-agnostic and demonstrated twice over**; the cost frontier sits exactly at
> content extraction (per-field labelling) and corpus curation (per-topic homonym audit) —
> and the system is built so that everything beyond that frontier **refuses rather than
> degrades**.
