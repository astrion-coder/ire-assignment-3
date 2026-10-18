# Reference Guide for Claude Code

This document contains the necessary information needed for Claude Code to help with the assignment efficiently.

## Important Files and Folders
1. `assignments/` - This is the folder that contains all the assignment questions. Any time a question is asked, this is the first folder you will visit to try and figure out which assignment i am talking about. Usually I'll refer the specific assignment by filename to you.
2. `assignments/Assignment 3 Benchmarking Approximate Nearest Neighbour Search.pdf` - the current assignment (CS4.406, individual, due **25 October 2026, 23:59 IST** on Moodle). It is the source of truth: where `PLAN.md` or this file disagrees with it, the PDF wins.
3. Deliverable names fixed by the assignment (never rename them): `run_all.sh`, `README.md`, `requirements.txt`, `hypothesis.md`, `results/results.csv`, `results/figures/`, `ai_log/ai_statement.md`, `report.pdf`.
4. `design_note` - the optimisation log from Minor Note 3 (create it with the first optimisation).
5. `PLAN.md` - the step-by-step plan for this assignment. It is not loaded automatically, so read it before starting a task.

## Tech Stack
The programming language used for all kinds of code is Python. The local environment is only going to be used for generating code and verifying minor correctness and other minor issues. If any model training is necessary, it should be created in a separate notebook and instructions on how to run it in kaggle should be present in the notebook.

Testing framework is pytest and for package management, uv is used.

How this applies to Assignment 3:
- There is no model training. IVF/PQ training (k-means, codebooks) is part of building an index and counts toward its build time, so it runs inside the benchmark, never in a separate notebook or on another machine.
- The heavy step is the full benchmark, `bash run_all.sh`. The ground rules require every reported number to come from **one machine**, with its specs and library versions recorded. If the full run happens on Kaggle, use a thin Kaggle notebook (with the Kaggle instructions in it, as above) that sets up the code and data and calls `bash run_all.sh`, and do the whole full run in one session (or confirm the CPU model is identical across sessions), because Kaggle may hand out different hardware per session.
- `bash run_all.sh --quick` must finish in under 15 minutes on a laptop, so time it on the local machine.
- The submission needs a `requirements.txt`. Pin versions in it and regenerate it from uv whenever dependencies change, e.g. `uv export --format requirements-txt --no-hashes -o requirements.txt`.

## Coding Guidelines
1. After any new feature is added in a cell, always add tests for that in the next cell. For example:

    ```python
    // New python feature
    ```

    ```python
    // Tests
    ```

2. Most code should be written in jupyter notebooks.

3. `bash run_all.sh` has to regenerate every number, figure and table with no human involved, so every notebook must run top to bottom headlessly (e.g. `jupyter nbconvert --to notebook --execute`), in a fixed order, with relative paths only. Quick mode comes from an environment variable or parameter, never from editing a cell.

4. The next-cell tests are pytest tests (e.g. `ipytest` inside the notebook; ask before installing it). The assignment requires unit tests for our recall@10 function, including a tie at the 10th neighbour. Also test that the Part 4 generator returns identical data for the same seed.

5. Write the shared pieces once and reuse them in every part: data loading, ground truth, recall@10, the timing harness, the `results.csv` writer and the plotting code, so every part measures the same way.

## Minor Notes
1. If you run a command and the output says "Module Not Found", do not install it. Give me the command and I will install. You are not allowed to install anything without my consent.

2. Anytime you make a numeric claim like in SPEC.md you said "~7–12s for the full MIND val/test population (65,173 users) at the matmul step, ~19–40s for top-K selection — under two minutes total, and proportionally faster for EB-NeRD", also write the commands in README.md that would allow to verify these claims in one command.
    - For this assignment the README must explain `bash run_all.sh` and `bash run_all.sh --quick` anyway. Add a one-command check for every other claim, e.g. `time bash run_all.sh --quick` for the 15-minute limit.
    - Every number in the report must come from output that `run_all.sh` regenerates and must trace back to a row of `results/results.csv`. Never estimate a number, quote one from memory, or copy one from anywhere else.

3. Anytime any optimization gets applied, it must be written to design_note first, so you don't lose context.
    - An optimisation must never change what is measured: QPS stays one query at a time, single-threaded, median of repeats. Only untimed work (loading, ground truth, caching) may be sped up.
    - Also record in design_note every choice that could bias a measurement (thread settings, warm-up, caching, what counts as build time). Report question 5 draws on it.

## Assignment 3 standing rules
These apply in every session; `PLAN.md` and the PDF have the details.
- Before running a Part 3 or Part 4 experiment on its real data (any scale, including `--quick`), check that `git log -- hypothesis.md` shows its hypothesis committed. If it doesn't, stop and tell me.
- `.git` ships with the submission: never commit datasets, HDF5 files, generated vectors, ground-truth caches or index files, and never rewrite history (`commit --amend`, rebase, force-push).
- Whenever you create or edit a source file, record it in `ai_log/ai_statement.md` as AI-generated or AI-assisted.
- Never tune anything on queries 5,000–9,999; they are only for reported numbers.
- Recall@10, timing code and plots are our own code; FAISS and hnswlib are only for the indexes; never use the ann-benchmarks framework.
