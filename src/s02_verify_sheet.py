"""Step 2 - verification sheet for the reviewer.

The LLM screens every record first (step 3). The reviewer then checks all LLM inclusions and a
random share of the LLM exclusions (10% in the paper). The sheet shows the LLM decision next to
the record; for every row the reviewer fills in the verified decision.

Usage
  python src/s02_verify_sheet.py --frac 0.10
Output
  data/decisions/verification_sheet.xlsx   fill verified_decision (include/exclude), verified_code
                                           (E1-E5 for exclusions), verified_families (for inclusions)
                                           and, if the decision changes, a short note; then save it as
                                           data/decisions/verification.xlsx
"""
import argparse

import pandas as pd

from common import DECISIONS, INTERIM, ROOT, read_table

SEED = 2026
SHOW = ["id", "title", "year", "source", "doctype", "abstract", "author_kw"]
LLM = ["llm_decision", "llm_code", "llm_families", "llm_reason"]
FILL = ["verified_decision", "verified_code", "verified_families", "note"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frac", type=float, default=0.10, help="share of LLM exclusions to check")
    a = p.parse_args()

    rec = read_table(INTERIM / "records.csv")
    llm = read_table(DECISIONS / "screening_llm.csv")
    llm = llm.rename(columns={"decision": "llm_decision", "code": "llm_code", "families": "llm_families",
                              "reason": "llm_reason"})
    df = rec.merge(llm, on="id", how="inner")

    inc = df[df.llm_decision.str.lower() == "include"].assign(checked_because="all inclusions")
    exc = df[df.llm_decision.str.lower() == "exclude"]
    smp = exc.sample(frac=a.frac, random_state=SEED).assign(checked_because=f"random {a.frac:.0%} of exclusions")
    out = pd.concat([inc, smp])[SHOW + LLM + ["checked_because"]].sort_values("id")
    for c in FILL:
        out[c] = ""

    path = DECISIONS / "verification_sheet.xlsx"
    crit = (ROOT / "screening" / "criteria.md").read_text(encoding="utf-8").splitlines()
    with pd.ExcelWriter(path) as w:
        out.to_excel(w, index=False, sheet_name="verification")
        pd.DataFrame({"criteria (screening/criteria.md)": crit}).to_excel(w, index=False, sheet_name="criteria")
    print(f"{len(inc)} inclusions + {len(smp)} of {len(exc)} exclusions -> {path}")


if __name__ == "__main__":
    main()
