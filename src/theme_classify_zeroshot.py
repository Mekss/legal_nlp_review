"""Portable zero-shot theme classifier — generic engine + external spec, no hardcoded lexicons.

A theme is defined by a NAME + a natural-language DESCRIPTION + a few SEED phrases (data/
theme_spec.json). Classification is cosine similarity between each case's passage embeddings
(already cached in the multilingual-e5 index, all sources) and the theme prototype embedding.
Because e5 is multilingual, ONE English spec classifies EN/DE/FR/IT alike — the German Swiss/
RIS corpora are tagged with the same spec, no per-language patterns.

Portable by construction:
  * new theme      = add a block to theme_spec.json (name/describe/seeds/group)
  * new corpus     = its chunks are already in EMB_MATRIX; nothing to change
  * new language   = nothing to change (e5 is multilingual)
  * new DOMAIN     = replace theme_spec.json; engine code is untouched

Honest framing (same as the regex themes): high-recall approximate tags, NOT a validated
classifier. Threshold tau is auto-tuned per theme against the ECHR regex themes as SILVER
labels (no hand-labels), then transferred cross-lingually; coherence is reported, not assumed.

Boots the deployed pipeline cells (embedder, chunks, EMB_MATRIX) the same way ask_web does.
Run (from src/):  ../.venv/bin/python theme_classify_zeroshot.py
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
REPORTS = HERE.parent / "reports"
SPEC_PATH = DATA / "theme_spec.json"
OUT = DATA / "themes_zeroshot.parquet"

# ---- default spec: English descriptions + seeds; groups. Portable/editable, not code. ----
DEFAULT_SPEC = {
    "abduction_hague": {"group": "private_dispute",
        "describe": "international child abduction and wrongful removal or retention of a child across borders under the Hague Convention",
        "seeds": ["Hague Convention child abduction", "wrongful removal or retention", "return of the child", "internationale Kindesentführung", "widerrechtliches Verbringen"]},
    "adoption": {"group": "public_protection",
        "describe": "adoption of a child, including freeing a child for adoption and adoptive parents",
        "seeds": ["adoption of the child", "adoptive parents", "freeing for adoption", "Adoption", "Annahme an Kindes statt"]},
    "care_removal": {"group": "public_protection",
        "describe": "a child taken into public care, foster placement, or child-protection removal from the parents",
        "seeds": ["taken into public care", "foster care placement", "care order", "child protection", "Fremdplatzierung", "Obhutsentzug", "Kindesschutz"]},
    "alienation": {"group": "private_dispute",
        "describe": "one parent turning or manipulating the child against the other parent; parental alienation and estrangement",
        "seeds": ["parental alienation", "turning the child against the other parent", "manipulation of the child", "Eltern-Kind-Entfremdung", "Loyalitätskonflikt"]},
    "domestic_violence": {"group": "cross_cutting",
        "describe": "domestic violence, ill-treatment, or physical or sexual abuse within the family",
        "seeds": ["domestic violence", "ill-treatment", "physical or sexual abuse", "häusliche Gewalt", "Misshandlung"]},
    "custody_residence": {"group": "private_dispute",
        "describe": "custody, parental authority or responsibility, and with which parent the child resides",
        "seeds": ["custody of the child", "parental authority", "residence of the child", "Sorgerecht", "Obsorge", "Obhut", "elterliche Sorge"]},
    "contact_access": {"group": "private_dispute",
        "describe": "a parent's right of contact, access or visitation with their child, and its enforcement",
        "seeds": ["contact rights", "access and visiting rights", "enforcement of contact", "Umgangsrecht", "Besuchsrecht", "persönlicher Verkehr"]},
    "length_procedural": {"group": "cross_cutting",
        "describe": "the excessive length of the proceedings and failure to decide within a reasonable time",
        "seeds": ["length of the proceedings", "reasonable time requirement", "undue delay", "überlange Verfahrensdauer", "angemessene Frist"]},
}


def load_spec():
    if not SPEC_PATH.exists():
        SPEC_PATH.write_text(json.dumps(DEFAULT_SPEC, ensure_ascii=False, indent=1))
        print(f"wrote default spec -> {SPEC_PATH.name} (edit this, not the code)")
    return json.loads(SPEC_PATH.read_text())


def boot():
    """Exec ask.ipynb's loader cell -> pipeline in globals (embed_query, chunks, EMB_MATRIX)."""
    os.chdir(HERE)
    nb = json.loads((HERE / "ask.ipynb").read_text())
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "RAG_NB   = Path" in "".join(c["source"]):
            exec("".join(c["source"]), globals())
            break
    for need in ("embed_query", "chunks", "EMB_MATRIX"):
        assert need in globals(), f"{need} missing after boot"
    assert EMB_MATRIX.shape[0] == len(chunks), "matrix/chunks misaligned"


def theme_prototypes(spec):
    names = list(spec)
    vecs = []
    for th in names:
        parts = [spec[th]["describe"]] + spec[th].get("seeds", [])
        v = np.vstack([embed_query(p) for p in parts]).mean(0)   # embed_query -> (1,768)
        vecs.append(v / (np.linalg.norm(v) + 1e-9))
    return names, np.vstack(vecs).astype("float32")             # (T,768), unit rows


def case_scores(P):
    """Max cosine over each case's passages -> (cases_df, score_matrix aligned to it)."""
    sims = EMB_MATRIX @ P.T                                     # (Nchunks, T), both unit-norm
    key = [f"{c['source']}:{c['doc_id']}" for c in chunks]
    df = pd.DataFrame(sims)
    df["key"] = key
    g = df.groupby("key", sort=False).max()                    # theme present if ANY passage matches
    meta = {f"{c['source']}:{c['doc_id']}": (c["doc_id"], c["source"], c["jurisdiction"]) for c in chunks}
    cases = pd.DataFrame([meta[k] for k in g.index], columns=["id", "source", "jurisdiction"])
    return cases, g.to_numpy()


def tune_tau(names, scores, cases):
    """Auto-tune tau per theme on ECHR regex themes as SILVER labels (no hand-labels)."""
    silver = pd.read_parquet(DATA / "echr_themes.parquet")[["id"] + [f"is_{n}" for n in names]]
    ech = cases[cases.source == "echr"].reset_index(drop=True)
    S = scores[(cases.source == "echr").to_numpy()]
    m = ech.merge(silver, on="id", how="inner")
    idx = ech.index[ech.id.isin(m.id)].to_numpy()
    S = scores[(cases.source == "echr").to_numpy()][np.isin(ech.id.to_numpy(), m.id.to_numpy())]
    taus, f1s = {}, {}
    grid = np.arange(0.74, 0.885, 0.005)
    for j, n in enumerate(names):
        y = m[f"is_{n}"].to_numpy().astype(int)
        best_t, best_f = 0.82, -1
        for t in grid:
            yhat = (S[:, j] >= t).astype(int)
            tp = int(((yhat == 1) & (y == 1)).sum()); fp = int(((yhat == 1) & (y == 0)).sum()); fn = int(((yhat == 0) & (y == 1)).sum())
            f = tp / (tp + 0.5 * (fp + fn)) if (tp + fp + fn) else 0.0
            if f > best_f:
                best_f, best_t = f, float(t)
        taus[n], f1s[n] = round(best_t, 3), round(best_f, 3)
    return taus, f1s


def main():
    spec = load_spec()
    print("booting pipeline (cached embeddings, no re-embed)…")
    boot()
    names, P = theme_prototypes(spec)
    print(f"themes: {names}\nchunks: {len(chunks)} | matrix {EMB_MATRIX.shape}")
    cases, scores = case_scores(P)
    print(f"cases scored: {len(cases)}  by source {cases.source.value_counts().to_dict()}")

    taus, f1s = tune_tau(names, scores, cases)
    print("\nauto-tuned tau (silver=ECHR regex themes) | agreement F1:")
    for n in names:
        print(f"  {n:18s} tau={taus[n]:.3f}  F1={f1s[n]:.3f}")

    tau_vec = np.array([taus[n] for n in names])
    flags = scores >= tau_vec
    group = {n: spec[n]["group"] for n in names}
    # primary = highest-scoring FLAGGED theme; else 'other'
    masked = np.where(flags, scores, -1.0)
    primary_idx = masked.argmax(1)
    primary = [names[i] if flags[r, i] else "other" for r, i in enumerate(primary_idx)]
    out = cases.copy()
    out["primary_theme_zs"] = primary
    out["theme_group_zs"] = [group.get(p, "cross_cutting") for p in primary]
    for j, n in enumerate(names):
        out[f"zs_is_{n}"] = flags[:, j]
        out[f"zs_score_{n}"] = scores[:, j].round(4)
    out.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT.name} ({len(out)} rows, all sources)")

    print("\nprimary_theme_zs by source (share):")
    print(pd.crosstab(out.primary_theme_zs, out.source, normalize="columns").round(3).to_string())

    # coherence: zero-shot alienation vs the VALIDATED alienation flag (ECHR only)
    val = pd.read_parquet(DATA / "echr_themes.parquet")[["id", "alienation_alleged"]]
    c = out[out.source == "echr"].merge(val, on="id", how="inner")
    if len(c):
        a, b = c.zs_is_alienation.astype(int), c.alienation_alleged.astype(int)
        tp = int(((a == 1) & (b == 1)).sum()); fp = int(((a == 1) & (b == 0)).sum()); fn = int(((a == 0) & (b == 1)).sum())
        rec = tp / (tp + fn) if (tp + fn) else 0
        print(f"\ncoherence: zero-shot is_alienation recovers {tp}/{tp+fn} validated allegations "
              f"(recall {rec:.2f}); {fp} extra flagged (broad topic vs precise allegation — expected).")

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "themes_zeroshot.json").write_text(json.dumps(
        {"generated": pd.Timestamp.now().isoformat(timespec="seconds"),
         "n_cases": len(out), "by_source": out.source.value_counts().to_dict(),
         "tau": taus, "silver_f1": f1s, "spec_themes": names,
         "note": "Zero-shot multilingual-e5 theme tags; portable spec (theme_spec.json); "
                 "high-recall approximate, tau auto-tuned on ECHR regex silver labels."}, indent=1))
    print("saved report -> reports/themes_zeroshot.json")


if __name__ == "__main__":
    main()
