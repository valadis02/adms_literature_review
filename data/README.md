# Data

## data/raw/ — database exports (NOT published)

Put the exports here with these names; the scripts pick them up by prefix:

- `scopus_*.csv` — Scopus CSV export with "Citation information", "Bibliographical information" and "Abstract & keywords"
- `ieee_*.csv` — IEEE Xplore CSV export
- `q5_*.csv` — Scopus export of query Q5 (coverage check only; the different prefix keeps it out of the sample)

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
| `screening_llm.csv` | id, decision, code, families, reason | LLM (collected by step 3) |
| `verification.xlsx` | LLM columns + verified_decision, verified_code, verified_families, note | reviewer (from `verification_sheet.xlsx`, step 2) |
| `verification_changes.csv` | every row where the reviewer changed the LLM decision, code or families | script (step 4 summary) |
| `screening_final.csv` | id, decision, code, families, source (`llm`, `verified`, `changed`) | script (step 4 finalize) |
| `extraction.csv` | see `extraction/extraction_form.md` (71 full texts of the sample) | reviewer, form pre-filled by the LLM |
| `extraction_q5.csv` | same columns, for the six Q5 records read in full (not part of the 71) | reviewer, form pre-filled by the LLM |
| `platforms.csv` | platform, source URL, access date, family 1-11 coding | reviewer |

## data/interim/ — generated, not published
