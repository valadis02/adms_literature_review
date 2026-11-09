# Data

## data/raw/ — database exports (NOT published)

Put the exports here with these names; the scripts pick them up by prefix:

- `scopus_*.csv` — Scopus CSV export with "Citation information", "Bibliographical information" and "Abstract & keywords"
- `ieee_*.csv` — IEEE Xplore CSV export

Scopus and IEEE Xplore terms of use do not allow redistribution of full exports (abstracts in particular).
Keep `data/raw/` out of the public repository (it is in `.gitignore`). What is published instead is
`data/decisions/`, which identifies every record by id, DOI and title, so that anyone with database access
can rebuild the sample.

Before publishing, generate the public record list:

```
python -c "import pandas as pd; d=pd.read_csv('data/interim/records.csv'); d[['id','db','doi','title','year','source','doctype','meta_ok','meta_reason']].to_csv('data/decisions/records_public.csv', index=False)"
```

## data/decisions/ — published

| File | Columns | Who fills it |
|---|---|---|
| `records_public.csv` | id, db, doi, title, year, source, doctype, meta_ok, meta_reason | script |
| `screening_human.xlsx` | id, decision, code, families, note | human reviewer (from `human_sheet_*.xlsx`) |
| `screening_human_retest.xlsx` | same | human reviewer, after >= 2 weeks |
| `screening_llm.csv` | id, decision, code, families, reason | LLM (collected by step 3) |
| `disagreements.xlsx` | ... + final_decision, final_code, final_families, resolution_note | human reviewer |
| `screening_final.csv` | id, decision, code, families, source | script (step 4 finalize) |
| `sample_strata.csv` | id, stratum | script (step 2 sample) |
| `extraction.csv` | see `extraction/extraction_form.md` | human reviewer |
| `platforms.csv` | platform, source URL, access date, family 1-11 coding | human reviewer |

## data/interim/ — generated, not published
