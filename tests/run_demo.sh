#!/usr/bin/env bash
# Runs the whole pipeline on synthetic data in a temporary copy of the repository.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
cp -r "$REPO/src" "$REPO/screening" "$TMP/"
mkdir -p "$TMP/data" "$TMP/outputs"
cd "$TMP"
cp "$REPO/tests/make_synthetic_data.py" .
python make_synthetic_data.py data
python src/s01_merge_dedup.py > /dev/null
python src/s03_llm_batches.py make --size 150 > /dev/null
python make_synthetic_data.py data after_s01
python src/s03_llm_batches.py collect
python src/s02_human_sheet.py sample --n 120
python src/s04_agreement.py llm > /dev/null
python src/s04_agreement.py retest > /dev/null
python src/s04_agreement.py finalize
python src/s05_abstract_mapping.py > /dev/null
python src/s06_select_fulltext.py cited --k 3
python src/s06_select_fulltext.py random --k 2
python make_synthetic_data.py data after_s06
python src/s07_fulltext_analysis.py > /dev/null
python src/s07_fulltext_analysis.py --sample random > /dev/null
python src/s08_latex_tables.py
echo "Demo OK: outputs in $TMP/outputs"
ls "$TMP/outputs" "$TMP/outputs/figures" "$TMP/outputs/tables"
