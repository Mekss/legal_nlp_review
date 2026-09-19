"""Re-deploy `alienation_alleged` as a first-class queryable content field.

`alienation_alleged` predates the field factory: it was built and validated in
`echr_extraction.ipynb` (transparent rules + attribution + negation, no transformers) and
reached the dispatcher through a hand-written `_h_alienation` branch, which was retired. The
column itself was never the problem — it is the most thoroughly validated content field in the
project (120 reviewed labels, an out-of-fold calibration, an rules-vs-LLM comparison). What it
lacked was the *deployment contract* every factory field uses:

    data/field_<name>_deployed.parquet   id, <name>, conf_raw, conf_cal, evidence, provenance
    data/field_<name>_meta.json          definition, lexicon, threshold, question_terms, validation

`ask.ipynb` discovers any field that has those two files, registers it in DuckDB, writes it
into the NL->SQL schema and routes questions to it — no code changes. This script writes them
from the existing validated extraction rather than re-extracting anything, so nothing about
the column's provenance or its measured quality changes.

One thing IS recomputed: the calibration target. `echr_extracted.alienation_conf_cal` is
calibrated P(allegation) — the quantity `echr_query.ipynb` thresholds. The deployed contract
means something else by `conf_cal`: P(this drafted cell is correct), which is what makes a
threshold comparable across fields (`field_deploy.ipynb`, "the target is 'this drafted cell is
correct'"). Fitting the deployed meaning here is what lets one threshold be read the same way
on all five fields. The original column keeps its own calibration, untouched.

Run:  .venv/bin/python src/deploy_alienation_field.py
"""

import json
from pathlib import Path

import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import precision_recall_fscore_support

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
DEPLOY_DATE = "2026-09-18"
FIELD = "alienation_alleged"
THRESHOLD = 0.7                      # the same bar every other deployed field is read at

EXTRACTED = DATA / "echr_extracted.parquet"
LABELS = DATA / "echr_labeled_sample.csv"
OUT_PARQ = DATA / f"field_{FIELD}_deployed.parquet"
OUT_META = DATA / f"field_{FIELD}_meta.json"

# The definition as confirmed in echr_extraction.ipynb section 5 -- the ALLEGATION, never the
# holding. Copied verbatim in substance so the sidecar and the notebook cannot disagree.
DEFINITION = (
    "alienation_alleged = TRUE when a party -- typically the applicant -- asserts that the "
    "other parent alienated the child, turned or set the child against them, manipulated the "
    "child or poisoned the child's mind, as recorded in the facts or the complaints. It is the "
    "ALLEGATION, not the holding: whether the Court accepted it is irrelevant to this field. "
    "It is FALSE where the alienation vocabulary appears only in court or third-party "
    "narration with no party attribution, only in quoted law, a dissent or the operative "
    "provisions, or only inside a negated or rejected statement."
)

# the extractor's own cluster, written out as readable surface forms
LEXICON = [
    "alienated the child",
    "estrangement",
    "manipulating the child",
    "parental alienation",
    "parental alienation syndrome",
    "poisoning the child's mind",
    "set the child against",
    "turned the child against",
]

# what a question has to say for the router to pick this field
QUESTION_TERMS = [
    "parental alienation",
    "alienation alleged",
    "alienation allegation",
    "allegation of alienation",
    "alienation cases",
    "estrangement",
    "Entfremdung",
]


def main():
    df = pd.read_parquet(EXTRACTED)
    lab = pd.read_csv(LABELS)

    # ---- the gate: the extractor measured against the reviewed labels ---------------------
    lab["gold"] = pd.to_numeric(lab["gold_alienation_alleged"], errors="coerce")
    lab = lab[lab.gold.notna()].copy()
    lab["gold"] = lab.gold.astype(int)
    draft = lab.extractor_guess.astype(bool).astype(int)
    correct = lab.gold == draft
    flips = int((~correct).sum())
    p, r, f1, _ = precision_recall_fscore_support(lab.gold, draft, average="binary",
                                                  zero_division=0)
    print(f"GATE: {len(lab)} reviewed labels | flip rate {flips}/{len(lab)} "
          f"({flips / len(lab) * 100:.0f}%) | rules F1 vs gold {f1:.3f} "
          f"(P {p:.3f} / R {r:.3f})")
    if flips == 0:
        print("!! WARNING: zero flips -- labels may be rubber-stamped; validation is weak.")

    # ---- deployment calibration: P(this drafted cell is correct) --------------------------
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(lab.alienation_conf.to_numpy(float), correct.to_numpy().astype(float))
    print(f"deployment isotonic fitted on {len(lab)} reviewed labels "
          f"(target: the drafted cell is correct)")

    # ---- the deployed column -------------------------------------------------------------
    dep = pd.DataFrame({
        "id": df.id,
        FIELD: df[FIELD].astype(bool),
        "conf_raw": df.alienation_conf.astype(float),
        "conf_cal": iso.predict(df.alienation_conf.to_numpy(float)),
        "evidence": df.alienation_evidence,
        # the rules extractor records WHY it fired (section, mention count, attribution,
        # negation); keep it, it is the auditability this field was built for
        "provenance": ["rules:echr_extraction.ipynb;"
                       + json.loads(pv).get(FIELD, "unrecorded") for pv in df.provenance],
    })
    dep.to_parquet(OUT_PARQ, index=False)
    pos = int(dep[FIELD].sum())
    conf_n = int((dep[FIELD] & (dep.conf_cal >= THRESHOLD)).sum())
    print(f"wrote {OUT_PARQ.name}: {len(dep)} rows | positive: {pos} "
          f"| confident (cal>={THRESHOLD}): {conf_n} | abstained: {pos - conf_n}")

    meta = {
        "field": FIELD,
        "kind": "boolean",
        "unit": None,
        "definition": DEFINITION,
        "lexicon": LEXICON,
        "threshold": THRESHOLD,
        "question_terms": QUESTION_TERMS,
        "corpus": "echr_parental_alienation.json (ECHR-EN; domain of validity)",
        "validation": {
            "n_labels": int(len(lab)),
            "flip_rate": f"{flips}/{len(lab)}",
            "f1": round(float(f1), 3),
            "precision": round(float(p), 3),
            "recall": round(float(r), 3),
        },
        "labels_file": LABELS.name,
        # not an LLM field: say so, rather than let a generic caveat call it one
        "extractor": "transparent rules (lexicon + party attribution + negation)",
        "model": None,
        "labels_provenance": (
            "single annotator (the researcher), frozen 120-case sample; the labelling template "
            "displayed the extractor's guess and evidence sentence, so anchoring bias cannot be "
            "excluded and 37/120 labels overrule the extractor -- see "
            "reports/extraction_validation_report.md"),
        "notes": (
            "Re-deployed from echr_extraction.ipynb by src/deploy_alienation_field.py; the "
            "column is not re-extracted. conf_cal here is P(cell is correct), the deployed "
            "contract's meaning, refit on the same 120 labels; echr_extracted.alienation_conf_cal "
            "keeps its own P(allegation) calibration for echr_query.ipynb. A local-LLM variant "
            "of this field scored F1 0.593 against the same gold sample "
            "(reports/llm_vs_rules_extraction.md) but was only ever run over those 120 cases, "
            "so the corpus-wide column is the rules one."),
    }
    OUT_META.write_text(json.dumps(meta, indent=2))
    print(f"wrote {OUT_META.name} -- ask.ipynb discovers the field through this sidecar")

    # ---- the per-field report every other deployed field has ------------------------------
    report = REPORTS / f"field_{FIELD}_report.md"
    report.write_text(
        f"# Deployed field report: `{FIELD}` (boolean)\n\n"
        f"- definition: {DEFINITION}\n"
        f"- extractor: transparent rules (lexicon cluster + party attribution + negation), "
        f"`echr_extraction.ipynb` section 5 -- no transformers, the whole model is readable\n"
        f"- rules drafts vs gold: P={p:.3f} R={r:.3f} F1={f1:.3f}\n"
        f"- sample: {len(lab)} reviewed labels (stratified over the 2015-2025 corpus), "
        f"headline: F1 {f1:.3f}\n"
        f"- **flip rate {flips}/{len(lab)}** (human vs drafts; low = anchoring warning)\n"
        f"- calibration: refit here on the deployed target (the drafted cell is correct); the "
        f"out-of-fold validation of this extractor's confidence is ECE 0.179 raw -> 0.068 "
        f"calibrated, reported in `extraction_validation_report.md` against the other target "
        f"(P(allegation)), which `echr_query.ipynb` still uses\n"
        f"- coverage at the deployed threshold {THRESHOLD}: {conf_n} confident positives, "
        f"{pos - conf_n} predicted positives abstained (surfaced, never dropped), "
        f"{len(dep)} cases in the column\n"
        f"- alternative extractor: local LLM (llama3.2) scored F1 0.593 on the same gold "
        f"sample (`llm_vs_rules_extraction.md`) but was only ever run over those 120 cases, "
        f"so the corpus-wide column is the rules one\n"
        f"- protocol: single annotator, template displayed the extractor's guess and evidence "
        f"sentence (anchoring caveat, as with all gold sets in this project); domain of "
        f"validity: ECHR Article-8 English cases only.\n\n"
        f"## Why this field is deployed rather than hand-wired\n"
        f"It reached the dispatcher through a bespoke `_h_alienation` branch until "
        f"{DEPLOY_DATE}. That branch ignored every scope filter a question named, so "
        f"*\"alienation cases against Romania\"* silently counted the whole corpus. Shipped "
        f"through the standard two-file contract it gets respondent/year/theme scoping, "
        f"conjunctions with the other deployed fields, and its own calibrated threshold -- "
        f"and the router reaches it through `_match_deployed_fields`, like every other field.\n",
        encoding="utf-8")
    print(f"wrote {report.name}")


if __name__ == "__main__":
    main()
