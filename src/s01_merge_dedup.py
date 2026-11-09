"""Step 1 - merge database exports, remove duplicates, apply the metadata criteria.

Input : data/raw/scopus_*.csv and data/raw/ieee_*.csv (exports as downloaded)
Output: data/interim/records.csv      one row per unique record, with a stable id (R0001 / I0001)
        outputs/prisma_identification.json   numbers for the identification stage of the PRISMA diagram
        outputs/sample_stats.md        counts per year, source, document type, term group

Usage : python src/s01_merge_dedup.py
"""
import json
import re
import unicodedata
from collections import Counter

import pandas as pd

from common import INTERIM, OUT, RAW

# Column names in the Scopus export and their aliases in IEEE Xplore / Web of Science exports.
COLS = {
    "title": ["Title", "Article Title", "Document Title"],
    "year": ["Year", "Publication Year"],
    "doi": ["DOI"],
    "abstract": ["Abstract"],
    "author_kw": ["Author Keywords"],
    "index_kw": ["Index Keywords", "Keywords Plus", "IEEE Terms"],
    "source": ["Source title", "Source Title", "Publication Title"],
    "doctype": ["Document Type", "Document Identifier"],
    "language": ["Language of Original Document", "Language"],
    "authors": ["Authors", "Author Full Names"],
    "cited": ["Cited by", "Times Cited, All Databases", "Article Citation Count"],
    "link": ["Link", "PDF Link"],
}

# Term groups of the search strings (A = systems, B = DER/flexibility, C = AI/digital); used for statistics only.
GROUPS = {
    "A_systems": [r"advanced distribution management system", r"distribution management system", r"\bderms\b",
                  r"der management system", r"distributed energy resources? management system", r"\badms\b"],
    "B_flex": [r"flexib", r"demand response", r"congestion management", r"hosting capacity",
               r"operating envelope", r"der management", r"distributed energy resource"],
    "C_ai": [r"machine learning", r"artificial intelligence", r"deep learning", r"forecast", r"digital twin",
             r"multi-agent", r"state estimation"],
}

ALLOWED_DOCTYPES = r"article|conference|review|book chapter|journal|magazine"
EXCLUDED_DOCTYPES = r"standard|erratum|retracted|editorial|note|letter|front matter|conference review"


def pick(df, key):
    for c in COLS[key]:
        if c in df.columns:
            return df[c]
    return pd.Series([""] * len(df), index=df.index)


def load():
    frames = []
    for db, pattern in (("Scopus", "scopus_*.csv"), ("IEEE Xplore", "ieee_*.csv")):
        for p in sorted(RAW.glob(pattern)):
            raw = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
            df = pd.DataFrame({k: pick(raw, k) for k in COLS})
            df["db"], df["file"] = db, p.name
            frames.append(df)
            print(f"{p.name}: {len(df)} records")
    if not frames:
        raise SystemExit(f"No exports found in {RAW}. Expected scopus_*.csv and/or ieee_*.csv.")
    return pd.concat(frames, ignore_index=True)


def norm_title(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def add_keys(df):
    df = df.copy()
    df["doi_n"] = df["doi"].str.lower().str.strip().str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True)
    df["title_n"] = df["title"].map(norm_title)
    df["key"] = df["doi_n"].where(df["doi_n"] != "", "t:" + df["title_n"])
    return df


def dedup_within(df):
    """Duplicates inside one database (same DOI, or same normalised title)."""
    n0 = len(df)
    df = df.drop_duplicates("key").drop_duplicates("title_n")
    return df, n0 - len(df)


def tag(df):
    text = (df["title"] + " " + df["abstract"] + " " + df["author_kw"] + " " + df["index_kw"]).str.lower()
    for g, pats in GROUPS.items():
        df[g] = text.str.contains("|".join(pats), regex=True)
    df["is_review"] = df["doctype"].str.contains("review", case=False) | df["title"].str.contains(
        r"\breview\b|\bsurvey\b|state[- ]of[- ]the[- ]art", case=False, regex=True)
    return df


def metadata_criteria(df):
    dt = df["doctype"].str.lower()
    lang = df["language"].str.lower()
    reason = pd.Series("", index=df.index)
    bad_type = dt.str.contains(EXCLUDED_DOCTYPES, regex=True) | ~dt.str.contains(ALLOWED_DOCTYPES, regex=True)
    bad_type &= dt != ""  # an empty document type is left to the thematic screening
    reason[bad_type] = "document type"
    bad_lang = (lang != "") & ~lang.str.contains("english")
    reason[bad_lang & (reason == "")] = "language"
    df["meta_ok"] = reason == ""
    df["meta_reason"] = reason
    return df


def main():
    df = add_keys(load())
    identified = df.groupby("db").size().to_dict()

    parts, within = [], {}
    for db in ("Scopus", "IEEE Xplore"):
        sub, n = dedup_within(df[df.db == db])
        parts.append(sub)
        within[db] = n
    both = pd.concat(parts, ignore_index=True)  # Scopus first, so Scopus copies are kept
    n_before = len(both)
    both = both.drop_duplicates("key").drop_duplicates("title_n")
    across = n_before - len(both)

    both = metadata_criteria(tag(both.reset_index(drop=True)))
    prefix = both["db"].map({"Scopus": "R", "IEEE Xplore": "I"})
    both["id"] = prefix + both.groupby("db").cumcount().add(1).map("{:04d}".format)

    cols = ["id", "key", "db", "title", "year", "source", "doctype", "language", "authors", "doi", "cited",
            "abstract", "author_kw", "index_kw", "A_systems", "B_flex", "C_ai", "is_review", "meta_ok",
            "meta_reason", "file", "link"]
    both[cols].to_csv(INTERIM / "records.csv", index=False, encoding="utf-8")

    prisma = {
        "identified": identified,
        "identified_total": int(sum(identified.values())),
        "duplicates_within_db": within,
        "duplicates_across_db": int(across),
        "unique": int(len(both)),
        "removed_by_metadata": both.loc[~both.meta_ok, "meta_reason"].value_counts().to_dict(),
        "to_thematic_screening": int(both.meta_ok.sum()),
        "to_thematic_screening_by_db": both[both.meta_ok].db.value_counts().to_dict(),
    }
    (OUT / "prisma_identification.json").write_text(json.dumps(prisma, indent=2), encoding="utf-8")

    lines = ["# Sample statistics (unique records)", ""]
    for g in GROUPS:
        lines.append(f"- {g}: {int(both[g].sum())}")
    lines.append(f"- reviews (document type or title): {int(both.is_review.sum())}")
    for title, col in (("Per year", "year"), ("Top sources", "source"), ("Document type", "doctype")):
        lines += ["", f"## {title}", "", "| | count |", "|---|---|"]
        c = Counter(both[col])
        items = sorted(c.items()) if col == "year" else c.most_common(20)
        lines += [f"| {k or '(empty)'} | {v} |" for k, v in items]
    (OUT / "sample_stats.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(prisma, indent=2))


if __name__ == "__main__":
    main()
