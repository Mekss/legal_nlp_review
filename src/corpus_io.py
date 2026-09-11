"""Streaming reader for the per-source corpus files.

`json.loads(path.read_text())` needs the whole file as a string AND the whole object
graph at once. After the 2026-09-09 reload the Swiss corpus is 416 MB on disk (12,174
decisions averaging 45k characters), so loading all three sources that way peaks past
what an 8 GB machine has spare. The files are written with `indent=1`, which puts every
top-level record between a line that is exactly " {" and one that is " }" or " },", so
they can be parsed one record at a time.

    from corpus_io import load_records
    swiss = load_records("../data/swiss_parental_alienation.json")            # no text
    swiss = load_records("../data/swiss_parental_alienation.json", text=True) # with text

`text=False` drops `full_text` / `content` after parsing each record and keeps
`text_length`, which every record already carries — enough for counts, coverage and
distributions, and a fraction of the memory.
"""

import json

TEXT_FIELDS = ("full_text", "content")


def iter_records(path, text=False):
    """Yield one record at a time. Never holds more than a single record."""
    buf, inrec = [], False
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip("\n")
            if not inrec:
                if stripped.strip() == "{":
                    inrec, buf = True, [line]
            else:
                buf.append(line)
                if stripped in (" },", " }", "},", "}"):
                    rec = json.loads("".join(buf).rstrip().rstrip(","))
                    if not text:
                        for k in TEXT_FIELDS:
                            if k in rec:
                                rec[k] = ""
                    yield rec
                    inrec, buf = False, []


def load_records(path, text=False):
    return list(iter_records(path, text=text))
