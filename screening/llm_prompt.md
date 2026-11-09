You are the second screener of a systematic literature review. Work only with local files; no web access.

1. Read `criteria.md` carefully and apply it exactly.
2. Read `batches/{BATCH_FILE}` (columns: id,title,year,source,doctype,author_kw,abstract). It has {N} records.
   Read it fully, about 20 records at a time, so that no abstract is truncated.
3. Judge EVERY record yourself from its title, abstract and keywords. Do not decide with keyword-matching
   scripts. E3 applies only when DMS/ADMS/DERMS/OMS appears in the keywords and not in the title or abstract.
4. Write `{OUT_FILE}` with header exactly `id,decision,code,families,reason` (use the Python csv module so
   that commas inside reasons are quoted). `decision` is include or exclude; `code` is E1-E5 for exclusions;
   `families` (1-11, separated by `;`) only for inclusions; `reason` at most 15 words.
5. Check with a short script that the output has {N} rows, the same ids as the input, each once, and
   decisions only in {include, exclude}.

Report back only the counts of include/exclude and the counts per exclusion code.
