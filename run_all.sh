#!/usr/bin/env bash
# Steps that need no human input, in order. Run from the repository root.
set -euo pipefail
python src/s01_merge_dedup.py
python src/s04_agreement.py finalize
python src/s05_abstract_mapping.py
python src/s07_fulltext_analysis.py
if python -c "import pandas as pd,sys; d=pd.read_csv('data/decisions/extraction.csv',dtype=str); sys.exit(0 if 'sample' in d and (d['sample']=='random').any() else 1)"; then
  python src/s07_fulltext_analysis.py --sample cited
  python src/s07_fulltext_analysis.py --sample random
fi
python src/s08_latex_tables.py
echo "Done. See outputs/."
