"""Step 7 - full-text analysis: maturity per family (Fig. 7), data inputs, standards, stated gaps,
triangulation table (Table 9).

Input : data/decisions/extraction.csv (one row per full text; columns in extraction/extraction_form.md)
        outputs/numbers_abstract.json (from step 5, for the triangulation table)
Output: outputs/figures/maturity.pdf
        outputs/numbers_fulltext.json
        outputs/maturity_per_family.csv     n, counts per level, field count and share (study level and,
                                            if maturity_by_family is filled, capability level)
        outputs/triangulation.csv

Usage : python src/s07_fulltext_analysis.py [--sample cited|random|all]
"""
import argparse
import json

import pandas as pd

from common import C3, DECISIONS, FAM, FIELD, FIG, MATURITY, OUT, parse_families, plot_style, read_table

DATA_TERMS = {"SCADA": "scada", "AMI/smart meter": "ami|smart meter", "GIS": r"\bgis\b", "PMU/µPMU": "pmu",
              "DER telemetry": "der telemetry|inverter", "weather": "weather"}
STD_TERMS = {"CIM (IEC 61968/61970)": r"\bcim\b|61968|61970", "IEC 61850": "61850", "DNP3": "dnp3|1815",
             "IEEE 1547": "1547", "IEEE 2030.5": r"2030\.5", "OpenADR": "openadr", "IEC 62351": "62351",
             "ICCP/TASE.2": "iccp|tase"}


def parse_mbf(s):
    """'6:field pilot;10:simulation' -> {6: 'field pilot', 10: 'simulation'}"""
    out = {}
    for part in str(s).split(";"):
        if ":" in part:
            f, m = part.split(":", 1)
            if f.strip().isdigit():
                out[int(f)] = m.strip().lower()
    return out


def count_terms(series, terms):
    t = series.fillna("").str.lower()
    return {k: int(t.str.contains(p, regex=True).sum()) for k, p in terms.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="all", choices=["all", "cited", "random"])
    a = ap.parse_args()
    plt = plot_style()

    ex = read_table(DECISIONS / "extraction.csv")
    if "sample" in ex and a.sample != "all":
        ex = ex[ex["sample"] == a.sample]
    ex["fl"] = ex.families.map(parse_families)
    ex["maturity"] = ex.maturity.str.lower().str.strip()
    bad = ex.loc[(ex.unit != "review") & ~ex.maturity.isin(MATURITY), ["id", "maturity"]]
    if len(bad):
        print("WARNING: unknown maturity labels:\n", bad.to_string(index=False))

    num = {"fulltexts": int(len(ex)), "unit": ex.unit.value_counts().to_dict()}
    nr = ex[ex.unit != "review"].copy()
    num["non_review"] = int(len(nr))
    num["maturity_overall"] = nr.maturity.value_counts().reindex(MATURITY).fillna(0).astype(int).to_dict()
    has_mbf = "maturity_by_family" in nr and (nr.maturity_by_family.str.strip() != "").any()
    nr["mbf"] = nr.maturity_by_family.map(parse_mbf) if "maturity_by_family" in nr else [{}] * len(nr)

    rows = []
    for f in FAM:
        s = nr[nr.fl.map(lambda L: f in L)]
        c = s.maturity.value_counts()
        row = {"family": f"{f} {FAM[f]}", "n": len(s), **{m: int(c.get(m, 0)) for m in MATURITY}}
        row["field_n"] = int(sum(c.get(m, 0) for m in FIELD))
        row["field_pct"] = round(100 * row["field_n"] / len(s), 0) if len(s) else None
        if has_mbf:  # capability level: the level reached for this family, else the study level
            lv = s.apply(lambda r: r.mbf.get(f, r.maturity), axis=1)
            row["field_n_capability"] = int(lv.isin(FIELD).sum())
            row["field_pct_capability"] = round(100 * row["field_n_capability"] / len(s), 0) if len(s) else None
        rows.append(row)
    mat = pd.DataFrame(rows)
    mat.to_csv(OUT / "maturity_per_family.csv", index=False)
    num["maturity_per_family"] = mat.set_index("family").to_dict(orient="index")

    # Fig. 7
    fig, ax = plt.subplots(figsize=(6.5, 2.9))
    colors = ["#cfd8e3", "#9bbcd9", "#5b8db8", C3, "#8a4b10"]
    labels = ["Concept", "Simulation", "Lab / HIL", "Field pilot", "Deployed"]
    ylab = [f"{r.family} (n={r.n})" for r in mat.itertuples()]
    left = pd.Series(0, index=mat.index)
    for m, col, lab in zip(MATURITY, colors, labels):
        ax.barh(ylab, mat[m], left=left, color=col, label=lab)
        left += mat[m]
    ax.invert_yaxis()
    ax.set_xlabel("Non-review full-text studies addressing the family")
    ax.legend(frameon=False, ncol=5, loc="lower center", bbox_to_anchor=(0.4, 1.0), fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "maturity.pdf"); plt.close(fig)

    num["data_inputs"] = count_terms(ex.data_inputs, DATA_TERMS)
    num["standards"] = count_terms(ex.standards, STD_TERMS)
    num["no_standard_named"] = int((ex.standards.str.strip().str.lower().isin(["", "none", "not stated"])).sum())
    gaps = ex.gap_themes.str.split(";").explode().str.strip()
    num["studies_with_gap"] = int((ex.gap_themes.str.strip() != "").sum())
    num["gap_themes"] = gaps[gaps != ""].value_counts().to_dict()

    # Table 9: growth (abstract level) + field share + stated gaps
    ab_path = OUT / "numbers_abstract.json"
    if ab_path.exists():
        ab = json.loads(ab_path.read_text())
        share = ab["family_share_pct"]
        tri = []
        for f in FAM:
            r = mat[mat.family == f"{f} {FAM[f]}"].iloc[0]
            tri.append({"family": f"{f} {FAM[f]}", "share_2010_19": share["2010-19"][str(f)]
                        if str(f) in share["2010-19"] else share["2010-19"].get(f),
                        "share_2020_26": share["2020-26"][str(f)] if str(f) in share["2020-26"]
                        else share["2020-26"].get(f),
                        "field": f"{r.field_n}/{r.n}", "field_pct": r.field_pct})
        pd.DataFrame(tri).to_csv(OUT / "triangulation.csv", index=False)

    suffix = "" if a.sample == "all" else f"_{a.sample}"
    (OUT / f"numbers_fulltext{suffix}.json").write_text(json.dumps(num, indent=2, default=str), encoding="utf-8")
    print(json.dumps(num, indent=2, default=str))


if __name__ == "__main__":
    main()
