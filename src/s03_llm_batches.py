"""Step 3 - batches for the LLM screener and collection of its answers.

The LLM receives the same written criteria as the human (screening/criteria.md) and the prompt in
screening/llm_prompt.md. Each batch is a CSV of records; the LLM returns a CSV with
id,decision,code,families,reason for every id.

Usage
  python src/s03_llm_batches.py make --size 190     -> data/interim/batches/batch_*.csv + prompt per batch
  python src/s03_llm_batches.py collect             -> data/decisions/screening_llm.csv
                                                       (reads data/interim/llm_out/*.csv and checks completeness)
"""
import argparse

import pandas as pd

from common import DECISIONS, INTERIM, ROOT, read_table

COLS = ["id", "title", "year", "source", "doctype", "author_kw", "abstract"]
BATCH = INTERIM / "batches"
LLM_OUT = INTERIM / "llm_out"


def make(size):
    BATCH.mkdir(exist_ok=True)
    LLM_OUT.mkdir(exist_ok=True)
    rec = read_table(INTERIM / "records.csv")
    rec = rec[rec.meta_ok.str.lower() == "true"].sample(frac=1, random_state=7).reset_index(drop=True)
    template = (ROOT / "screening" / "llm_prompt.md").read_text(encoding="utf-8")
    # the prompt uses paths relative to data/interim/
    (INTERIM / "criteria.md").write_text((ROOT / "screening" / "criteria.md").read_text(encoding="utf-8"),
                                         encoding="utf-8")
    n = -(-len(rec) // size)
    for i in range(n):
        ch = rec.iloc[i * size:(i + 1) * size]
        ch[COLS].to_csv(BATCH / f"batch_{i + 1}.csv", index=False)
        prompt = template.replace("{BATCH_FILE}", f"batch_{i + 1}.csv").replace("{N}", str(len(ch))) \
                         .replace("{OUT_FILE}", f"llm_out/screen_{i + 1}.csv")
        (BATCH / f"prompt_{i + 1}.md").write_text(prompt, encoding="utf-8")
        print(f"batch {i + 1}: {len(ch)} records")


def collect():
    rec = read_table(INTERIM / "records.csv")
    expected = set(rec.loc[rec.meta_ok.str.lower() == "true", "id"])
    files = sorted(LLM_OUT.glob("*.csv"))
    if not files:
        raise SystemExit(f"No LLM outputs in {LLM_OUT}")
    df = pd.concat([read_table(f) for f in files], ignore_index=True)
    df["decision"] = df["decision"].str.lower().str.strip()
    dup = df[df.id.duplicated(keep=False)]
    missing = expected - set(df.id)
    extra = set(df.id) - expected
    bad = df[~df.decision.isin(["include", "exclude"])]
    print(f"rows {len(df)} | duplicates {len(dup)} | missing {len(missing)} | unknown ids {len(extra)} | "
          f"invalid decisions {len(bad)}")
    if missing:
        print("missing ids (first 20):", sorted(missing)[:20])
    df = df.drop_duplicates("id", keep="last")
    df[["id", "decision", "code", "families", "reason"]].to_csv(DECISIONS / "screening_llm.csv", index=False)
    print(df.decision.value_counts().to_dict(), "->", DECISIONS / "screening_llm.csv")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["make", "collect"])
    p.add_argument("--size", type=int, default=190)
    a = p.parse_args()
    make(a.size) if a.cmd == "make" else collect()


if __name__ == "__main__":
    main()
