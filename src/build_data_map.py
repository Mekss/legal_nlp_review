"""Rebuild src/data_map.html -- the interactive map of what the corpus can answer.

Run:  cd src && ../.venv/bin/python build_data_map.py

The page itself (layout, physics, panel) is hand-written and stays as it is; this script only
rewrites the JSON block inside `<script id="data">`. Every table, column and count is read from
the relations the live pipeline queries, built by the pipeline's own code: the ECHR scope view,
its dimensions and the deployed fields come from scope_selftest.py (which lifts them out of
ask.ipynb), the cross-source tables from ask.ipynb's metadata cell. A new deployed field, a new
HUDOC column or a reloaded corpus shows up on the next run with nothing added here. What IS
written here: which Bucket-2 columns are worth showing, the example questions, and the prose.
"""
import contextlib, io, json, re
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "data_map.html"
TOP = 8                                   # values shown per field

# the scope view, _DIMS, deployed fields -- exactly what the shipped resolver sees
with contextlib.redirect_stdout(io.StringIO()):
    import scope_selftest as st
con, DATA = st.con, st.DATA


def ask_cell(marker):
    for c in json.load(open(HERE / "ask.ipynb"))["cells"]:
        if c["cell_type"] == "code" and marker in "".join(c["source"]):
            return "".join(c["source"])
    raise SystemExit(f"no cell with {marker!r} in ask.ipynb")


# swiss_meta / ris_meta / keyword_hits / case_themes: ask.ipynb's own metadata cell
ns = {"DATA_DIR": DATA, "df": st.echr, "con": con, "SCHEMA": "", "FEW_SHOT": []}
with contextlib.redirect_stdout(io.StringIO()):
    exec(ask_cell("con.register(\"swiss_meta\""), ns)
case_themes = ns["case_themes"]

# Bucket 4's date range, read from the notebook rather than restated
DIA_RANGE = eval(re.search(r"DIA_RANGE = (\([^)]*\))", ask_cell("BUCKET 4 -- diachronic")).group(1))

# Derived columns -- computed by the pipeline (rules, themes, calibration), not source
# metadata; the value registry labels these tables "(derived)". A column that table merely
# carries over from HUDOC (importance, matched_keywords, ...) is source metadata, not derived.
# Their coverage is shown, their value distribution is not.
DERIVED = set(st.echr.columns) - {k for r in st._echr_raw for k in r}


# ---- profiling ---------------------------------------------------------------------------
def _atoms(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    if isinstance(v, (list, tuple)) or hasattr(v, "tolist"):
        return [str(x) for x in list(v)]
    return [a.strip() for a in str(v).split(";") if a.strip()]


def _num(x):
    """1574 -> '1,574', a year stays '2025', a calibrated 0.1363... -> '0.136'."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or pd.isna(x):
        return str(x)
    if float(x).is_integer():
        return f"{x:,.0f}" if abs(x) >= 10000 else f"{x:.0f}"
    return f"{x:.3g}"


def profile(table, col, where="TRUE", multi=False):
    """coverage %, distinct count, top values -- straight from DuckDB."""
    s = con.execute(f'SELECT "{col}" FROM {table} WHERE {where}').df()[col]
    n = len(s)
    filled = s.dropna()
    if multi:
        counts = pd.Series([a for v in filled for a in _atoms(v)]).value_counts()
    elif pd.api.types.is_bool_dtype(filled) or set(filled.unique()) <= {True, False}:
        counts = filled.map({True: "yes", False: "no"}).value_counts()
    elif pd.api.types.is_numeric_dtype(filled) and filled.nunique() > 12:
        span = f"{_num(filled.min())}–{_num(filled.max())}"
        return {"coverage": round(100 * len(filled) / n) if n else 0,
                "n_distinct": int(filled.nunique()), "note": f"range {span}",
                "values": [[span, int(len(filled))]]}
    else:
        counts = filled.map(_num).value_counts()
    return {"coverage": round(100 * len(filled) / n) if n else 0,
            "n_distinct": int(len(counts)),
            "values": [[k, int(v)] for k, v in counts.head(TOP).items()]}


def _no_values(p):
    p["values"] = []
    p.pop("n_distinct", None)
    p["note"] = "derived column — distribution not shown"
    return p


def field(fid, label, table, col, example, derived=False, **kw):
    note = kw.pop("note", "")
    p = profile(table, col, **kw)
    if derived:
        _no_values(p)
    note = " · ".join(x for x in (p.pop("note", ""), note) if x)
    return {"id": fid, "label": label, "kind": "field", "example": example, "note": note, **p}


def n(sql):
    return con.execute(sql).fetchone()[0]


# ---- Bucket 1: sources -------------------------------------------------------------------
genre = dict(con.execute("SELECT genre, COUNT(*) FROM echr GROUP BY 1").fetchall())
ris_types = dict(con.execute("SELECT dokumenttyp, COUNT(*) FROM ris_meta GROUP BY 1").fetchall())
in_set = dict(case_themes.groupby("source").size()) if case_themes is not None else {}
n_echr, n_ris, n_swiss = n("SELECT COUNT(*) FROM echr"), n("SELECT COUNT(*) FROM ris_meta"), \
    n("SELECT COUNT(*) FROM swiss_meta")

b1 = {"id": "b1", "label": "Bucket 1 · grounded retrieval", "bucket": "b1",
      "desc": "Open questions answered from retrieved passages with citations, or an abstention. "
              "Any topic the corpora cover.",
      "example": "When can custody be transferred because of alienating behaviour?",
      "children": [
          {"id": "src_echr", "label": "ECHR", "kind": "source", "count": n_echr,
           "note": f"EN · {genre.get('merits', 0):,} judgments / "
                   f"{genre.get('admissibility', 0):,} decisions / "
                   f"{genre.get('communicated', 0):,} communicated",
           "desc": "European Court of Human Rights, Article-8 family-life case law.",
           "example": "What does the Court require before returning an abducted child?"},
          {"id": "src_ris", "label": "Austria · OGH", "kind": "source",
           "count": int(in_set.get("ris", n_ris)),
           "note": f"DE · {n_ris:,} imported ({ris_types.get('Rechtssatz', 0):,} Rechtssätze + "
                   f"{ris_types.get('Text', 0):,} decision texts)"
                   + (f" → {int(in_set['ris']):,} in the civil-law working set"
                      if "ris" in in_set else ""),
           "desc": "Oberster Gerichtshof — Austrian supreme court, via RIS.",
           "example": "Unter welchen Voraussetzungen kann die Obhut entzogen werden?"},
          {"id": "src_swiss", "label": "Switzerland", "kind": "source",
           "count": n_swiss,
           "note": f"DE · cantonal & federal civil courts · "
                   f"{n('SELECT COUNT(DISTINCT canton) FROM swiss_meta')} cantons",
           "desc": "Swiss cantonal and federal decisions, via entscheidsuche.ch.",
           "example": "Wie unterscheiden sich die Kantone bei der Obhut?"},
      ]}

# ---- Bucket 2: metadata tables the NL->SQL translator is told about ----------------------
tables = [
    {"id": "t_echr_meta", "label": "echr_meta", "kind": "table", "count": n("SELECT COUNT(*) FROM echr_meta"),
     "desc": "ECHR case-level metadata: respondent, year, importance, formation, "
             "proceedings duration, separate opinions.",
     "children": [
         field("respondent", "respondent", "echr_meta", "respondent", "How many cases against Poland?"),
         field("year", "year", "echr_meta", "year", "How many ECHR cases per year?"),
         field("importance", "importance", "echr_meta", "importance", "How many importance-1 cases are there?"),
         field("formation", "formation", "echr_meta", "formation", "How many Grand Chamber cases?"),
         field("duration_days", "duration_days", "echr_meta", "duration_days",
               "What is the median time from application to judgment?",
               note="introduction → judgment; none for communicated cases"),
         field("separate_opinion", "separate_opinion", "echr_meta", "separate_opinion",
               "How many cases have a separate opinion?")]},
    {"id": "t_echr", "label": "echr (extracted)", "kind": "table", "count": n_echr,
     "desc": "ECHR extraction/theme table — rules-derived per-case columns (outcome, genre, "
             "articles, themes) over the full corpus.",
     "children": [
         field("respondent_state", "respondent_state", "echr", "respondent_state", "How many cases against Romania?", derived=True),
         field("genre", "genre", "echr", "genre", "How many merits judgments are there?", derived=True),
         field("outcome", "outcome", "echr", "outcome", "What share of merits cases found a violation?", derived=True),
         field("articles", "articles", "echr", "articles", "How many cases concern Article 6?", multi=True, derived=True),
         field("primary_theme", "primary_theme", "echr", "primary_theme", "How many care-removal cases?", derived=True),
         field("theme_group", "theme_group", "echr", "theme_group", "How many public-protection cases?", derived=True)]},
    {"id": "t_swiss_meta", "label": "swiss_meta", "kind": "table", "count": n_swiss,
     "desc": "Swiss decisions metadata.",
     "children": [
         field("canton", "canton", "swiss_meta", "canton", "How many Swiss cases from Kanton Bern?"),
         field("court_type", "court_type", "swiss_meta", "court_type", "How many Swiss cases per court type?"),
         field("year", "year", "swiss_meta", "year", "How many Swiss cases per year?")]},
    {"id": "t_ris_meta", "label": "ris_meta", "kind": "table", "count": n_ris,
     "desc": "Austrian OGH metadata.",
     "children": [
         field("dokumenttyp", "dokumenttyp", "ris_meta", "dokumenttyp", "How many Rechtssätze vs decisions?"),
         field("senate", "senate", "ris_meta", "senate", "How many cases per senate?"),
         field("year", "year", "ris_meta", "year", "How many Austrian cases per year?")]},
    {"id": "t_keyword_hits", "label": "keyword_hits", "kind": "table",
     "count": n("SELECT COUNT(DISTINCT keyword) FROM keyword_hits"),
     "desc": "Every case's matched IMPORT keywords, per source — joins to the meta tables on id. "
             "A matched keyword is not a classified theme.",
     "children": [
         field("kw_echr", "ECHR keywords (EN)", "keyword_hits", "keyword",
               "How many ECHR cases mention child abduction per respondent?",
               where="source = 'echr'", note="join keyword_hits→echr_meta"),
         field("kw_swiss", "Swiss keywords (DE)", "keyword_hits", "keyword",
               "How many Swiss cases mention Obhut per canton?",
               where="source = 'swiss'", note="join keyword_hits→swiss_meta"),
         field("kw_ris", "Austrian keywords (DE)", "keyword_hits", "keyword",
               "How many Austrian cases mention Obsorge per year?",
               where="source = 'ris'", note="join keyword_hits→ris_meta")]},
]
if case_themes is not None:
    flags = [c for c in case_themes.columns if c.startswith("is_")]
    by_src = ", ".join(f"{s} {v:,}" for s, v in case_themes.groupby("source").size().items())
    tables.append(
        {"id": "t_case_themes", "label": "case_themes", "kind": "table", "count": len(case_themes),
         "desc": "Zero-shot family-law THEMES for ALL sources (portable multilingual classifier, "
                 "one English spec; approximate/high-recall, not a validated classifier). "
                 f"{len(case_themes):,} records ({by_src}).",
         "children": [
             field("ct_primary", "primary_theme", "case_themes", "primary_theme",
                   "How many contact_access cases per Swiss canton?", derived=True,
                   note="join case_themes→swiss_meta/echr_meta/ris_meta on id (+ source)"),
             {"id": "ct_flags", "label": "theme flags (is_*)", "kind": "field",
              "example": "How many abduction_hague cases per respondent state?",
              "coverage": 100,
              "note": f"{len(flags)} boolean themes × {case_themes.source.nunique()} sources "
                      f"({', '.join(c[3:] for c in flags)}) · derived column — distribution not shown",
              "values": []}]})

b2 = {"id": "b2", "label": "Bucket 2 · metadata SQL", "bucket": "b2",
      "desc": "Countable questions over structured metadata via guarded NL→SQL. The generated SQL "
              "is shown as the trust boundary.",
      "example": "How many cases against Poland are in the corpus?", "children": tables}

# ---- Bucket 3: deployed content fields + the scope they can be cut by ---------------------
def f1_of(v):
    return next((v[k] for k in ("llm_f1", "f1", "rules_f1") if k in v), None)


cfields = []
for fname, meta in st.DEPLOYED_FIELDS.items():
    thr, v = meta["threshold"], meta.get("validation", {})
    tot = n(f"SELECT COUNT(*) FROM field_{fname}")
    f1 = f1_of(v)
    cfields.append({
        "id": f"f_{fname}", "label": fname, "kind": "cfield",
        "desc": meta["definition"].split(". ")[0].rstrip(".") + ". Confident = TRUE AND calibrated "
                f"conf ≥ {thr:.2f}; low-confidence cells are abstained and surfaced, not dropped.",
        "example": f"How many cases where {(meta.get('question_terms') or [fname.replace('_', ' ')])[0]}?",
        "coverage": 100,
        "note": " · ".join(x for x in (f"threshold {thr:.2f}", f"F1 {f1:.3f}" if f1 else "",
                                        f"{v['n_labels']} labels" if "n_labels" in v else "",
                                        meta.get("model", ""),
                                        "derived column — distribution not shown") if x),
        "values": [],
        "count": tot})

scope_dims = []
for col, dim in st._DIMS.items():
    p = profile("echr_scope", col, multi=dim["kind"] == "list")
    if col in DERIVED:
        _no_values(p)
    scope_dims.append({"id": f"sc_{col}", "label": col, "kind": "field",
                       "example": f"How many {cfields[0]['label'].replace('_', ' ') if cfields else ''} "
                                  f"cases per {col.replace('_', ' ')}?",
                       **{**p, "note": " · ".join(x for x in (
                           dim["kind"] + (" · ';'-list, matched per atom" if dim["kind"] == "list" else ""),
                           p.get("note", "")) if x)}})
cfields.append({
    "id": "t_echr_scope", "label": "echr_scope · filters", "kind": "table", "count": len(scope_dims),
    "desc": "Every dimension a deployed field can be filtered or grouped by — echr + echr_meta + "
            "echr_hudoc (raw HUDOC fields incl. article-level violation / nonviolation), profiled "
            "from the data at startup. Conditions combine; a condition the corpus cannot honour "
            "is refused, never dropped.",
    "children": scope_dims})

b3 = {"id": "b3", "label": "Bucket 3 · extracted / calibrated", "bucket": "b3",
      "desc": "Content aggregates over validated, per-case extracted fields with a calibrated "
              "confidence threshold and an abstention audit. Fields combine (AND, each at its own "
              "threshold) and can be cut by any ECHR scope dimension.",
      "example": "How many cases have both an expert opinion ordered and the child heard?",
      "children": cfields}

# ---- Bucket 4: diachronic wording change --------------------------------------------------
b4 = {"id": "b4", "label": "Bucket 4 · wording over time", "bucket": "b4",
      "desc": "“What changed for <any word or topic> between X and Y?” — not tied to a field "
              "or a fixed topic list. Windowed keyness around the term, grounded in KWIC quotes, "
              "with a deterministic word-guard on the summary. ECHR / English only, "
              f"{DIA_RANGE[0]}–{DIA_RANGE[1]}: RIS Rechtssätze are undatable and pre-2010 Swiss "
              "coverage is thin, so a German run is refused.",
      "example": "How has the Court's language on parental alienation changed since 2010?",
      "children": []}

refuse = {"id": "refuse", "label": "Refusal · not extracted", "bucket": "refuse",
          "desc": "Concepts no validated per-case column carries. Answering from retrieval would "
                  "fabricate a statistic, so the system refuses (or you build + validate a field in "
                  "the field factory).",
          "example": "In what proportion of cases did the mother receive custody?",
          "children": [
              {"id": "r_custody", "label": "custody outcome", "kind": "gap",
               "desc": "Who was granted custody — not extracted.",
               "example": "In what proportion of cases did the mother receive custody?"},
              {"id": "r_marital", "label": "marital status", "kind": "gap",
               "desc": "Whether the parents were married — not extracted.",
               "example": "How many applicants were married?"}]}

DATA_JSON = {
    "generated": datetime.now().isoformat(timespec="seconds"),
    "banner": f"✓ {n_echr:,} ECHR · {n_ris:,} Austrian · {n_swiss:,} Swiss records · "
              f"{len(st.DEPLOYED_FIELDS)} deployed content fields "
              f"({', '.join(st.DEPLOYED_FIELDS)}) · {len(st._DIMS)} ECHR scope dimensions.",
    "root": {"label": "ask anything",
             "desc": "One question box. The router picks the only bucket that can answer faithfully."},
    "buckets": [b1, b2, b3, b4, refuse],
}

# ---- write back into the page -------------------------------------------------------------
html = OUT.read_text()
start = html.index('<script id="data" type="application/json">') + len('<script id="data" type="application/json">')
end = html.index("</script>", start)
blob = json.dumps(DATA_JSON, indent=1, ensure_ascii=False, default=int).replace("</", "<\\/")
OUT.write_text(html[:start] + blob + html[end:])
print(f"wrote {OUT.name}: {len(DATA_JSON['buckets'])} buckets | "
      f"{sum(len(c.get('children', [])) for b in DATA_JSON['buckets'] for c in b['children'])} fields | "
      f"deployed: {', '.join(st.DEPLOYED_FIELDS)}")
