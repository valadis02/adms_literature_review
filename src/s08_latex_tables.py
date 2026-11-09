"""Step 8 - LaTeX tables of the full-text studies (Tables 4 and 6 of the paper, and the reviews table).

Input : data/decisions/extraction.csv (column 'bibkey' = the citation key in the paper's .bib)
Output: outputs/tables/function_studies.tex, system_studies.tex, reviews_set.tex

Usage : python src/s08_latex_tables.py
"""
import pandas as pd

from common import DECISIONS, TAB, parse_families, read_table

MAT = {"concept": "Concept", "simulation": "Sim.", "lab/hil testbed": "Lab/HIL", "field pilot": "Pilot",
       "deployed in operation/product": "Deployed"}
REP = [("\\", ""), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("$", "\\$"), ("~", "$\\sim$"),
       ("Δ", "$\\Delta$"), ("µ", "$\\mu$"), ("μ", "$\\mu$"), ("≥", "$\\geq$"), ("≤", "$\\leq$"),
       ("→", "$\\rightarrow$"), ("×", "$\\times$"), ("–", "--"), ("—", "---"), ("‘", "`"), ("’", "'"),
       ("“", "``"), ("”", "''"), ("±", "$\\pm$"), ("^", "\\^{}")]


def esc(s):
    s = str(s)
    for a, b in REP:
        s = s.replace(a, b)
    return s


def longtable(df, caption, label, path, with_maturity=True):
    if with_maturity:
        spec, head = r"@{}p{1.1cm}p{0.7cm}p{1.3cm}p{8.6cm}p{1.6cm}p{1.2cm}@{}", \
            r"Ref. & Year & Families & Capability provided to the DMS (as stated by the authors) & Validation & Maturity\\"
    else:
        spec, head = r"@{}p{1.1cm}p{0.7cm}p{1.6cm}p{11.2cm}@{}", r"Ref. & Year & Families & Scope (as stated)\\"
    lines = [r"\begin{small}", r"\setlength{\tabcolsep}{3pt}", rf"\begin{{longtable}}{{{spec}}}",
             rf"\caption{{{caption}}}\label{{{label}}}\\", r"\toprule", head, r"\midrule\endfirsthead",
             r"\toprule", head, r"\midrule\endhead", r"\bottomrule\endfoot"]
    for _, r in df.iterrows():
        cells = [f"\\cite{{{r.bibkey}}}", str(r.year), ",".join(map(str, r.fl)), esc(r.capability_summary)]
        if with_maturity:
            cells += [esc(r.validation_label), MAT.get(r.maturity.lower(), r.maturity)]
        lines.append(" & ".join(cells) + r"\\")
    lines += [r"\end{longtable}", r"\end{small}"]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(df)} rows -> {path}")


def main():
    ex = read_table(DECISIONS / "extraction.csv")
    ex["fl"] = ex.families.map(parse_families)
    if "bibkey" not in ex or (ex.bibkey == "").any():
        ex["bibkey"] = ex.get("bibkey", "").where(ex.get("bibkey", "") != "", ex.id)
    if "validation_label" not in ex:
        ex["validation_label"] = ex.validation
    ex = ex.sort_values(["year", "id"])
    longtable(ex[ex.unit == "function"], "Function-level studies analysed in full text (one capability developed "
              "for a DMS, ADMS or DERMS). Families refer to Fig.~1.", "tab:function", TAB / "function_studies.tex")
    longtable(ex[ex.unit.isin(["system", "testbed"])], "System- and test-bed-level studies analysed in full text.",
              "tab:system", TAB / "system_studies.tex")
    longtable(ex[ex.unit == "review"], "Reviews retrieved in the database search and analysed in full text.",
              "tab:revset", TAB / "reviews_set.tex", with_maturity=False)


if __name__ == "__main__":
    main()
