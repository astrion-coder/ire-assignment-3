# Benchmarking Approximate Nearest Neighbour Search (CS4.406, Assignment 3)

This repository benchmarks exact search, HNSW, IVF-Flat and IVF-PQ on SIFT-1M and GloVe-100. All four indexes come from FAISS; the recall@10 function, the timing harness, the plots and the tables are our own code. It also runs two experiments:
- **Part 3, scaling:** SIFT at 100K, 300K and 1M vectors.
- **Part 4, hard geometry:** seeded Gaussian noise added to SIFT.

## Setup
Python 3.12. With [uv](https://docs.astral.sh/uv/):

    uv sync

With pip:

    python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

When using uv, prefix the commands below with `uv run` (for example `uv run bash run_all.sh --quick`).

## Data
    bash run_all.sh --download        # or: python scripts/download_data.py

This downloads two files, about 1 GB together, into `data/`, which is not tracked in git:
- http://ann-benchmarks.com/sift-128-euclidean.hdf5
- http://ann-benchmarks.com/glove-100-angular.hdf5

`run_all.sh` also downloads them on its first run. If the download fails, fetch each file by hand (`curl -L -o data/<file> <url>`), then run `python scripts/download_data.py --check`.

## Running
    bash run_all.sh              # full run: every number, figure and table in the report
    bash run_all.sh --quick      # the same pipeline on small subsets (first 100,000 vectors)
    bash run_all.sh --only 05    # rerun one stage, here: redraw every figure and table from results.csv

- **Quick mode** took 4 minutes 7 seconds on the machine below. That was from a cold start (no cached ground truth, data already downloaded), with a browser open. The assignment's limit is 15 minutes on a laptop.
- **Full mode** writes to `results/` and `report/tables/`, and saves the executed notebooks, outputs included, in place.
- **Quick mode** writes everything to `results_quick/`, including the executed notebooks, so it never overwrites full results.
- **For steady timings,** close the browser and other busy programs before a full run. The timing thread is pinned to one core, but other programs can still share that core (see `design_note.md`).
- **On macOS,** quick mode runs, but the timing thread can't be pinned to a core, so its timings can be less steady. The machine record shows this: `timing_cpu` is empty and BLAS is Apple's Accelerate (see `design_note.md`).

The stages are notebooks, run in a fixed order:

| Stage | Notebook | What it does |
|---|---|---|
| 00 | `notebooks/00_core.ipynb` | Shared code and its tests: data, ground truth, recall@10, timing, index building, results file, figures and tables, hypothesis check |
| 01 | `notebooks/01_exact_baseline.ipynb` | Part 1: agreement with the stored neighbours, exact search one query at a time and in one batch |
| 02 | `notebooks/02_benchmark.ipynb` | Part 2: HNSW, IVF-Flat and IVF-PQ sweeps on both datasets |
| 03 | `notebooks/03_scaling.ipynb` | Part 3: scaling experiment (checks that its hypothesis is committed first) |
| 04 | `notebooks/04_hard_geometry.ipynb` | Part 4: seeded noise generator, its tests, and the experiment (checks that its hypothesis is committed first) |
| 05 | `notebooks/05_report_assets.ipynb` | Every figure and table, rebuilt from `results.csv` alone; machine and timing-quality tables |

Each feature cell is followed by its pytest cell (run with `ipytest`). A failing test stops `run_all.sh`. The packaging script has its own tests: `pytest tests/`.

## Measurement protocol
`design_note.md` records every choice that could bias a measurement, written down before it was applied.
- **Queries:** settings are tuned on queries 0–4,999 and reported on queries 5,000–9,999.
- **QPS:** one query at a time, on one thread pinned to one core, with warm-up queries first. Each setting is timed 3 times and the median is reported.
- **Recall@10:** ties at the 10th neighbour are not counted as mistakes. Ground truth is our own exact search, recomputed for every subset and every noise level.
- **Seeds:** all seeds are fixed. Multi-threaded HNSW builds are still not bit-for-bit reproducible.

## Outputs
- **`results/results.csv`:** one row for every benchmark run behind a number in the report. Each row also records the machine, library versions, query split, timings of every pass and distance computations per query.
- **`results/figures/`:** every figure, as PDF and PNG.
- **`report/tables/`:** every table, as Markdown and LaTeX, generated from `results.csv`.

## Verifying claims
Every number in the report comes from a table generated from `results/results.csv`. These commands check each kind of claim. In quick mode, read `results_quick/tables/` instead of `report/tables/`.

| Claim | One-command check |
|---|---|
| `--quick` finishes in under 15 minutes (4 min 7 s on the machine below) | `time bash run_all.sh --quick` |
| The two data files total about 1 GB | `du -ch data/*.hdf5` |
| Every figure and table is regenerated from `results.csv` alone | `bash run_all.sh --only 05` |
| Our exact neighbours agree with the stored ones (Part 1) | `cat report/tables/part1_agreement.md` |
| One batch is faster than one query at a time (Part 1) | `cat report/tables/part1_timing.md` |
| FAISS's bundled BLAS is a generic SSE3 (Prescott) build; numpy's uses AVX2 (Haswell) kernels | `cat report/tables/machine.md` |
| QPS of each index at recall 0.90 and 0.95 (Part 2) | `cat report/tables/part2_qps_at_recall.md` |
| Build time, size and bytes per vector at recall 0.95, and the RAM IVF-PQ keeps beside its serialised size (Part 2) | `cat report/tables/part2_cost_at_095.md` |
| The highest recall each index reaches (Part 2) | `cat report/tables/part2_best_recall.md` |
| How the cost of recall 0.95 grows with N; latency at 150K and 10M from the fit (Part 3, Q4) | `cat report/tables/part3_scaling.md report/tables/part3_growth.md` |
| The L3 cache is 24 MiB, so 30K SIFT vectors (15 MB) fit in it and 100K (51 MB) don't | `lscpu \| grep L3` |
| What noise does to relative contrast, recall and speed (Part 4) | `cat report/tables/part4_noise.md` |
| How steady the timings were (Q5) | `cat report/tables/run_quality.md` |
| One machine ran everything, and which library versions | `cat report/tables/machine.md` |
| The CPU has 6 two-thread performance cores (CPUs 0–11) and 8 efficiency cores (CPUs 12–19) | `cat /sys/devices/cpu_core/cpus /sys/devices/cpu_atom/cpus` |
| Each hypothesis was committed before its results | `git log --date=iso --format='%h %ad %s' -- hypothesis.md results/` |

## Building the report
Locally, with TeX Live (on Arch: `texlive-basic texlive-latex texlive-latexrecommended texlive-latexextra texlive-fontsrecommended texlive-binextra`):

    cd report && latexmk -pdf report.tex      # or build report/report.tex with LaTeX Workshop in VS Code

This writes `report/report.pdf`, which `scripts/package.py` puts at the top of the zip. On Overleaf instead (pdfLaTeX), this bundles `report.tex`, the tables and the figure PDFs into one zip to upload as a new project:

    mkdir -p dist && python -c "import zipfile, pathlib as p; z = zipfile.ZipFile('dist/overleaf_report.zip', 'w'); z.write('report/report.tex', 'report.tex'); [z.write(f, 'tables/' + f.name) for f in sorted(p.Path('report/tables').glob('*.tex'))]; [z.write(f, 'figures/' + f.name) for f in sorted(p.Path('results/figures').glob('*.pdf'))]; z.close()"

## Repository layout
| Path | Contents |
|---|---|
| `run_all.sh` | One-command reproduction (`--quick`, `--only NN`, `--download`) |
| `notebooks/` | The six stages above |
| `hypothesis.md` | Hypotheses for Parts 3 and 4, committed before those experiments ran |
| `design_note.md` | Measurement choices, optimisations and findings, in the order they were made |
| `results/` | `results.csv` and `figures/` from the full run |
| `report/tables/` | Tables generated from `results.csv` |
| `report/report.tex` | LaTeX source of the report; it includes the generated tables and figures |
| `scripts/download_data.py` | Downloads and checks the two datasets |
| `scripts/package.py` | Builds the submission zip: `python scripts/package.py --roll <ROLLNUMBER>` |
| `tests/` | Tests for the packaging script |

## Machine and library versions
Every row of `results.csv` records these; `report/tables/machine.md` lists every value found. Development and the quick-mode timing above used:

| Field | Value |
|---|---|
| CPU | 13th Gen Intel Core i5-13500 (6 performance cores with 2 threads each, 8 efficiency cores) |
| RAM | 15.3 GiB |
| OS | Arch Linux, kernel 7.2.10 |
| Python | 3.12.15 |
| Libraries | faiss-cpu 1.15.1, numpy 2.5.4, h5py 3.16.0, pandas 3.1.0, matplotlib 3.11.2 (all pinned in `requirements.txt`) |
| Timing | thread pinned to CPU 2 (a performance core); builds use 12 threads |
