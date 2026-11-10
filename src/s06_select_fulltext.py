"""Step 6 - selection of the full-text subset, and the Q5 coverage check.

Usage
  python src/s06_select_fulltext.py cited --k 3 --db Scopus
        all reviews + the k most cited records of each family x period cell, from Scopus records only
        (the first selection of the paper: 91 records)
  python src/s06_select_fulltext.py cited --k 3 --keep data/interim/fulltext_cited.csv
        repeats the selection on all included records (Scopus + IEEE Xplore) and ADDS the records that now
        enter the top k of their cell, without removing any record already selected (3 records in the paper)
  python src/s06_select_fulltext.py q5
        Q5 coverage check: overlap of the Q5 export with the Q1 records, system names in Q5 titles/abstracts/
        keywords, Q5 records per year, and the six Q5 records read in full (4 most cited, 2 most recent)
  python src/s06_select_fulltext.py random --k 2
        optional stratified random sample from records not already selected. Not used in the paper.

Output
  data/interim/fulltext_cited.csv | fulltext_random.csv   id, reason, cell
  data/interim/q5_fulltext.csv, outputs/numbers_q5.json
"""
import argparse
import json

import pandas as pd

from common import ERAS, FAM, INTERIM, OUT, RAW, parse_families, read_table

SEED = 2026


def cells(inc):
    inc = inc.copy()
    inc["fl"] = inc.families.map(parse_families)
    inc["cited_n"] = pd.to_numeric(inc.cited, errors="coerce").fillna(0)
    return inc


def select_cited(inc, k):
    rows = [(i, "review", "") for i in inc[inc.is_review.str.lower() == "true"].id]
    taken = {r[0] for r in rows}
    for e in ERAS:
        for f in FAM:
            cell = inc[(inc.era == e) & inc.fl.map(lambda L: f in L) & ~inc.id.isin(taken)]
            for i in cell.sort_values("cited_n", ascending=False).head(k).id:
                rows.append((i, f"top-{k} cited", f"{f}|{e}"))
                taken.add(i)
    return pd.DataFrame(rows, columns=["id", "reason", "cell"])


def cmd_cited(a, inc):
    out = INTERIM / "fulltext_cited.csv"
    if a.keep:
        prev = read_table(a.keep)
        new = select_cited(inc, a.k)
        add = new[~new.id.isin(prev.id)].assign(reason=lambda d: d.reason + " (added, all databases)")
        df = pd.concat([prev, add], ignore_index=True)
        print(f"kept {len(prev)}, added {len(add)}: {list(add.id)}")
    else:
        sub = inc[inc.db == a.db] if a.db else inc
        df = select_cited(sub, a.k)
    df.to_csv(out, index=False)
    print(df.reason.value_counts().to_dict(), "->", out)


def cmd_random(a, inc):
    taken = set(read_table(INTERIM / "fulltext_cited.csv").id)
    rows = []
    for e in ERAS:
        for f in FAM:
            cell = inc[(inc.era == e) & inc.fl.map(lambda L: f in L) & ~inc.id.isin(taken)
                       & (inc.is_review.str.lower() != "true")]
            for i in cell.sample(min(a.k, len(cell)), random_state=SEED).id:
                rows.append((i, "random", f"{f}|{e}"))
                taken.add(i)
    out = INTERIM / "fulltext_random.csv"
    pd.DataFrame(rows, columns=["id", "reason", "cell"]).to_csv(out, index=False)
    print(len(rows), "random records ->", out)


def cmd_q5():
    from s01_merge_dedup import COLS, GROUPS, add_keys, pick
    files = sorted(RAW.glob("q5_*.csv"))
    if not files:
        raise SystemExit(f"No Q5 export in {RAW} (expected q5_*.csv; not scopus_*, so that it stays out of the sample)")
    q5 = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig") for p in files])
    q5 = add_keys(pd.DataFrame({k: pick(q5, k) for k in COLS})).drop_duplicates("key")
    rec = read_table(INTERIM / "records.csv")
    rec = add_keys(rec) if "title_n" not in rec else rec
    overlap = q5[q5.key.isin(rec.key) | q5.title_n.isin(rec.title_n)]
    text = (q5.title + " " + q5.abstract + " " + q5.author_kw + " " + q5.index_kw).str.lower()
    names = text.str.contains("|".join(GROUPS["A_systems"]), regex=True)
    q5["cited_n"] = pd.to_numeric(q5.cited, errors="coerce").fillna(0)
    q5["y"] = pd.to_numeric(q5.year, errors="coerce")
    top = q5.sort_values("cited_n", ascending=False).head(4).assign(reason="most cited")
    recent = q5[~q5.key.isin(top.key)].sort_values(["y", "cited_n"], ascending=False).head(2) \
        .assign(reason="most recent")
    pick6 = pd.concat([top, recent])[["reason", "title", "year", "doi", "cited"]]
    pick6.to_csv(INTERIM / "q5_fulltext.csv", index=False)
    num = {"q5_records": int(len(q5)), "overlap_with_q1_records": int(len(overlap)),
           "q5_with_system_name": int(names.sum()),
           "per_year": q5.y.dropna().astype(int).value_counts().sort_index().to_dict()}
    (OUT / "numbers_q5.json").write_text(json.dumps(num, indent=2, default=str), encoding="utf-8")
    print(json.dumps(num, indent=2, default=str))
    print(pick6.to_string(index=False, max_colwidth=70))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["cited", "random", "q5"])
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--db", choices=["Scopus", "IEEE Xplore"], help="cited: restrict to one database")
    p.add_argument("--keep", help="cited: earlier selection to extend without removing records")
    a = p.parse_args()
    if a.mode == "q5":
        cmd_q5()
        return
    inc = cells(read_table(INTERIM / "included.csv"))
    {"cited": cmd_cited, "random": cmd_random}[a.mode](a, inc)


if __name__ == "__main__":
    main()
