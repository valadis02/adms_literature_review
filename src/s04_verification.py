"""Step 4 - result of the verification and final screening decisions.

Usage
  python src/s04_verification.py summary    how many LLM decisions the reviewer changed, in which direction,
                                            and how often exclusion codes and families were corrected
                                            -> outputs/verification_summary.json
                                            -> data/decisions/verification_changes.csv (every changed row)
  python src/s04_verification.py finalize   data/decisions/screening_final.csv: the verified decision where the
                                            record was checked, the LLM decision otherwise

Inputs (data/decisions/)
  screening_llm.csv    id, decision, code, families, reason   (from step 3)
  verification.xlsx    the filled verification sheet           (from step 2)

There is no agreement statistic: the reviewer saw the LLM decision while checking it, so the check is a
verification, not an independent second screening.
"""
import argparse
import json

import pandas as pd

from common import DECISIONS, OUT, parse_families, read_table


def load_llm():
    d = read_table(DECISIONS / "screening_llm.csv")
    d["decision"] = d["decision"].str.lower().str.strip()
    return d[["id", "decision", "code", "families"]].drop_duplicates("id").set_index("id")


def load_verification():
    for ext in (".xlsx", ".csv"):
        p = DECISIONS / f"verification{ext}"
        if p.exists():
            v = read_table(p)
            v["verified_decision"] = v["verified_decision"].str.lower().str.strip()
            blank = v[~v.verified_decision.isin(["include", "exclude"])]
            if len(blank):
                raise SystemExit(f"{len(blank)} rows without a valid verified_decision, e.g. {list(blank.id[:10])}")
            return v.drop_duplicates("id").set_index("id")
    raise SystemExit(f"verification.xlsx/.csv not found in {DECISIONS}")


def cmd_summary():
    llm, v = load_llm(), load_verification()
    m = v.join(llm, how="left")
    changed = m[m.verified_decision != m.decision]
    inc_out = changed[changed.decision == "include"]
    exc_in = changed[changed.decision == "exclude"]
    kept_exc = m[(m.decision == "exclude") & (m.verified_decision == "exclude")]
    kept_inc = m[(m.decision == "include") & (m.verified_decision == "include")]
    code_fix = kept_exc[(kept_exc.verified_code.str.strip() != "")
                        & (kept_exc.verified_code.str.upper().str.strip() != kept_exc.code.str.upper().str.strip())]
    fam_fix = kept_inc[(kept_inc.verified_families.str.strip() != "")
                       & (kept_inc.verified_families.map(parse_families) != kept_inc.families.map(parse_families))]
    res = {
        "checked": int(len(m)),
        "checked_llm_inclusions": int((m.decision == "include").sum()),
        "checked_llm_exclusions": int((m.decision == "exclude").sum()),
        "llm_inclusions_reversed_to_exclude": int(len(inc_out)),
        "llm_exclusions_reversed_to_include": int(len(exc_in)),
        "reversal_rate_inclusions": round(len(inc_out) / max((m.decision == "include").sum(), 1), 3),
        "reversal_rate_exclusions_sample": round(len(exc_in) / max((m.decision == "exclude").sum(), 1), 3),
        "exclusion_code_corrected": int(len(code_fix)),
        "families_corrected": int(len(fam_fix)),
        "reversed_inclusions_by_new_code": inc_out.verified_code.str.upper().str.strip().value_counts().to_dict(),
        "reversed_exclusions_by_old_code": exc_in.code.str.upper().str.strip().value_counts().to_dict(),
    }
    (OUT / "verification_summary.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    cols = ["decision", "code", "families", "verified_decision", "verified_code", "verified_families", "note"]
    pd.concat([changed, code_fix, fam_fix])[cols].rename(columns={"decision": "llm_decision", "code": "llm_code",
                                                                  "families": "llm_families"}) \
        .reset_index().drop_duplicates("id").to_csv(DECISIONS / "verification_changes.csv", index=False)
    print(json.dumps(res, indent=2))


def cmd_finalize():
    llm = load_llm()
    final = llm.copy()
    final["source"] = "llm"
    try:
        v = load_verification()
    except SystemExit as e:
        print(f"WARNING: {e}; using LLM decisions only")
        v = None
    if v is not None:
        ids = v.index.intersection(final.index)
        for i in ids:
            r = v.loc[i]
            same = r.verified_decision == final.loc[i, "decision"]
            final.loc[i, "decision"] = r.verified_decision
            if r.verified_decision == "exclude":
                final.loc[i, "code"] = r.verified_code.strip() or (final.loc[i, "code"] if same else "")
                final.loc[i, "families"] = ""
            else:
                final.loc[i, "code"] = ""
                final.loc[i, "families"] = r.verified_families.strip() or (final.loc[i, "families"] if same else "")
            final.loc[i, "source"] = "verified" if same else "changed"
    no_code = final[(final.decision == "exclude") & (final.code.str.strip() == "")]
    if len(no_code):
        print(f"WARNING: {len(no_code)} exclusions without an exclusion code, e.g. {list(no_code.index[:10])}")
    no_fam = final[(final.decision == "include") & (final.families.str.strip() == "")]
    if len(no_fam):
        print(f"WARNING: {len(no_fam)} inclusions without families, e.g. {list(no_fam.index[:10])}")
    final.reset_index().rename(columns={"index": "id"}).to_csv(DECISIONS / "screening_final.csv", index=False)
    print(final.groupby(["source", "decision"]).size().to_string())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["summary", "finalize"])
    {"summary": cmd_summary, "finalize": cmd_finalize}[p.parse_args().cmd]()


if __name__ == "__main__":
    main()
