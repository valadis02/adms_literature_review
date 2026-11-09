"""Synthetic data to test the whole pipeline without the real exports.

Writes fake exports and decision files into a copy of the data folder given as argument.
The numbers mean nothing; they only exercise the code paths.

Usage : python tests/make_synthetic_data.py <data_dir>
"""
import random
import sys
from pathlib import Path

import pandas as pd

random.seed(1)
D = Path(sys.argv[1])
(D / "raw").mkdir(parents=True, exist_ok=True)
(D / "decisions").mkdir(parents=True, exist_ok=True)

VENUES = ["IEEE Power and Energy Society General Meeting", "IET Conference Publications",
          "IEE Conference Publication", "IEEE Transactions on Power Systems", "Energies", "IEEE Access"]
MAT = ["concept", "simulation", "simulation", "simulation", "lab/HIL testbed", "field pilot",
       "deployed in operation/product"]


def rec(i, db):
    y = random.choice(range(1995, 2027))
    t = f"Distribution management system study number {i} on topic {random.randint(1, 50)}"
    return {"Title" if db == "s" else "Document Title": t,
            "Year" if db == "s" else "Publication Year": str(y),
            "DOI": f"10.9999/x.{i}" if random.random() > 0.1 else "",
            "Abstract": "We present an ADMS function for distribution networks with DER and forecasting.",
            "Author Keywords": "ADMS; DMS",
            "Source title" if db == "s" else "Publication Title": random.choice(VENUES),
            "Document Type" if db == "s" else "Document Identifier":
                random.choice(["Article", "Conference Paper", "Review", "Erratum"] if db == "s"
                              else ["IEEE Conferences", "IEEE Journals", "IEEE Standards"]),
            "Language of Original Document": random.choice(["English"] * 15 + ["Chinese"]) if db == "s" else "",
            "Authors": "A. Author; B. Author",
            "Cited by" if db == "s" else "Article Citation Count": str(random.randint(0, 200))}


scopus = [rec(i, "s") for i in range(400)]
scopus += scopus[:5]  # within-db duplicates
ieee = [rec(i, "i") for i in range(300, 520)]  # 100 overlap with Scopus
pd.DataFrame(scopus).to_csv(D / "raw" / "scopus_main.csv", index=False)
pd.DataFrame(ieee).to_csv(D / "raw" / "ieee_main.csv", index=False)
print("raw exports written")


def decisions(ids, flip=0.0):
    rows = []
    for i in ids:
        inc = random.random() < 0.65
        if random.random() < flip:
            inc = not inc
        fam = ";".join(sorted({str(random.randint(1, 11)) for _ in range(random.randint(1, 3))}, key=int))
        rows.append({"id": i, "decision": "include" if inc else "exclude",
                     "code": "" if inc else random.choice(["E1", "E2", "E3", "E3", "E5"]),
                     "families": fam if inc else "", "reason": "synthetic"})
    return pd.DataFrame(rows)


def after_s01():
    rec_ = pd.read_csv(D / "interim" / "records.csv", dtype=str, keep_default_na=False)
    ids = rec_.loc[rec_.meta_ok == "True", "id"].tolist()
    llm = decisions(ids)
    out = D / "interim" / "llm_out"
    out.mkdir(parents=True, exist_ok=True)
    llm.iloc[: len(llm) // 2].to_csv(out / "screen_1.csv", index=False)
    llm.iloc[len(llm) // 2:].to_csv(out / "screen_2.csv", index=False)
    random.seed(2)
    hum = decisions(ids[:200], flip=0.0)
    hum["decision"] = [d if random.random() > 0.08 else ("exclude" if d == "include" else "include")
                       for d in llm.set_index("id").loc[hum.id, "decision"]]
    hum.to_excel(D / "decisions" / "screening_human.xlsx", index=False)
    hum.iloc[:50].to_csv(D / "decisions" / "screening_human_retest.csv", index=False)
    print("decision files written")


def after_s06():
    ft = pd.concat([pd.read_csv(D / "interim" / f, dtype=str) for f in ("fulltext_cited.csv",
                                                                        "fulltext_random.csv")])
    inc = pd.read_csv(D / "interim" / "included.csv", dtype=str, keep_default_na=False).set_index("id")
    rows = []
    for _, r in ft.iterrows():
        unit = "review" if r.reason == "review" else random.choice(["function", "function", "system", "testbed"])
        rows.append({"id": r.id, "bibkey": f"Key_{r.id}", "year": str(int(float(inc.loc[r.id, "y"]))),
                     "sample": "random" if r.reason == "random" else "cited", "unit": unit,
                     "families": inc.loc[r.id, "families"],
                     "maturity": "" if unit == "review" else random.choice(MAT),
                     "maturity_by_family": "", "validation": "IEEE 13-bus test feeder",
                     "validation_label": "Test feeder", "data_inputs": random.choice(["SCADA; AMI", "AMI", "PMU"]),
                     "standards": random.choice(["CIM; IEC 61850", "none", "IEEE 2030.5"]),
                     "gap_themes": random.choice(["interoperability", "data/observability; field validation", ""]),
                     "capability_summary": "Synthetic capability with 5% & µPMU characters."})
    pd.DataFrame(rows).to_csv(D / "decisions" / "extraction.csv", index=False)
    print("extraction written")


if __name__ == "__main__" and len(sys.argv) > 2:
    {"after_s01": after_s01, "after_s06": after_s06}[sys.argv[2]]()
