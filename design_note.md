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

## 2026-10-23: core notebook (`00_core.ipynb`), choices fixed before it first runs
- **The timed loop writes ids as it goes.** Inside the loop, each query's ids are written into a preallocated array (FAISS `search(..., D=, I=)`), and those ids are what recall is computed from. The loop does the same work for every index, so the overhead is equal across indexes. Taking ids from the timed calls themselves also avoids a subtle mismatch: a separate batched search could rank near-tied IVF centroids differently from single-query calls.
- **Warm-up queries are the first 200 of the set being measured.** They run untimed before the timed passes, and the same queries are timed again later. Exact search scans everything anyway; for the indexes, warming 200 of 5,000 queries is a small effect, the same for all of them.
- **Part 1's multi-threaded batch timing is not pinned.** It uses 12 FAISS/BLAS threads. Pinning the main thread does not move OpenMP worker threads that already exist, so those threads may run on E-cores. The thread count is recorded.
- **Ground-truth caches are keyed by a fingerprint of the data** (shape plus a sample of rows), so a changed subset or noise level can never reuse a stale file.
- **Defaults:** k-means seeds are set explicitly (`cp.seed` and, for IVF-PQ, `pq.cp.seed` = 42). FAISS HNSW's level generator uses FAISS's fixed internal seed. Multi-threaded HNSW insertion is still not bit-for-bit reproducible.

## 2026-10-23: Part 1 (`01_exact_baseline.ipynb`), choices fixed before it first runs
- **The agreement check always uses the full base set.** It compares our exact neighbours with the stored ones, and the stored neighbours are only valid for the full set. Full mode checks all 10,000 queries; quick mode checks the first 1,000 (0–999, tuning half; nothing is tuned from them).
- **Distance units.** FAISS returns squared L2. Before comparing distances, they are converted to the units the files are believed to store: plain L2 for SIFT, and 1 − cos for GloVe, which on unit vectors equals squared L2 ÷ 2. The notebook reports the largest difference, so this belief is checked, not assumed.
- **Timing sets.** One query at a time uses queries 5,000–5,999 (see the optimisation above). One batch uses all reporting-half queries, timed twice: pinned to one thread, and with 12 unpinned threads. QPS is compared per query, so the different set sizes don't matter.
- **Finding from the first quick run, and a check added because of it.** FAISS's single-thread batch search was no faster than one query at a time on GloVe (1.0×), while SIFT gained 2.9×. A scratch diagnostic (100K vectors, 1,000 queries) showed the cause is the dimension, not the data:
  - SIFT cut to 100 dims was as slow as GloVe (1.29 vs 1.30 ms per query).
  - GloVe zero-padded to 128 dims was as fast as SIFT (0.64 ms).
  - Shuffling the order of the base vectors, or scaling them, changed nothing.
  - numpy's own BLAS computes the d = 100 matrix product quickly, so the slow path is probably in the BLAS bundled with faiss-cpu.

  Part 1 now also times the single-thread batch with SIFT cut to its first 100 dims and GloVe zero-padded to 128 (`variant` column). The report can then cite this from `results.csv`. The padded and truncated copies are used for this timing only, never for recall. This is a Q5 candidate: batched exact-search speed depends on a library kernel's handling of the dimension, not just on N × d.
