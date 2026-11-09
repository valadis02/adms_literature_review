"""Step 9 (optional) - check the DOIs of a BibTeX file against Crossref.

For every entry with a DOI, compares the title and year in the .bib with the Crossref record and lists
mismatches, unknown DOIs and entries without a DOI. Needs internet access.

Usage : python src/s09_check_references.py path/to/refs.bib
Output: outputs/reference_check.csv
"""
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

from common import OUT

UA = "adms-review-reference-check/1.0"


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"[{}\\]", "", s)).strip()


def entries(text):
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        f = {k.lower(): v.strip() for k, v in re.findall(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", body, re.M)}
        yield m.group(2).strip(), f


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["message"]


def main():
    text = open(sys.argv[1], encoding="utf-8").read()
    rows = []
    for key, f in entries(text):
        doi = f.get("doi", "")
        if not doi:
            rows.append([key, "", "no DOI", "", ""])
            continue
        try:
            msg = crossref(doi)
        except Exception as e:  # noqa: BLE001
            rows.append([key, doi, f"not found ({e.__class__.__name__})", "", ""])
            continue
        title = (msg.get("title") or [""])[0]
        year = str((msg.get("issued", {}).get("date-parts") or [[None]])[0][0])
        sim = SequenceMatcher(None, norm(f.get("title", "")), norm(title)).ratio()
        status = "ok"
        if sim < 0.85:
            status = "title mismatch"
        if f.get("year") and year != "None" and f["year"] != year:
            status += "; year mismatch"
        rows.append([key, doi, status, title, year])
        time.sleep(0.2)
    with open(OUT / "reference_check.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "doi", "status", "crossref_title", "crossref_year"])
        w.writerows(rows)
    bad = [r for r in rows if r[2] != "ok"]
    print(f"{len(rows)} entries, {len(bad)} to check -> {OUT / 'reference_check.csv'}")


if __name__ == "__main__":
    main()
