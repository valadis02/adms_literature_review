"""Step 4 - agreement between screeners and the final screening decisions.

Usage
  python src/s04_agreement.py llm        human (blind) vs LLM on the records both coded:
                                         confusion matrix, Cohen's kappa, LLM precision/recall for inclusion,
                                         agreement on exclusion codes and on capability families;
                                         writes data/decisions/disagreements.xlsx for resolution
  python src/s04_agreement.py retest     intra-rater agreement (screening_human vs screening_human_retest)
  python src/s04_agreement.py finalize   data/decisions/screening_final.csv:
                                         resolved disagreement > human decision > LLM decision

Inputs (data/decisions/)
  screening_human.xlsx|csv         id, decision, code, families      (human, blind)
  screening_human_retest.xlsx|csv  same columns                       (optional)
  screening_llm.csv                id, decision, code, families      (from s03)
  disagreements.xlsx               after resolution: column 'final_decision' (+ final_code, final_families)
"""
import argparse
import json

import pandas as pd

from common import DECISIONS, FAM, OUT, parse_families, read_table


def load(name):
    for ext in (".xlsx", ".csv"):
        p = DECISIONS / f"{name}{ext}"
        if p.exists():
            df = read_table(p)
            df["decision"] = df["decision"].str.lower().str.strip()
            df = df[df.decision.isin(["include", "exclude"])]
            return df[["id", "decision", "code", "families"]].drop_duplicates("id")
    raise SystemExit(f"{name}.xlsx/.csv not found in {DECISIONS}")


def kappa(a, b):
    a, b = pd.Series(a).reset_index(drop=True), pd.Series(b).reset_index(drop=True)
    labels = sorted(set(a) | set(b))
    po = (a == b).mean()
    pe = sum((a == l).mean() * (b == l).mean() for l in labels)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0, float(po)


def compare(h, o, name_h, name_o):
    m = h.merge(o, on="id", suffixes=("_h", "_o"))
    if m.empty:
        raise SystemExit("No records coded by both.")
    k, po = kappa(m.decision_h, m.decision_o)
    tp = int(((m.decision_h == "include") & (m.decision_o == "include")).sum())
    fp = int(((m.decision_h == "exclude") & (m.decision_o == "include")).sum())
    fn = int(((m.decision_h == "include") & (m.decision_o == "exclude")).sum())
    res = {
        "n": int(len(m)), "observed_agreement": round(po, 3), "cohens_kappa": round(k, 3),
        f"{name_o}_precision_include": round(tp / (tp + fp), 3) if tp + fp else None,
        f"{name_o}_recall_include": round(tp / (tp + fn), 3) if tp + fn else None,
        "confusion": pd.crosstab(m.decision_h.rename(name_h), m.decision_o.rename(name_o)).to_dict(),
    }
    both_ex = m[(m.decision_h == "exclude") & (m.decision_o == "exclude")]
    if len(both_ex):
        res["exclusion_code_agreement"] = round(float((both_ex.code_h.str.strip().str.upper()
                                                       == both_ex.code_o.str.strip().str.upper()).mean()), 3)
    both_in = m[(m.decision_h == "include") & (m.decision_o == "include")]
    if len(both_in):
        fh, fo = both_in.families_h.map(parse_families), both_in.families_o.map(parse_families)
        jac = [len(set(x) & set(y)) / len(set(x) | set(y)) if set(x) | set(y) else 1.0 for x, y in zip(fh, fo)]
        res["families_mean_jaccard"] = round(float(pd.Series(jac).mean()), 3)
        per = {}
        for f in FAM:
            k_f, _ = kappa(fh.map(lambda L: f in L), fo.map(lambda L: f in L))
            per[f"{f} {FAM[f]}"] = round(k_f, 3)
        res["families_kappa_per_family"] = per
    return res, m


def cmd_llm():
    res, m = compare(load("screening_human"), load("screening_llm"), "human", "llm")
    (OUT / "agreement_human_llm.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    dis = m[m.decision_h != m.decision_o].copy()
    for c in ("final_decision", "final_code", "final_families", "resolution_note"):
        dis[c] = ""
    dis.to_excel(DECISIONS / "disagreements.xlsx", index=False)
    print(f"{len(dis)} disagreements -> {DECISIONS / 'disagreements.xlsx'}")


def cmd_retest():
    res, _ = compare(load("screening_human"), load("screening_human_retest"), "first", "retest")
    res = {k.replace("retest_precision_include", "retest_vs_first_precision")
           .replace("retest_recall_include", "retest_vs_first_recall"): v for k, v in res.items()}
    (OUT / "agreement_intra_rater.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


def cmd_finalize():
    llm = load("screening_llm").set_index("id")
    try:
        hum = load("screening_human").set_index("id")
    except SystemExit:
        hum = pd.DataFrame(columns=["decision", "code", "families"])
    final = llm.copy()
    final["source"] = "llm"
    final.loc[hum.index.intersection(final.index), ["decision", "code", "families"]] = hum
    final.loc[hum.index.intersection(final.index), "source"] = "human"
    new = hum.index.difference(final.index)
    if len(new):
        final = pd.concat([final, hum.loc[new].assign(source="human")])
    dpath = DECISIONS / "disagreements.xlsx"
    if dpath.exists():
        d = read_table(dpath)
        d = d[d.final_decision.str.strip() != ""].set_index("id")
        for i, r in d.iterrows():
            final.loc[i, "decision"] = r.final_decision.lower().strip()
            final.loc[i, "code"] = r.final_code
            final.loc[i, "families"] = r.final_families
            final.loc[i, "source"] = "resolved"
    no_code = final[(final.decision == "exclude") & (final.code.str.strip() == "")]
    if len(no_code):
        print(f"WARNING: {len(no_code)} exclusions without an exclusion code, e.g. {list(no_code.index[:10])}")
    final.reset_index().rename(columns={"index": "id"}).to_csv(DECISIONS / "screening_final.csv", index=False)
    print(final.groupby(["source", "decision"]).size().to_string())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["llm", "retest", "finalize"])
    {"llm": cmd_llm, "retest": cmd_retest, "finalize": cmd_finalize}[p.parse_args().cmd]()


if __name__ == "__main__":
    main()
