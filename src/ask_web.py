"""ask_web.py -- chatbot webpage over ask_anything() from ask.ipynb.

Boots the exact same cells ask.ipynb execs (RAG pipeline + query layer +
metadata relations + dispatcher), then serves a single-page chat UI.
Every question/answer pair is appended to ../data/ask_web_history.json,
so the conversation history survives restarts and is shown on page load.

Run (from src/):   ../.venv/bin/python ask_web.py
Open:              http://127.0.0.1:8765

No third-party web framework -- stdlib http.server only.
"""

import contextlib
import io
import json
import os
import random
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
HERE = Path(__file__).resolve().parent
ASK_NB = HERE / "ask.ipynb"
PAGE = HERE / "ask_web.html"
HIST_PATH = HERE.parent / "data" / "ask_web_history.json"
REGISTRY_PATH = HERE.parent / "reports" / "value_registry.json"  # value_registry.ipynb

# value-registry source -> (queryable duckdb table, display label)
REG_SOURCES = {
    "echr": ("echr", "ECHR"),
    "echr_extracted (derived)": ("echr", "ECHR"),
    "echr_themes (derived)": ("echr", "ECHR"),
    "swiss": ("swiss_meta", "Swiss"),
    "ris": ("ris_meta", "Austrian OGH"),
}
# not worth suggesting: constant per source, internal, or confidence machinery
SKIP_FIELDS = {"jurisdiction", "lang", "languageisocode", "matched_keywords",
               "content_type", "from_rechtssatz", "alienation_alleged",
               "alienation_conf", "alienation_conf_cal", "outcome_conf"}

# the three code cells of ask.ipynb that build the whole system
# (pipeline loader, metadata relations, dispatcher) -- same marker
# technique the notebook itself uses, so web and notebook cannot drift
BOOT_MARKERS = ["RAG_NB   = Path", "_swiss = _json.loads", "def _h_alienation"]

_LOCK = threading.Lock()  # ask_anything + duckdb con are not thread-safe


def boot():
    os.chdir(HERE)  # notebook paths ("../data", sibling .ipynb) are src-relative
    nb = json.loads(ASK_NB.read_text())
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if any(m in src for m in BOOT_MARKERS):
            exec(src, globals())
    assert "ask_anything" in globals(), "dispatcher cell did not load"


def load_history():
    if HIST_PATH.exists():
        return json.loads(HIST_PATH.read_text()).get("entries", [])
    return []


def save_history(entries):
    HIST_PATH.write_text(json.dumps(
        {"saved_at": datetime.now().isoformat(timespec="seconds"),
         "entries": entries}, ensure_ascii=False, indent=1))


def run_question(question):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            globals()["ask_anything"](question)
        except Exception as e:
            print("ERROR while answering:", e)
    return buf.getvalue()


_POOL = None


def suggestion_pool():
    """Askable fields: value-registry categoricals that exist in a registered
    duckdb table, plus factory-deployed content fields, plus the one validated
    alienation column. Built once; /suggest samples from it."""
    global _POOL
    if _POOL is not None:
        return _POOL
    con = globals()["con"]
    pool = [{"field": "parental alienation allegation", "source": "ECHR content",
             "values": ["extracted + calibrated, threshold-aware"],
             "fill": "How many cases involve an allegation of parental alienation?"}]
    seen = set()
    if REGISTRY_PATH.exists():
        reg = json.loads(REGISTRY_PATH.read_text())
        cols = {}
        for table, _ in REG_SOURCES.values():
            try:
                cols[table] = {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
            except Exception:
                cols[table] = set()
        for src, entry in reg.items():
            if src not in REG_SOURCES:
                continue
            table, label = REG_SOURCES[src]
            for f, v in entry["fields"].items():
                if (v["kind"] != "categorical" or f in SKIP_FIELDS or (label, f) in seen
                        or f not in cols[table] or v.get("coverage_pct", 100) < 30
                        or v["n_distinct"] < 2):
                    continue
                seen.add((label, f))
                pool.append({"field": f, "source": label,
                             "values": [k for k in v["values"] if k != "(other)"][:6]})
    for fname, meta in globals().get("DEPLOYED_FIELDS", {}).items():
        pool.append({"field": fname.replace("_", " "), "source": "ECHR content",
                     "values": meta.get("lexicon", [])[:4],
                     "fill": f"How many cases involve {fname.replace('_', ' ')}?"})
    _POOL = pool
    return pool


def suggestions(n=6):
    """A fresh random subset of askable fields, each with a starter question."""
    pool = suggestion_pool()
    out = []
    for s in random.sample(pool, min(n, len(pool))):
        fill = s.get("fill")
        if not fill:  # metadata field: randomly a per-field or a per-value starter
            if set(s["values"]) <= {"True", "False"}:
                fill = f"How many {s['source']} cases have {s['field'].replace('_', ' ')} True?"
            elif random.random() < 0.5:
                fill = f"How many {s['source']} cases per {s['field']}?"
            else:
                fill = (f"How many {s['source']} cases have "
                        f"{s['field'].replace('_', ' ')} {random.choice(s['values'])}?")
        out.append({"source": s["source"], "field": s["field"],
                    "values": s["values"], "fill": fill})
    return out


def stats():
    g = globals()
    return {
        "chunks": int(g["index"].ntotal),
        "table_rows": int(len(g["df"])),
        "router_patterns": len(g["AGGREGATE_PATTERNS"]),
        "deployed_fields": sorted(g.get("DEPLOYED_FIELDS", {})),
    }


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # keep the terminal readable; questions are logged in do_POST

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(
            body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/history":
            with _LOCK:
                self._send(200, {"entries": load_history(), "stats": stats(),
                                 "suggestions": suggestions()})
        elif self.path == "/suggest":
            self._send(200, {"suggestions": suggestions()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/ask":
            question = (self._body().get("question") or "").strip()
            if not question:
                self._send(400, {"error": "empty question"})
                return
            print(f"[{datetime.now():%H:%M:%S}] Q: {question}")
            with _LOCK:
                transcript = run_question(question)
                entry = {"ts": datetime.now().isoformat(timespec="seconds"),
                         "question": question, "transcript": transcript}
                entries = load_history() + [entry]
                save_history(entries)
            self._send(200, entry)
        elif self.path == "/clear":
            with _LOCK:
                save_history([])
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})


def main():
    print("booting pipeline from ask.ipynb ...")
    boot()
    s = stats()
    print(f"ready: {s['chunks']} chunks | {s['table_rows']} table rows | "
          f"fields: {', '.join(s['deployed_fields']) or 'none'}")
    print(f"serving on http://{HOST}:{PORT}  (history -> {HIST_PATH})")
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
