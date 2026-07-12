# ECHR extraction validation report
- labelled sample: **120** cases, gold positive rate **33.3%**

## Metadata tier — exact-match accuracy
- `outcome`: **1.000** (n=95)
- caveat: `gold_outcome` was **pre-filled from the extractor's own guess** and confirm-only during labelling, so this is a consistency check, **not an independent validation** of the outcome field.

## Content tier — alienation_alleged
- precision **0.543**, recall **0.475**, F1 **0.507** (threshold 0.5, n=120)
- confusion: TP=19 FP=16 FN=21 TN=64

## Calibration (validated out-of-fold)
- **ECE raw = 0.179**, **ECE calibrated (5-fold out-of-fold) = 0.068** — the calibrated figure is measured on rows the isotonic fit never saw, so it supports the unseen-data claim.
- raw confidence is **non-monotonic** (the ~0.7 band is less often a true allegation than the ~0.45 band); isotonic calibration flattens that region, trading ranking granularity for probability meaning.
- deployed isotonic mapping (refit on all labelled rows) persisted to `alienation_calibration.joblib`; reliability diagram `alienation_reliability_diagram.png`.

## Labelling protocol — limitations
- Labels come from a **single annotator**; the template displayed the extractor's guess and evidence sentence, so an **anchoring bias** cannot be excluded (37/120 labels do overrule the extractor). No inter-annotator agreement has been measured yet.

## Domain of validity
- Calibration holds **only within the validated domain: ECHR Article 8 contact / parental-alienation cases**. It must be **re-run** to extend to other Articles, other ECHR subject-matter, or other corpora (RIS/Swiss).
- **Sample frame:** the frozen 120-case sample was stratified over the 2015–2025 corpus (719 cases). The corpus was extended to 2000–2025 (1,116 cases) on 2026-07-07; the metrics above still validate the extractor on those 120 cases, but pre-2015 judgments (older HUDOC formatting) are **outside the sample frame** — re-stratifying and re-labelling over the extended corpus is the clean fix.
