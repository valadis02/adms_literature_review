#!/usr/bin/env bash
# Steps that need no human input, in order. Run from the repository root.
set -euo pipefail
python src/s01_merge_dedup.py
python src/s04_verification.py summary
python src/s04_verification.py finalize
python src/s05_abstract_mapping.py
if ls data/raw/q5_*.csv >/dev/null 2>&1; then
  python src/s06_select_fulltext.py q5
fi
python src/s07_fulltext_analysis.py
python src/s08_latex_tables.py
echo "Done. See outputs/."
