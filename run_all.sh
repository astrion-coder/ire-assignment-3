#!/usr/bin/env bash
# One-command reproduction for CS4.406 Assignment 3.
#   bash run_all.sh              full run: regenerates every number, figure and table in the report
#   bash run_all.sh --quick      the same pipeline on small subsets (e.g. the first 100,000 vectors)
#   bash run_all.sh --only 02    run one stage (notebook number), e.g. after fixing it
#   bash run_all.sh --download   only download and check the datasets
set -euo pipefail

cd "$(dirname "$0")"
export ANN_ROOT="$PWD"
export ANN_MODE=full
ONLY=""
DOWNLOAD_ONLY=0
PYTHON="${PYTHON:-python}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quick) ANN_MODE=quick ;;
        --only) ONLY="${2:?--only needs a stage number, e.g. 02}"; shift ;;
        --download) DOWNLOAD_ONLY=1 ;;
        -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
        *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
    esac
    shift
done

"$PYTHON" scripts/download_data.py
[[ $DOWNLOAD_ONLY -eq 1 ]] && exit 0

# Fixed order: 00_core holds the shared code and its tests; 05 rebuilds figures and tables from results.csv.
STAGES=(00_core 01_exact_baseline 02_benchmark 03_scaling 04_hard_geometry 05_report_assets)

# Full runs keep the executed notebooks (outputs included) in place; quick runs write copies elsewhere.
QUICK_NOTEBOOKS=results_quick/notebooks
[[ $ANN_MODE == quick ]] && mkdir -p "$QUICK_NOTEBOOKS"

for stage in "${STAGES[@]}"; do
    [[ -n $ONLY && $stage != "$ONLY"* ]] && continue
    notebook="notebooks/$stage.ipynb"
    [[ -f $notebook ]] || { echo "missing $notebook" >&2; exit 1; }
    echo "=== [$ANN_MODE] $stage  $(date +%H:%M:%S) ==="
    if [[ $ANN_MODE == full ]]; then
        "$PYTHON" -m jupyter nbconvert --to notebook --execute --inplace \
            --ExecutePreprocessor.timeout=-1 "$notebook"
    else
        "$PYTHON" -m jupyter nbconvert --to notebook --execute \
            --ExecutePreprocessor.timeout=-1 --output-dir "$QUICK_NOTEBOOKS" "$notebook"
    fi
done
echo "=== [$ANN_MODE] done  $(date +%H:%M:%S) ==="
