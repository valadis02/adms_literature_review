"""Step 6 - selection of the full-text subset.

Usage
  python src/s06_select_fulltext.py cited --k 3     all reviews + the k most cited records of each
                                                    family x period cell (the rule of the paper)
  python src/s06_select_fulltext.py random --k 2    stratified random sample of k records per cell, drawn
                                                    from records NOT already selected (robustness check)
Output
  data/interim/fulltext_cited.csv | fulltext_random.csv   id, reason, cell
"""
import argparse

import pandas as pd

from common import ERAS, FAM, INTERIM, parse_families, read_table

SEED = 2026


def cells(inc):
    inc = inc.copy()
    inc["fl"] = inc.families.map(parse_families)
    inc["cited_n"] = pd.to_numeric(inc.cited, errors="coerce").fillna(0)
    return inc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["cited", "random"])
    p.add_argument("--k", type=int, default=3)
    a = p.parse_args()
    inc = cells(read_table(INTERIM / "included.csv"))
    rows = []
    if a.mode == "cited":
        for i in inc[inc.is_review.str.lower() == "true"].id:
            rows.append((i, "review", ""))
        taken = {r[0] for r in rows}
        for e in ERAS:
            for f in FAM:
                cell = inc[(inc.era == e) & inc.fl.map(lambda L: f in L) & ~inc.id.isin(taken)]
                for i in cell.sort_values("cited_n", ascending=False).head(a.k).id:
                    rows.append((i, f"top-{a.k} cited", f"{f}|{e}"))
                    taken.add(i)
        out = INTERIM / "fulltext_cited.csv"
    else:
        prev = read_table(INTERIM / "fulltext_cited.csv")
        taken = set(prev.id)
        for e in ERAS:
            for f in FAM:
                cell = inc[(inc.era == e) & inc.fl.map(lambda L: f in L) & ~inc.id.isin(taken)
                           & (inc.is_review.str.lower() != "true")]
                for i in cell.sample(min(a.k, len(cell)), random_state=SEED).id:
                    rows.append((i, "random", f"{f}|{e}"))
                    taken.add(i)
        out = INTERIM / "fulltext_random.csv"
    df = pd.DataFrame(rows, columns=["id", "reason", "cell"])
    df.to_csv(out, index=False)
    print(df.reason.value_counts().to_dict(), "->", out)


if __name__ == "__main__":
    main()
