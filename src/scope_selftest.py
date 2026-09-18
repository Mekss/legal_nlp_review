"""Sweep every metadata dimension a deployed content field can be asked about.

Run:  .venv/bin/python src/scope_selftest.py

The point of this file is that the sweep WRITES ITSELF. It profiles the corpus, and for every
dimension it finds it generates a question, resolves the scope, runs the SQL, and compares the
result against the same filter applied directly -- so a new metadata column or a new deployed
field is covered the moment it exists, with nothing added here. Three silent wrong answers
(a dropped country, a dropped year, a dropped everything-else) were each found by hand, one
question at a time; this is that process, done exhaustively and repeatably.

The scope block is read out of `src/ask.ipynb`, so what is tested is the shipped code. Country
NAME -> ISO resolution belongs to Bucket 1's learned map and is stubbed here (it needs the full
pipeline); the live server check covers it.
"""
import json, random, re as _re, sys
from pathlib import Path

import duckdb, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
random.seed(0)


def load_scope_block(nb_path=ROOT / "src" / "ask.ipynb"):
    """The shipped resolver, lifted verbatim out of the notebook."""
    for cell in json.load(open(nb_path))["cells"]:
        src = "".join(cell["source"])
        if "def _deployed_scope(" in src:
            start = src.index("# Scope resolution")
            start = src.rindex("# ---", 0, start)
            return src[start:src.index("def _h_alienation(")]
    raise SystemExit("no scope block found in ask.ipynb")


# ---- a minimal stand-in for the pipeline the resolver normally runs inside ------------------
echr = pd.read_parquet(DATA / "echr_themes.parquet")
echr["year"] = pd.to_datetime(echr["judgment_date"], errors="coerce").dt.year
con = duckdb.connect()
con.register("echr", echr)

# echr_meta as the live pipeline shapes it (values synthesised -- this proves the view JOIN
# picks up columns `echr` does not have; the live check runs against the real one)
con.register("echr_meta", pd.DataFrame({
    "id": echr.id,
    # the real HUDOC spellings: one token, upper case. "Grand Chamber" as a person types it
    # only resolves because the resolver closes up spaces between adjacent words.
    "formation": [random.choice(["GRANDCHAMBER", "CHAMBER", "COMMITTEE"]) for _ in range(len(echr))],
    "duration_days": [random.randint(200, 4000) for _ in range(len(echr))],
    "separate_opinion": [random.random() < 0.2 for _ in range(len(echr))],
    "importance": echr.importance, "year": echr.year}))

_GROUP_SYNONYMS = {"theme": ["primary_theme"], "primary theme": ["primary_theme"],
                   "theme group": ["theme_group"], "state": ["respondent_state"],
                   "country": ["respondent_state"], "respondent": ["respondent_state"],
                   "year": ["year"], "outcome": ["outcome"], "genre": ["genre"],
                   "importance": ["importance"], "formation": ["formation"],
                   "article": ["articles"], "canton": ["canton"], "senate": ["senate"]}

_COUNTRIES = {"poland": "POL", "romania": "ROU", "germany": "DEU", "russia": "RUS",
              "italy": "ITA", "norway": "NOR", "france": "FRA", "turkey": "TUR"}


def _sql_route(question):                    # Bucket 1 owns the real learned map
    q = f" {(question or '').lower()}"
    return "", [("respondent_state", c) for n, c in _COUNTRIES.items() if f" {n}" in q]


exec(load_scope_block(), globals())

FIELDS = sorted(p.name[len("field_"):-len("_deployed.parquet")]
                for p in DATA.glob("field_*_deployed.parquet"))
for f in FIELDS:
    con.register(f"field_{f}", pd.read_parquet(DATA / f"field_{f}_deployed.parquet"))


def counts(field, where):
    return con.execute(f"""SELECT COUNT(*) FILTER (f."{field}" AND f.conf_cal >= 0.7), COUNT(*)
                           FROM field_{field} f JOIN echr_scope e ON f.id = e.id
                           WHERE TRUE{where}""").fetchone()


def frequent(col, n=5):
    return [r[0] for r in con.execute(
        f'SELECT "{col}" FROM echr_scope WHERE "{col}" IS NOT NULL '
        f'GROUP BY 1 ORDER BY count(*) DESC LIMIT {n}').fetchall()]


def probe_for(col, dim, field):
    """Generate a question for one dimension, plus the filter it must produce."""
    spaced = col.replace("_", " ")
    if col == "respondent_state":
        return f"how many {spaced} cases in Poland".replace(spaced, field.replace('_', ' ')), \
               "e.respondent_state = 'POL'"
    stem = f"how many {field.replace('_', ' ')} cases"
    if col == "year":
        return f"{stem} in 2022", "e.year = 2022"
    if dim["kind"] == "cat":
        v = next(x for x in frequent(col) if len(str(x)) >= 4)
        return f"{stem} with {spaced} {str(v).replace('_', ' ')}", f"e.{col} = '{v}'"
    if dim["kind"] == "bool":
        bare = col.split("_", 1)[1] if col.startswith(("is_", "has_")) else col
        return f"{stem} involving {bare.replace('_', ' ')}", f"e.{col} = TRUE"
    if dim["kind"] == "num":
        v = next(x for x in frequent(col) if x is not None)
        v = int(v) if float(v) == int(float(v)) else round(float(v), 4)
        return f"{stem} with {spaced} {v}", f"e.{col} = {v}"
    atom = max(dim["values"], key=lambda a: len(str(a)))
    return (f"{stem} under {sorted(_DIM_PREFIXES[col], key=len)[0]} {atom}",
            f"""(';' || e.{col} || ';') LIKE '%;{atom};%'""")


def main():
    if not FIELDS:
        raise SystemExit("no deployed fields in data/ -- nothing to sweep")
    # sweep with the field carrying the most confident cells: a field that abstains everywhere
    # compares 0 against 0 on every probe and would pass a resolver that filtered nothing
    field = max(FIELDS, key=lambda f: counts(f, "")[0])
    base = counts(field, "")
    print(f"corpus: {len(echr)} ECHR cases | deployed fields: {', '.join(FIELDS)}")
    print(f"sweeping with `{field}`; baseline (no filter): "
          f"{base[0]} confident of {base[1]}\n")
    fails = []

    print(f"{'ok':4s} {'dimension':22s} {'confident/scope':>16s}  resolved scope")
    for col, dim in _DIMS.items():
        q, expect = probe_for(col, dim, field)
        where, grp, note = _deployed_scope(q, field_terms=field)
        if where is None:
            fails.append((col, q, f"refused: {note}"))
            print(f"{'FAIL':4s} {col:22s} {'':>16s}  REFUSED: {note[:60]}")
            continue
        got, want = counts(field, where), counts(field, " AND " + expect)
        ok = got == want and where.strip()
        if not ok:
            fails.append((col, q, f"got {got} want {want} | {where}"))
        print(f"{'ok' if ok else 'FAIL':4s} {col:22s} {f'{got[0]}/{got[1]}':>16s}  "
              f"{note or '*** NOTHING RESOLVED ***'}")

    print(f"\n{'ok':4s} the same sweep for every other deployed field -- the field's own name is\n"
          f"     masked out of the question, and what that masking removes depends on the field")
    for other in FIELDS:
        if other == field:
            continue
        bad = []
        for col, dim in _DIMS.items():
            q, expect = probe_for(col, dim, other)
            where, _, note = _deployed_scope(q, field_terms=other)
            if where is None or not where.strip():
                bad.append((col, note or "nothing resolved"))
            elif counts(other, where) != counts(other, " AND " + expect):
                bad.append((col, f"count mismatch | {where}"))
        fails += [(other, c, why) for c, why in bad]
        print(f"{'ok' if not bad else 'FAIL':4s}   {other:24s} {len(_DIMS) - len(bad)}/{len(_DIMS)} dimensions")

    print(f"\n{'ok':4s} breakdowns")
    for col, dim in _DIMS.items():
        if dim["kind"] not in ("bool", "cat", "num"):
            continue
        _, grp, _ = _deployed_scope(
            f"how many {field.replace('_', ' ')} cases per {col.replace('_', ' ')}",
            field_terms=field)
        if grp != col:
            fails.append((col, "per " + col, f"resolved to {grp!r}"))
        print(f"{'ok' if grp == col else 'FAIL':4s}   per {col}")

    print(f"\n{'ok':4s} refusals -- a condition the corpus cannot honour must never pass quietly")
    for q in [f"how many {field} cases per canton", f"how many {field} cases per judge",
              f"how many {field} cases for each applicant surname"]:
        where, _, note = _deployed_scope(q, field_terms=field)
        if where is not None:
            fails.append(("refusal", q, "answered instead of refusing"))
        print(f"{'ok' if where is None else 'FAIL':4s}   {q}")

    print(f"\n{'ok':4s} negative controls -- no condition named, so nothing may be filtered")
    for q in [f"how many {field.replace('_', ' ')} cases are there",
              f"in how many judgments was {field.replace('_', ' ')} found"]:
        where, grp, note = _deployed_scope(q, field_terms=field)
        clean = where == "" and grp is None
        if not clean:
            fails.append(("negative", q, f"invented {note!r} / {grp!r}"))
        print(f"{'ok' if clean else 'FAIL':4s}   {q}")

    # Generated probes phrase things the easy way (column name, then value). These are the
    # phrasings a person actually types, and the readings that must not collide.
    print(f"\n{'ok':4s} phrasing -- written by hand, because a generator cannot be adversarial\n"
          f"     about its own output")
    f2 = "coercive_measures"
    PHRASING = [
        ("how many coercive measures cases ended in no violation", {"outcome = 'no violation'"}, None),
        ("how many coercive measures cases ended in a violation",  {"outcome = 'violation'"}, None),
        ("how many coercive measures cases involve domestic violence",
         {"is_domestic_violence = TRUE"}, None),
        ("how many coercive measures cases with primary theme domestic violence",
         {"primary_theme = 'domestic_violence'"}, None),
        ("how many coercive measures cases in Poland in 2022",
         {"respondent_state = 'POL'", "year = 2022"}, None),
        ("how many coercive measures cases involving domestic violence in Poland since 2015",
         {"respondent_state = 'POL'", "year >= 2015", "is_domestic_violence = TRUE"}, None),
        ("how many coercive measures cases in Poland per year", {"respondent_state = 'POL'"}, "year"),
        ("how many coercive measures cases per country since 2015", {"year >= 2015"}, "respondent_state"),
        ("how many merits judgments of importance 1 involve coercive measures",
         {"genre = 'merits'", "importance = 1"}, None),
        ("how many coercive measures cases with duration over 2000 days", {"duration_days > 2000"}, None),
        ("how many coercive measures cases of importance at least 2", {"importance >= 2"}, None),
        ("how many coercive measures cases under article 8 in Poland",
         {"articles contains '8'", "respondent_state = 'POL'"}, None),
        ("how many coercive measures cases decided by the Grand Chamber",
         {"formation = 'GRANDCHAMBER'"}, None),
        ("how many coercive measures cases with a separate opinion", {"separate_opinion = TRUE"}, None),
    ]
    for q, want, wantgrp in PHRASING:
        where, grp, note = _deployed_scope(q, field_terms=f2)
        got = {x.strip() for x in note.replace("filtered on ", "").split(" and ")} if note else set()
        ok = where is not None and got == want and grp == wantgrp
        if not ok:
            fails.append(("phrasing", q, f"got {sorted(got)} / {grp!r}, want {sorted(want)} / {wantgrp!r}"))
        print(f"{'ok' if ok else 'FAIL':4s}   {q}")

    print(f"\n==== {len(_DIMS)} dimensions swept | FAILURES: {len(fails)}")
    for f in fails:
        print("    ", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
