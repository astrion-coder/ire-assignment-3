# Benchmarking Approximate Nearest Neighbour Search (CS4.406, Assignment 3)

This repository benchmarks exact search, HNSW, IVF-Flat and IVF-PQ (all from FAISS) on SIFT-1M and GloVe-100. It also runs a scaling experiment (Part 3) and a hard-geometry experiment on SIFT with added noise (Part 4). The recall@10 function, the timing harness and the plots are our own code.

> Status: scaffold. Sections marked *(Step 8)* or *(Step 9)* are filled in once the pipeline is complete.

## Setup
Python 3.12. With [uv](https://docs.astral.sh/uv/):

    uv sync

With pip:

    python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

When using uv, prefix the commands below with `uv run`.

## Data
    bash run_all.sh --download        # or: python scripts/download_data.py

This downloads two files into `data/`, which is not tracked in git:
- http://ann-benchmarks.com/sift-128-euclidean.hdf5
- http://ann-benchmarks.com/glove-100-angular.hdf5

If the download fails, fetch each file by hand (`curl -L -o data/<file> <url>`), then run `python scripts/download_data.py --check`.

## Running
    bash run_all.sh              # full run: every number, figure and table in the report
    bash run_all.sh --quick      # same pipeline on small subsets (first 100,000 vectors); required to take under 15 minutes on a laptop
    bash run_all.sh --only 02    # rerun a single stage

The notebooks in `notebooks/` run in a fixed order (00 to 05). A full run writes to `results/` and saves the executed notebooks in place. A quick run writes to `results_quick/` instead, so it never overwrites full results.

## Outputs
- `results/results.csv`: one row for every benchmark run behind a number in the report, including the machine and library versions.
- `results/figures/`: all figures.
- `report/tables/`: all tables (Markdown and LaTeX), generated from `results.csv`.

## Repository layout
| Path | Contents |
|---|---|
| `notebooks/00_core.ipynb` | Shared code and its tests: data loading, ground truth, recall@10, timing, results writer, plots |
| `notebooks/01_exact_baseline.ipynb` | Part 1: exact baseline |
| `notebooks/02_benchmark.ipynb` | Part 2: HNSW, IVF-Flat, IVF-PQ on both datasets |
| `notebooks/03_scaling.ipynb` | Part 3: scaling experiment |
| `notebooks/04_hard_geometry.ipynb` | Part 4: data generator and experiment |
| `notebooks/05_report_assets.ipynb` | Figures and tables from `results.csv` |
| `hypothesis.md` | Hypotheses for Parts 3 and 4, committed before those experiments ran |
| `design_note.md` | Measurement choices and optimisations |
| `scripts/` | Data download and submission packaging |

## Verifying claims *(Step 8)*
| Claim | One-command check |
|---|---|
| `--quick` finishes in under 15 minutes | `time bash run_all.sh --quick` |

## Machine and library versions *(Step 9)*
These are recorded automatically in every row of `results.csv` and summarised here after the full run.
