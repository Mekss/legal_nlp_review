"""Post-import pipeline: embed the refreshed corpus, then regenerate the reports.

master_import.ipynb writes the per-source JSON files and labels them with
`matched_norms`. Everything after that is this script. It is deliberately a plain
script and not a notebook so it survives a closed session: nothing here depends on
a Claude Code session, a kernel, or nbconvert (which is not installed in .venv).

    cd src
    ../.venv/bin/python run_pipeline.py             # embed, then all reports
    ../.venv/bin/python run_pipeline.py embed       # embedding / index only
    ../.venv/bin/python run_pipeline.py reports     # reports only

Step 1 is the long one: it re-chunks the corpus and embeds every chunk id that is
not already in data/rag_echr_ris_emb_cache.npz. The cache is per chunk id and is
checkpointed, so an interrupted run resumes instead of starting over.
"""

import json
import os
import runpy
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Report notebooks, in dependency order. Each is executed cell by cell in its own
# namespace, exactly as ask_web.py boots ask.ipynb.
REPORT_NOTEBOOKS = [
    "corpus_distributions.ipynb",   # -> reports/corpus_distributions.md + figures/
    "corpus_audit.ipynb",           # -> data/corpus_audit_shortlist.csv
    "data_summary.ipynb",           # prints corpus counts (read-only)
    "value_registry.ipynb",         # -> value_registry.json (feeds ask_web suggestions)
    "build_data_map.py",            # -> src/data_map.html
]


def run_notebook(name):
    """Exec every code cell of a notebook in a fresh namespace. Returns True on success."""
    path = HERE / name
    if not path.exists():
        print(f"  !! {name} not found — skipping", flush=True)
        return False
    if path.suffix == ".py":
        try:
            runpy.run_path(str(path), run_name="__main__")
            return True
        except Exception:
            print(f"  !! {name} failed", flush=True)
            traceback.print_exc()
            return False
    nb = json.loads(path.read_text())
    ns = {"__name__": "__main__"}
    for n, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        try:
            exec("".join(cell["source"]), ns)
        except Exception:
            print(f"  !! {name} failed in code cell {n}", flush=True)
            traceback.print_exc()
            return False
    return True


def step_embed():
    # ask_web.boot() execs the pipeline cells of ask.ipynb, which re-chunk the corpus
    # and build the index. New chunks are embedded and appended to the npz cache;
    # chunks already cached are reused, so this is cheap on a re-run and expensive
    # only the first time after a corpus reload.
    print("=" * 70, "\nSTEP 1  embedding / index build\n", "=" * 70, flush=True)
    t0 = time.time()
    sys.path.insert(0, str(HERE))
    import ask_web
    ask_web.boot()
    print(f"STEP 1 done in {(time.time() - t0) / 60:.1f} min", flush=True)


def step_reports():
    print("=" * 70, "\nSTEP 2  reports\n", "=" * 70, flush=True)
    ok, failed = [], []
    for name in REPORT_NOTEBOOKS:
        print(f"\n--- {name} ---", flush=True)
        t0 = time.time()
        (ok if run_notebook(name) else failed).append(name)
        print(f"--- {name}: {time.time() - t0:.0f}s ---", flush=True)
    print(f"\nreports ok: {ok}")
    if failed:
        print(f"reports FAILED: {failed}")
    return not failed


def main():
    os.chdir(HERE)   # every notebook path is src-relative ("../data", "../reports")
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.time()
    if what in ("all", "embed"):
        step_embed()
    if what in ("all", "reports"):
        step_reports()
    print(f"\nPIPELINE DONE in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
