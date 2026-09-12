"""Re-run evaluation.ipynb and export a plain HTML of its cells + outputs.

Usage (from repo root or src/):
    .venv/bin/python src/run_evaluation.py                # re-execute, then export
    EVAL_FIELD=<name> .venv/bin/python src/run_evaluation.py   # pick a content field to score
    RENDER_ONLY=1 .venv/bin/python src/run_evaluation.py  # just re-export existing outputs

The notebook has no RUN_LLM gate any more. It degrades on what is actually reachable:
- generation backend: whatever GEN_BACKEND names (probed once, recorded in the output);
- NL->SQL: runs live when `ollama serve` is up, otherwise scores from
  data/synthetic_qa_cache.json, otherwise registers itself pending with the reason.

Writes: src/evaluation.ipynb (outputs refreshed) + reports/evaluation.html
        + reports/evaluation_results.json + reports/evaluation_summary.md.
No jupyter needed (jupyter here resolves to anaconda; this runs in-process).
"""
import contextlib
import html as _html
import io
import json
import os
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent
os.chdir(SRC)                                   # so "../data" and ask.ipynb resolve
NB = SRC / "evaluation.ipynb"
OUT_HTML = SRC.parent / "reports" / "evaluation.html"

nb = json.loads(NB.read_text())

# ---- re-execute code cells in one shared namespace (unless RENDER_ONLY) ----
if os.environ.get("RENDER_ONLY", "0") != "1":
    g = {}
    print(f"executing {NB.name} "
          f"(EVAL_FIELD={os.environ.get('EVAL_FIELD') or 'auto-discover'}) ...", flush=True)
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(src, g)
            txt = buf.getvalue()
        except Exception as e:                  # keep going; show the error in the cell
            txt = buf.getvalue() + f"\n!! ERROR: {type(e).__name__}: {e}"
            print("  cell errored:", e)
        cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": txt}]
        cell["execution_count"] = 1
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
    print("refreshed outputs ->", NB.name)


# ---- minimal markdown -> HTML (headers, lists, bold, inline code) ----
def md(text):
    out, in_ul, para = [], False, []
    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
    for raw in text.split("\n"):
        line = raw.rstrip()
        if line.startswith("- "):
            flush()
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append("<li>" + inline(line[2:]) + "</li>"); continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        if line.startswith("### "):
            flush(); out.append("<h3>" + inline(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush(); out.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush(); out.append("<h1>" + inline(line[2:]) + "</h1>")
        elif line.strip():
            para.append(line)                       # accumulate into a flowing paragraph
        else:
            flush()
    flush()
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline(s):
    s = _html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


# ---- render cells ----
blocks = []
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if cell["cell_type"] in ("markdown", "md"):
        blocks.append('<div class="md">' + md(src) + "</div>")
    else:
        # outputs only -- the code input is intentionally excluded
        out = "".join(o.get("text", "") for o in cell.get("outputs", []))
        if out.strip():
            blocks.append('<div class="cell"><pre class="out">' + _html.escape(out) + "</pre></div>")

page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>evaluation.ipynb</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    color:#1a1a1a;background:#fff;max-width:60em;margin:0 auto;padding:2.5em 1.5em 6em;line-height:1.5}
  h1{font-size:1.7em;margin:1.2em 0 .4em}h2{font-size:1.3em;margin:1.4em 0 .3em;border-bottom:1px solid #eee;padding-bottom:.2em}
  h3{font-size:1.08em;margin:1em 0 .3em}p{margin:.5em 0}ul{margin:.4em 0 .4em 1.4em}li{margin:.15em 0}
  code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#f2f2f4;padding:.1em .35em;border-radius:4px;font-size:.9em}
  .cell{margin:1.1em 0}
  pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;line-height:1.45;
    white-space:pre-wrap;overflow-x:auto;border-radius:6px;padding:12px 14px;margin:0}
  pre.in{background:#f6f8fa;border:1px solid #e6e8eb;color:#24292f}
  pre.out{background:#fbfbfc;border:1px solid #eee;border-top:none;color:#333}
  @media (prefers-color-scheme:dark){
    body{background:#0f1115;color:#e6e6e6}h2{border-color:#2a2d34}code{background:#20232a}
    pre.in{background:#161a20;border-color:#2a2d34;color:#dfe3ea}
    pre.out{background:#121519;border-color:#242830;color:#c9ccd2}}
</style></head><body>
""" + "\n".join(blocks) + "\n</body></html>"

OUT_HTML.write_text(page)
print("wrote", OUT_HTML)
