"""
debug_echr.py
-------------
Inspects the exact return values of get_echr_extra to diagnose why
full texts come back empty.

Run: .venv/bin/python debug_echr.py
"""

import pprint
import requests
from bs4 import BeautifulSoup

import echr_extractor
from echr_extractor import get_echr, get_echr_extra

print(f"echr_extractor version: {echr_extractor.__version__}")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. get_echr_extra — inspect both return values
# ---------------------------------------------------------------------------
print("\n[1] Calling get_echr_extra(count=5) …")
df, full_texts = get_echr_extra(
    start_date="2024-01-01",
    end_date="2025-12-31",
    language=["ENG"],
    count=5,
    save_file="n",
    progress_bar=False,
    query_payload='"parental alienation"',
)

print(f"\n--- df ---")
print(f"  type   : {type(df)}")
if df is not False and df is not None:
    print(f"  shape  : {df.shape}")
    print(f"  columns: {list(df.columns)}")
    text_cols = [c for c in df.columns if any(k in c.lower() for k in ("text", "content", "body", "docname", "full"))]
    print(f"  text-like columns: {text_cols}")
    print(f"\n  First row (values truncated to 200 chars):")
    for k, v in df.iloc[0].to_dict().items():
        vs = str(v)
        print(f"    {k!r}: {vs[:200]!r}{'...' if len(vs) > 200 else ''}")
else:
    print("  df is False/None — metadata fetch failed")

print(f"\n--- full_texts ---")
print(f"  type   : {type(full_texts)}")

if isinstance(full_texts, dict):
    print(f"  length : {len(full_texts)}")
    print(f"  keys   : {list(full_texts.keys())[:5]}")
    if full_texts:
        first_k, first_v = next(iter(full_texts.items()))
        vs = str(first_v)
        print(f"  first item: key={first_k!r}, value={vs[:300]!r}{'...' if len(vs) > 300 else ''}")

elif isinstance(full_texts, list):
    print(f"  length : {len(full_texts)}")
    if full_texts:
        print(f"  first item type: {type(full_texts[0])}")
        item = full_texts[0]
        if isinstance(item, dict):
            print(f"  first item keys: {list(item.keys())}")
            for k, v in item.items():
                vs = str(v)
                print(f"    {k!r}: {vs[:300]!r}{'...' if len(vs) > 300 else ''}")
        else:
            print(f"  first item: {str(full_texts[0])[:300]}")
    else:
        print("  list is EMPTY — no full texts returned")

elif full_texts is False or full_texts is None:
    print("  full_texts is False/None")

else:
    print(f"  unexpected type: {type(full_texts)}")
    print(f"  repr: {repr(full_texts)[:300]}")

# ---------------------------------------------------------------------------
# 2. get_echr_extra with save_file='y' — does it behave differently?
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("[2] Calling get_echr_extra(count=3, save_file='n') …")
df2, full_texts2 = get_echr_extra(
    start_date="2024-01-01",
    end_date="2025-12-31",
    language=["ENG"],
    count=3,
    save_file="n",
    progress_bar=False,
    query_payload='"parental alienation"',
)
print(f"  full_texts2 type  : {type(full_texts2)}")
if isinstance(full_texts2, list):
    print(f"  full_texts2 length: {len(full_texts2)}")
    if full_texts2:
        print(f"  first item keys   : {list(full_texts2[0].keys()) if isinstance(full_texts2[0], dict) else 'not a dict'}")

# ---------------------------------------------------------------------------
# 3. Direct HUDOC fetch — does the URL work at all?
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("[3] Direct HUDOC full-text fetch …")

# Grab a real itemid from df (if available)
test_itemid = None
if df is not False and df is not None and len(df) > 0:
    test_itemid = df.iloc[0].get("itemid")
    print(f"  Using itemid from df: {test_itemid}")
else:
    test_itemid = "001-238568"   # known case: X and Others v. Slovenia
    print(f"  df unavailable, using hardcoded itemid: {test_itemid}")

base_url = "https://hudoc.echr.coe.int/app/conversion/docx/html/body?library=ECHR&id="
url = base_url + test_itemid

print(f"  GET {url}")
try:
    resp = requests.get(url, timeout=15)
    print(f"  status   : {resp.status_code}")
    print(f"  content-type: {resp.headers.get('content-type', 'N/A')}")
    print(f"  body length : {len(resp.text)} chars")
    if resp.status_code == 200 and len(resp.text) > 100:
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        print(f"  parsed text length: {len(text)} chars")
        print(f"  first 400 chars of text:\n{text[:400]!r}")
    else:
        print(f"  raw body (first 500 chars): {resp.text[:500]!r}")
except Exception as e:
    print(f"  FAILED: {e}")

# ---------------------------------------------------------------------------
# 4. Reproduce the library's 1-second timeout to show why it silently fails
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("[4] Reproducing library's 1-second timeout …")
try:
    resp_short = requests.get(url, timeout=1)
    print(f"  1s timeout: OK (status {resp_short.status_code}, {len(resp_short.text)} chars)")
except requests.exceptions.Timeout:
    print("  1s timeout: TIMED OUT — this is why full_texts is always empty!")
    print("  The library uses timeout=1 in ECHR_html_downloader.py:68")
    print("  All downloads silently fail and are 'retried' once with the same 1s timeout.")
except Exception as e:
    print(f"  1s timeout: error {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS SUMMARY")
print("=" * 60)
if isinstance(full_texts, list):
    print(f"  full_texts is a LIST (not dict) — scraper's isinstance(ft, dict) check is WRONG")
    print(f"  Length: {len(full_texts)}")
    if full_texts:
        item = full_texts[0]
        if isinstance(item, dict):
            print(f"  Each item has keys: {list(item.keys())}")
            print(f"  Note key is 'item_id' (not 'itemid') — lookup by 'itemid' will always miss!")
    else:
        print("  Empty list likely caused by 1-second timeout in ECHR_html_downloader.py")
