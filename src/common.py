"""Shared definitions: paths, capability families, periods and next-generation definitions."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
DECISIONS = DATA / "decisions"
INTERIM = DATA / "interim"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
TAB = OUT / "tables"
for p in (INTERIM, FIG, TAB):
    p.mkdir(parents=True, exist_ok=True)

# Capability families (codebook, Fig. 1 of the paper)
FAM = {1: "Observability", 2: "Forecasting", 3: "Operational optimisation", 4: "Reliability and resilience",
       5: "DER and flexibility", 6: "Data and AI", 7: "Digital twin and simulation", 8: "Architecture",
       9: "Interoperability and standards", 10: "Cybersecurity", 11: "Operator support"}

ERAS = ["<=2009", "2010-19", "2020-26"]
ERA_LABELS = ["$\\leq$2009", "2010–2019", "2020–2026"]

MATURITY = ["concept", "simulation", "lab/hil testbed", "field pilot", "deployed in operation/product"]
FIELD = {"field pilot", "deployed in operation/product"}

# Next-generation definitions. "main" is the one used in the paper (Section 2.3);
# the others are the sensitivity variants.
NEXTGEN = {
    "main: >=1 of {5,6,7,9,10}": lambda L: any(f in L for f in (5, 6, 7, 9, 10)),
    "without family 9": lambda L: any(f in L for f in (5, 6, 7, 10)),
    ">=2 of {5,6,7,9,10}": lambda L: sum(f in L for f in (5, 6, 7, 9, 10)) >= 2,
}


def era(y):
    if pd.isna(y):
        return None
    y = int(y)
    return "<=2009" if y <= 2009 else ("2010-19" if y <= 2019 else "2020-26")


def parse_families(s):
    """'1;5;6' -> [1, 5, 6]. Accepts ';' or ',' separators."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return []
    parts = str(s).replace(",", ";").split(";")
    return sorted({int(x) for x in parts if x.strip().isdigit() and int(x) in FAM})


def read_table(path, **kw):
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str, **kw).fillna("")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", **kw)


def plot_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.spines.top": False,
                         "axes.spines.right": False})
    return plt


C1, C3 = "#2b5d8a", "#d98c2b"
