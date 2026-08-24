"""citation_check.py -- are the references in a grounded answer real?

The cheap half of a faithfulness evaluation. For every answer it asks three questions that
need no gold labels and no second model:

  1. does every cited id EXIST in the corpus?              -> invented citations
  2. was every cited id actually IN THE PROMPT?            -> cited-but-never-read
  3. does every quoted span APPEAR in a source it cited?   -> invented quotes

(1) and (2) come straight from grounding_report(); (3) is a normalised substring test, which
is why this is minutes rather than hours. It does NOT check whether the answer is a fair
reading of the sources -- an answer can pass all three and still misdescribe the law.

Run (from src/):  ../.venv/bin/python citation_check.py --limit 6 --modes hybrid,full
Output:           ../reports/citation_check.json  (checkpointed after every question)
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASK_NB = HERE / "ask.ipynb"
RETR_NB = HERE / "retrieval_evaluation.ipynb"
OUT = HERE.parent / "reports" / "citation_check.json"
BOOT_MARKERS = ["RAG_NB   = Path", "_swiss = _json.loads", "def _h_diachronic", "def _h_alienation"]

QUOTE_RE = re.compile(r"[\"“«]([^\"”»]{25,400})[\"”»]")
MIN_QUOTE_WORDS = 5      # shorter "quotes" are usually a term of art, not a claimed quotation


def boot():
    nb = json.loads(ASK_NB.read_text())
    for c in nb["cells"]:
        if c["cell_type"] == "code" and any(m in "".join(c["source"]) for m in BOOT_MARKERS):
            exec("".join(c["source"]), globals())
    assert "answer" in globals(), "pipeline did not load"


def questions(limit=None):
    """Reuse the retrieval evaluation's EN/DE question set -- same questions, so citation
    behaviour can be read next to the retrieval numbers instead of on its own scale."""
    nb = json.loads(RETR_NB.read_text())
    for c in nb["cells"]:
        src = "".join(c["source"])
        if c["cell_type"] == "code" and src.strip().startswith("EVAL_QUERIES = ["):
            ns = {}
            exec(src[:src.index("]") + 1], ns)
            qs = ns["EVAL_QUERIES"]
            return qs[:limit] if limit else qs
    raise SystemExit("EVAL_QUERIES not found in retrieval_evaluation.ipynb")


def _norm(t):
    # the ECHR corpus has underscores where commas belong, and models reflow whitespace;
    # compare on letters and digits only so neither counts as a quote mismatch
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower())).strip()


def quote_check(answer_text, used_hits):
    """Every quoted span in the answer must appear verbatim in some source that was in the
    prompt. Unverified spans are the model's own words presented as the Court's."""
    sources = _norm(" ".join(h["text"] for h in used_hits))
    rows = []
    for q in QUOTE_RE.findall(answer_text or ""):
        if len(q.split()) < MIN_QUOTE_WORDS:
            continue
        rows.append({"quote": q[:160], "found_in_prompt": _norm(q) in sources})
    return rows


def check_one(qid, lang, q, mode):
    globals()["GEN_PACKING"] = mode          # read per call, so this needs no re-boot
    r = answer(q)
    g = r["grounding"] or {}
    quotes = quote_check(r["answer"], r.get("used", []))
    path = save_provenance(r, route=f"citation_check:{mode}")
    return {
        "qid": qid, "lang": lang, "question": q, "packing": mode,
        "abstained": r["abstained"],
        "cases_retrieved": g.get("cases_retrieved", 0),
        "cases_in_prompt": g.get("cases_in_prompt", 0),
        "cases_cited": g.get("cases_cited", 0),
        "citations_ok": len(g.get("cited_chunk_ids", [])),
        "citations_invented": g.get("citations_invented", []),
        "citations_real_but_unseen": g.get("citations_real_but_unseen", []),
        "quotes_checked": len(quotes),
        "quotes_unverified": [x["quote"] for x in quotes if not x["found_in_prompt"]],
        "provenance": str(path),
    }


def summarise(rows):
    out = {}
    for mode in sorted({r["packing"] for r in rows}):
        rs = [r for r in rows if r["packing"] == mode]
        cites = sum(r["citations_ok"] for r in rs)
        inv = sum(len(r["citations_invented"]) for r in rs)
        unseen = sum(len(r["citations_real_but_unseen"]) for r in rs)
        quotes = sum(r["quotes_checked"] for r in rs)
        bad_q = sum(len(r["quotes_unverified"]) for r in rs)
        out[mode] = {
            "questions": len(rs),
            "answers_with_no_citation": sum(1 for r in rs if not r["citations_ok"]),
            "citations_resolved": cites, "citations_invented": inv,
            "citations_real_but_unseen": unseen,
            "citation_precision": round(cites / (cites + inv + unseen), 3) if cites + inv + unseen else None,
            "quotes_checked": quotes, "quotes_unverified": bad_q,
            "quote_precision": round((quotes - bad_q) / quotes, 3) if quotes else None,
            "mean_cases_cited": round(sum(r["cases_cited"] for r in rs) / len(rs), 2),
            "mean_cases_in_prompt": round(sum(r["cases_in_prompt"] for r in rs) / len(rs), 2),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=6, help="questions per packing mode")
    ap.add_argument("--modes", default="hybrid", help="comma-separated: hybrid,full,extract")
    args = ap.parse_args()

    boot()
    qs = questions(args.limit)
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    print(f"citation check: {len(qs)} questions x {len(modes)} packing modes", flush=True)

    rows = []
    for mode in modes:
        for qid, lang, q in qs:
            rows.append(check_one(qid, lang, q, mode))
            r = rows[-1]
            print(f"  {mode:8s} {qid} [{lang}] cited={r['citations_ok']} "
                  f"invented={len(r['citations_invented'])} "
                  f"unseen={len(r['citations_real_but_unseen'])} "
                  f"quotes={r['quotes_checked']}/{len(r['quotes_unverified'])} bad", flush=True)
            OUT.write_text(json.dumps({"run_at": datetime.now().isoformat(timespec="seconds"),
                                       "summary": summarise(rows), "rows": rows},
                                      ensure_ascii=False, indent=1))   # checkpoint every answer

    print("\nSUMMARY")
    for mode, s in summarise(rows).items():
        print(f"  {mode:8s} citation precision {s['citation_precision']} "
              f"({s['citations_invented']} invented, {s['citations_real_but_unseen']} unseen "
              f"of {s['citations_resolved'] + s['citations_invented'] + s['citations_real_but_unseen']}) "
              f"| quote precision {s['quote_precision']} ({s['quotes_unverified']}/{s['quotes_checked']} bad) "
              f"| mean cases cited {s['mean_cases_cited']} of {s['mean_cases_in_prompt']} in prompt")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
