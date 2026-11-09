"""Step 2 - screening sheets for the human reviewer (blind to the LLM decisions).

The sheet never contains the LLM's decision, so the human judgement is independent.
Rows are shuffled so that the order carries no information.

Usage
  python src/s02_human_sheet.py all                 every record that passed the metadata criteria
  python src/s02_human_sheet.py sample --n 200      stratified random sample (by LLM decision/code if available)
  python src/s02_human_sheet.py retest --n 50       re-screening of already coded records (intra-rater check;
                                                    run 2-3 weeks after the first pass, without looking at it)
Output
  data/decisions/human_sheet_<mode>.xlsx   fill columns decision / code / families, then save it as
                                           data/decisions/screening_human.xlsx (or ..._retest.xlsx)
"""
import argparse

import pandas as pd

from common import DECISIONS, INTERIM, ROOT, read_table

SEED = 2026
SHOW = ["id", "title", "year", "source", "doctype", "abstract", "author_kw"]
FILL = ["decision", "code", "families", "note"]


def criteria_frame():
    text = (ROOT / "screening" / "criteria.md").read_text(encoding="utf-8")
    return pd.DataFrame({"criteria (screening/criteria.md)": text.splitlines()})


def write(df, name):
    out = df[SHOW].copy()
    for c in FILL:
        out[c] = ""
    path = DECISIONS / f"human_sheet_{name}.xlsx"
    with pd.ExcelWriter(path) as w:
        out.to_excel(w, index=False, sheet_name="screening")
        criteria_frame().to_excel(w, index=False, sheet_name="criteria")
    print(f"{len(out)} records -> {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["all", "sample", "retest"])
    p.add_argument("--n", type=int, default=200)
    a = p.parse_args()

    rec = read_table(INTERIM / "records.csv")
    rec = rec[rec.meta_ok.str.lower() == "true"]

    if a.mode == "all":
        write(rec.sample(frac=1, random_state=SEED), "all")
        return

    if a.mode == "sample":
        llm_path = DECISIONS / "screening_llm.csv"
        if llm_path.exists():
            llm = read_table(llm_path)[["id", "decision", "code"]]
            df = rec.merge(llm, on="id", how="inner")
            # strata: include, and each exclusion code; at least 10 per stratum, the rest proportional
            df["stratum"] = df["decision"].where(df["decision"] == "include", "exclude:" + df["code"])
            sizes = df["stratum"].value_counts()
            alloc = (sizes / sizes.sum() * a.n).round().clip(lower=10).astype(int)
            alloc = pd.concat([alloc, sizes], axis=1).min(axis=1)
            parts = [df[df.stratum == s].sample(int(k), random_state=SEED) for s, k in alloc.items()]
            smp = pd.concat(parts)
            smp[["id", "stratum"]].to_csv(DECISIONS / "sample_strata.csv", index=False)
            print("strata:", alloc.to_dict())
        else:
            smp = rec.sample(min(a.n, len(rec)), random_state=SEED)
        write(smp.sample(frac=1, random_state=SEED), "sample")
        return

    # retest: records the human already coded, in a new order, without the earlier answers
    hum = read_table(DECISIONS / "screening_human.xlsx")
    done = rec[rec.id.isin(hum.loc[hum.decision != "", "id"])]
    write(done.sample(min(a.n, len(done)), random_state=SEED + 1), "retest")


if __name__ == "__main__":
    main()
