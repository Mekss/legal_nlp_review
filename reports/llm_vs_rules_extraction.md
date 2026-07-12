# RQ2 experiment — rules vs local-LLM extraction of `alienation_alleged`

- identical frozen gold sample (n=120), identical threshold (0.5); LLM = `llama3.2` via local Ollama, temperature 0, CPU-only, no paid APIs.
- LLM input = all cluster-lexicon sentences with section labels (no context restriction); cases without any cluster mention short-circuit to False for both extractors.

| extractor | precision | recall | F1 | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| rules (transparent) | 0.543 | 0.475 | **0.507** | 19 | 16 | 21 | 64 |
| LLM (llama3.2) | 0.585 | 0.6 | **0.593** | 24 | 17 | 16 | 63 |

- LLM self-reported confidence: ECE raw = **0.260**, 5-fold OOF-calibrated = **0.001** (same protocol as the rules extractor's calibration).
- agreement: both right 69, LLM-only right 18, rules-only right 14, both wrong 19.

## Reading
- This is the RQ2 result: whether moving from transparent rules to a local LLM buys reliability, and how much auditability it costs (the LLM returns a verbatim evidence sentence, but its decision process is opaque).
- Both extractors share the gold sample's limitations (single annotator, anchored template — see `extraction_validation_report.md`).
- Domain of validity: ECHR Article 8 contact/alienation cases only.
