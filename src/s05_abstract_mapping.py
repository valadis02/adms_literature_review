"""Step 5 - abstract-level mapping of the included records (Figs. 4-6, next-generation shares).

Input : data/interim/records.csv, data/decisions/screening_final.csv
Output: outputs/figures/per_year.pdf, sources.pdf, family_era.pdf
        outputs/numbers_abstract.json   screening counts, exclusion codes, family shares,
                                        next-generation share per period (definition of the paper)
        outputs/nextgen_sensitivity.csv only with --sensitivity (alternative definitions, not in the paper)

Usage : python src/s05_abstract_mapping.py [--sensitivity]
"""
import argparse
import json
import re

import pandas as pd

from common import C1, C3, DECISIONS, ERA_LABELS, ERAS, FAM, FIG, INTERIM, NEXTGEN, NEXTGEN_VARIANTS, OUT, era, \
    parse_families, plot_style, read_table

VENUE_ALIASES = {  # same series under different names in the exports
    r"^iet conference (proceedings|publications)|^iee conference publication": "IET/IEE Conference Publications",
    r"^ieee power (and|&) energy society general meeting|^ieee pes general meeting": "IEEE PES General Meeting",
    r"^ieee transactions on power systems": "IEEE Trans. Power Syst.",
    r"^ieee transactions on smart grid": "IEEE Trans. Smart Grid",
    r"^ieee transactions on power delivery": "IEEE Trans. Power Deliv.",
    r"^international journal of electrical power": "Int. J. Electr. Power Energy Syst.",
    r"^electric power systems research": "Electr. Power Syst. Res.",
    r"innovative smart grid technologies": "IEEE PES ISGT",
    r"universities power engineering": "UPEC",
}


def venue(s):
    s = str(s).strip()
    for pat, name in VENUE_ALIASES.items():
        if re.search(pat, s, re.I):
            return name
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r",? ?\d{4}.*$", "", s)
    return s if len(s) <= 48 else s[:46].rstrip() + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensitivity", action="store_true", help="also compute the alternative definitions")
    args = ap.parse_args()
    plt = plot_style()
    rec = read_table(INTERIM / "records.csv")
    fin = read_table(DECISIONS / "screening_final.csv")
    num = {"screened": int(len(fin)),
           "included": int((fin.decision == "include").sum()),
           "excluded_by_code": fin.loc[fin.decision == "exclude", "code"].str.upper().str.strip()
                                  .value_counts().to_dict(),
           "decision_source": {f"{s}|{d}": int(n) for (s, d), n in fin.groupby(["source", "decision"]).size()
                               .items()} if "source" in fin else {}}

    inc = rec.merge(fin[fin.decision == "include"][["id", "families"]], on="id")
    inc["y"] = pd.to_numeric(inc["year"], errors="coerce")
    inc["era"] = inc["y"].map(era)
    inc["fl"] = inc["families"].map(parse_families)
    num["included_by_db"] = inc.db.value_counts().to_dict()
    num["included_by_era"] = inc.era.value_counts().reindex(ERAS).fillna(0).astype(int).to_dict()
    num["years_outside_1989_2026"] = inc.loc[(inc.y < 1989) | (inc.y > 2026), "y"].dropna().astype(int).tolist()
    dt = inc.doctype.str.lower()
    conf = dt.str.contains("conference")
    jour = dt.str.contains("article|journal|review|magazine") & ~conf
    num["doctype"] = {"conference": int(conf.sum()), "journal_or_review": int(jour.sum()),
                      "other (e.g. book chapter)": int((~conf & ~jour).sum())}
    num["no_family_coded"] = int((inc.fl.map(len) == 0).sum())

    # family share per period
    rows = []
    for e in ERAS:
        sub = inc[inc.era == e]
        for f in FAM:
            rows.append((f, e, 100 * sub.fl.map(lambda L: f in L).mean() if len(sub) else 0))
    share = pd.DataFrame(rows, columns=["f", "era", "pct"]).pivot(index="f", columns="era", values="pct")[ERAS]
    num["family_share_pct"] = share.round(1).to_dict()

    # next-generation share per period (main definition; variants only with --sensitivity)
    defs = dict(NEXTGEN, **NEXTGEN_VARIANTS) if args.sensitivity else NEXTGEN
    sens = []
    for name, rule in defs.items():
        row = {"definition": name}
        for e in ERAS:
            sub = inc[inc.era == e]
            row[e] = round(100 * sub.fl.map(rule).mean(), 1) if len(sub) else None
        sens.append(row)
    sens = pd.DataFrame(sens)
    if args.sensitivity:
        sens.to_csv(OUT / "nextgen_sensitivity.csv", index=False)
    num["nextgen_share_pct"] = sens.set_index("definition").to_dict(orient="index")

    # Fig. 4: records per year and database
    yc = inc[(inc.y >= 1989) & (inc.y <= 2026)].groupby(["y", "db"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(6.5, 2.4))
    s = yc.get("Scopus", pd.Series(0, index=yc.index))
    ax.bar(yc.index, s, color=C1, label="Scopus")
    if "IEEE Xplore" in yc:
        ax.bar(yc.index, yc["IEEE Xplore"], bottom=s, color=C3, label="IEEE Xplore (additional)")
    ax.axvspan(2019.5, 2026.5, color="#eeeeee", zorder=0)
    ax.set_ylabel("Included records")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "per_year.pdf"); plt.close(fig)

    # Fig. 5: top venues (aliases merged)
    top = inc.source.map(venue)
    top = top[top != ""].value_counts().head(12)
    num["top_venues"] = top.to_dict()
    top = top[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    ax.barh(top.index, top.values, color=C1)
    for i, v in enumerate(top.values):
        ax.text(v + 0.3, i, str(v), va="center", fontsize=7)
    ax.set_xlabel("Included records")
    fig.tight_layout(); fig.savefig(FIG / "sources.pdf"); plt.close(fig)

    # Fig. 6: family share heatmap
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.imshow(share.values, cmap="Blues", aspect="auto", vmin=0, vmax=60)
    ax.set_xticks(range(3)); ax.set_xticklabels(ERA_LABELS)
    ax.set_yticks(range(len(FAM))); ax.set_yticklabels([f"{f} {FAM[f]}" for f in share.index])
    for i in range(len(FAM)):
        for j in range(3):
            v = share.values[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=7, color="white" if v > 35 else "black")
    ns = [int((inc.era == e).sum()) for e in ERAS]
    ax.set_title("Share of included records per period (n = " + ", ".join(map(str, ns)) + ")", fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "family_era.pdf"); plt.close(fig)

    inc[["id", "db", "y", "era", "source", "doctype", "cited", "families", "is_review"]].to_csv(
        INTERIM / "included.csv", index=False)
    (OUT / "numbers_abstract.json").write_text(json.dumps(num, indent=2, default=str), encoding="utf-8")
    print(json.dumps(num, indent=2, default=str))


if __name__ == "__main__":
    main()
