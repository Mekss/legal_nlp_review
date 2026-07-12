"""Theme classification layer for the ECHR corpus.

Enriches the validated extraction table with transparent, keyword-based family-law
THEME tags so the whole 719-case corpus (not just the ~35 alienation allegations) can be
sliced by SQL. Themes are multi-label (a case can be about both contact and alienation);
`primary_theme` is a single specificity-ranked label for clean GROUP BY.

Honest by design: this is high-recall keyword tagging over full judgment text, NOT a validated
classifier — precision is approximate and stated as a caveat wherever the numbers are used.
The precise, calibrated `alienation_alleged` flag (a genuine party allegation) stays separate
from the broad `is_alienation` topic flag.

Inputs : data/echr_parental_alienation.json  (full_text + matched_keywords, 719 cases)
         data/echr_extracted.parquet         (validated metadata: state/genre/outcome/date/...)
Output : data/echr_themes.parquet
"""
import json
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_JSON = DATA_DIR / "echr_parental_alienation.json"
META_PARQUET = DATA_DIR / "echr_extracted.parquet"
OUT_PARQUET = DATA_DIR / "echr_themes.parquet"

# Transparent keyword rules, matched on lowercased full_text. Patterns are deliberately
# specific (e.g. Hague-only abduction terms) to limit incidental false hits.
THEMES = {
    "abduction_hague":   [r"hague convention", r"wrongful (removal|retention)", r"child abduction",
                          r"international abduction", r"unlawful(ly)? (removal|retention|removed|retained)"],
    "adoption":          [r"\badoption\b", r"freeing for adoption", r"adoptive (parent|famil)", r"adopt the child"],
    "care_removal":      [r"taken into (public )?care", r"care order", r"foster (care|home|parent|famil)",
                          r"placed (in|into) (public |institutional )?care", r"child protection",
                          r"emergency (care|placement)", r"public care"],
    "alienation":        [r"parental alienation", r"alienat", r"turn(ed|ing)? the child(ren)? against",
                          r"manipulat", r"estrange", r"set the child(ren)? against"],
    "domestic_violence": [r"domestic violence", r"ill-treatment", r"physical(ly)? abus", r"sexual(ly)? abus",
                          r"violence against", r"battered"],
    "custody_residence": [r"\bcustody\b", r"residence (order|arrangement)", r"parental (authority|responsibilit)",
                          r"sole custody", r"joint custody"],
    "contact_access":    [r"contact rights", r"access rights", r"visiting rights", r"contact order",
                          r"enforcement of .{0,25}contact", r"right to contact", r"maintain contact",
                          r"contact (with|between)"],
    "length_procedural": [r"length of the proceedings", r"reasonable time", r"excessive length", r"undue delay"],
}

# Specificity order: distinct legal procedures win over broad family-law language.
SPECIFICITY = ["abduction_hague", "alienation", "adoption", "care_removal", "domestic_violence",
               "custody_residence", "contact_access", "length_procedural"]

# Coarse grouping for headline aggregates.
THEME_GROUP = {
    "care_removal": "public_protection", "adoption": "public_protection",
    "alienation": "private_dispute", "custody_residence": "private_dispute",
    "contact_access": "private_dispute", "abduction_hague": "private_dispute",
    "domestic_violence": "cross_cutting", "length_procedural": "cross_cutting", "other": "cross_cutting",
}

MIN_HITS = 2  # a theme must be mentioned >=2x to flag (drops incidental single mentions)

COMPILED = {th: [re.compile(p) for p in pats] for th, pats in THEMES.items()}


def classify(full_text):
    """Return (flags dict, primary_theme) for one judgment's full text."""
    t = (full_text or "").lower()
    counts = {th: sum(len(p.findall(t)) for p in pats) for th, pats in COMPILED.items()}
    flags = {th: counts[th] >= MIN_HITS for th in THEMES}
    primary = next((th for th in SPECIFICITY if flags[th]), "other")
    return flags, primary


def build():
    raw = json.loads(RAW_JSON.read_text())
    meta = pd.read_parquet(META_PARQUET)

    rows = []
    for case in raw:
        flags, primary = classify(case.get("full_text", ""))
        row = {"id": case.get("itemid"),
               "primary_theme": primary,
               "theme_group": THEME_GROUP[primary],
               "matched_keywords": ";".join(case.get("matched_keywords", [])),
               "text_length": case.get("text_length", 0)}
        row.update({f"is_{th}": flags[th] for th in THEMES})
        rows.append(row)
    themes = pd.DataFrame(rows)

    # Join theme columns onto the validated metadata (inner: keep cases present in both).
    out = meta.merge(themes, on="id", how="left")
    out["primary_theme"] = out["primary_theme"].fillna("other")
    out["theme_group"] = out["theme_group"].fillna("cross_cutting")
    for th in THEMES:
        out[f"is_{th}"] = out[f"is_{th}"].fillna(False)

    out.to_parquet(OUT_PARQUET, index=False)
    print(f"wrote {OUT_PARQUET}  ({len(out)} rows, {out['primary_theme'].nunique()} themes)")
    print("\nprimary_theme distribution:")
    print(out["primary_theme"].value_counts().to_string())
    print("\ntheme_group distribution:")
    print(out["theme_group"].value_counts().to_string())
    return out


if __name__ == "__main__":
    build()
