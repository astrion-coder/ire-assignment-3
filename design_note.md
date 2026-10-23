# Design note

Measurement choices and optimisations, written down **before** they are applied (CLAUDE.md, Minor Note 3). Anything here that could bias a number is a candidate for report question 5.

## 2026-10-23: protocol fixed before any code runs

### Machine
- Intel i5-13500 desktop, 15 GB RAM. The CPU is hybrid: P-cores are CPUs 0–11 (6 cores × 2 threads), E-cores are CPUs 12–19.
- At planning time the frequency governor was `powersave` with EPP `balance_performance`, and turbo was on. The governor is recorded with every run.

### Query timing (QPS)
- QPS is measured one query at a time on a single thread. FAISS is set to `omp_set_num_threads(1)` and BLAS to one thread via `threadpoolctl`.
- The timing thread is pinned to CPU 2 with `os.sched_setaffinity`, a P-core. On a hybrid CPU, an unpinned single thread can land on an E-core or migrate mid-run, which would mix two different speeds into one number. CPU 0 is avoided because it takes more interrupts. The CPU can be overridden with `ANN_TIMING_CPU`, and pinning is skipped where unsupported.
- Queries are converted to contiguous float32 and sliced before the timed loop, so no conversion is timed. Time comes from `time.perf_counter()` around the whole loop.
- Untimed warm-up queries run before each measured setting, so caches and CPU frequency settle first.
- Each setting is timed 3 times and the median QPS is reported. The raw times go into `results.csv`.

### Builds
- Builds use 12 threads (the P-core threads), and that count is recorded.
- Build time is the wall-clock time of train + add, measured once per configuration. A single measurement is noisier than a median; this is a known limitation (Q5).
- Index size is `len(faiss.serialize_index(index))`, and bytes per vector is that size divided by the number of vectors. Index files are never written to the repo.

### Recall@10
- Distances of the found ids and of the true 10th neighbour are recomputed in float64 from the float32 vectors. This avoids the cancellation error of FAISS's ‖x‖² + ‖q‖² − 2x·q form.
- A found id is correct if its distance is ≤ the true 10th distance × (1 + small relative tolerance). Ties at rank 10 therefore don't count as mistakes.
- Id `-1` (FAISS padding) counts as a miss, and duplicate ids count once.

### Ground truth
- Ground truth is our own exact FAISS search (`IndexFlatL2`, top 100). It runs batched and multi-threaded because it is not a timed measurement, and it is cached in `cache/`.
- It is recomputed for every subset (`--quick`, Part 3 sizes) and every generated variant (Part 4). The HDF5 `neighbors` are used only for the Part 1 agreement check.
- GloVe base vectors and queries are L2-normalised (zero-norm rows are left at zero), and L2 is used for everything.

### Query halves
- Tuning uses queries 0–4,999 and reporting uses 5,000–9,999. Quick mode uses 0–999 and 5,000–5,999.
- Everything chosen is chosen on the tuning half: build configurations, each index's Pareto front, the operating points at recall 0.90 and 0.95, and where a sweep stops. Reported numbers are what those choices achieve on the reporting half, even if that lands just under the target.

### Optimisations (cost savings; none changes how a query is timed)
- **Exact search, timed one query at a time, uses queries 5,000–5,999 in full mode, not all 5,000 reporting queries.** Exact recall is 1 by construction, so only the timing matters, and a 1M-vector scan per query is the slowest thing we time.
- **A sweep stops at the first search setting whose tuning-half recall reaches 0.995.** Larger settings only cost time and cannot change any operating point at 0.90 or 0.95.
