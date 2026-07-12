# Extraction domain-shift report (2000-2014 transfer test)

- frozen pre-2015 sample: **40** cases (stratified by extractor confidence), gold positive rate **52%**. Protocol identical to the 2015-2025 sample (single annotator, LLM-drafted, reviewed; anchoring caveat applies).

| leg | 2015-2025 (reference) | 2000-2014 (transfer) |
|---|---|---|
| rules F1 | 0.507 | **0.6** (P 0.632 / R 0.571) |
| LLM (llama3.2) F1 | 0.593 | **0.683** (P 0.7 / R 0.667) |
| ECE raw | 0.179 | **0.179** |
| ECE calibrated | 0.068 (in-domain OOF) | **0.084** (true out-of-domain: isotonic fitted on 2015-2025 only) |

## Reading
- This is the reusability question in miniature: what does moving the validated component to a new (time-)domain cost? Comparable F1/ECE = the 'label once' claim extends two decades back; degradation = temporal domain shift, quantified rather than assumed.
- Small n (40) -> wide confidence intervals; this is a transfer *check*, not a re-validation.
