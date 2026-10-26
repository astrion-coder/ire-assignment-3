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

## 2026-10-23: Part 2 (`02_benchmark.ipynb`), choices fixed before it first runs
- **Grids.** Full mode:
  - HNSW: M ∈ {8, 16, 32}, efConstruction 200, efSearch from 10 up (the exact grid is in the "Finer search grids" entry below).
  - IVF-Flat: nlist ∈ {1024, 4096}.
  - IVF-PQ: nlist 4096, m ∈ {16, 32, 64} for SIFT and {20, 50} for GloVe, 8 bits per sub-vector (FAISS's default), so m bytes of code per vector.
  - Both IVF indexes sweep nprobe from 1 to 256, skipping values above nlist.

  Quick mode builds one setting per index, on the first 100,000 vectors.
- **Best trade-off curve.** Each index's curve is the Pareto front over all its build settings and search values, chosen on the tune half. It's plotted at the report-half recall and QPS of those same configurations, so a point can sit slightly off a monotone curve.
- **Operating points at 0.90 and 0.95.** The fastest configuration of that index whose tune-half recall reaches the target. Its report-half recall and QPS are reported even if the recall lands just under the target. If no configuration reaches the target on the tune half, the QPS table says so. The cost table then shows the configuration with the highest tune-half recall and marks it.
- **The exact baseline is Part 1's one-at-a-time row.** Same protocol, queries 5,000–5,999, not re-measured in Part 2. The plotting code asserts that Part 1 and Part 2 timed the same base set.
- **Index size is what FAISS serialises:** vectors or PQ codes, ids (8 bytes per vector in IVF lists), centroids, PQ codebooks, HNSW links.
- **IVF-PQ needs more RAM than its serialised size.** FAISS's default for residual PQ with L2 keeps a precomputed distance table of nlist × m × 256 float32, which speeds up search. FAISS rebuilds it on load instead of storing it, so it's recorded separately as `search_table_bytes`. At nlist 4096 and m 64 that's about 268 MB, against 64 MB of codes. Q2 candidate: PQ saves less memory in RAM than on disk.
- **IVF k-means trains on the base vectors themselves**, since the files have no separate training set. FAISS's default samples at most 256 points per centroid, with a fixed seed: nlist 1024 trains on 262,144 vectors, nlist 4096 on all of them. Training is part of build time.
- **IVF-PQ runs without re-ranking**, so quantisation error caps its recall. Re-ranking is Part 3's Compression option, which we didn't choose.
- **The coarse quantiser is inside the timed call.** Each IVF query first finds its nprobe nearest centroids by a flat scan, and that scan is timed with the rest.
- **Figures and tables are drawn from `results.csv` alone**, by functions in `00_core.ipynb`. `05_report_assets.ipynb` calls the same functions, so a figure can be redrawn without re-running any benchmark.
- **Finer search grids, changed after the first quick run.** The first grids doubled efSearch and nprobe at each step. That's too coarse for operating points: on quick-mode SIFT, HNSW's tune-half recall jumped from 0.88 (efSearch 16) to 0.96 (efSearch 32), so 0.90 and 0.95 got the same setting, and QPS at 0.90 was understated by the size of the overshoot. Grids now step by about 1.33–1.5×:
  - efSearch: 10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768. Quick mode stops at 512, so GloVe's HNSW sweep still clears 0.95 when the multi-threaded build comes out slightly worse.
  - nprobe: 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256. Quick mode stops at 128 (nlist 256).

  This was seen on tune-half recall, so no reporting query informed it. The extra settings are mostly cheap low values; the largest settings dominate sweep time.

## 2026-10-23: distance counts (all parts), fixed before they first run
- **Every timed row records `distances_per_query`, at no cost to the timing.** FAISS always updates global counters during search, whether or not anyone reads them. `time_one_at_a_time` resets them after the warm-up and reads them after the timed passes, so no work enters the timed loop. What is counted:
  - **HNSW:** FAISS's own count (`hnsw_stats.ndis`), every distance its search computes on all levels.
  - **IVF:** the list entries scanned (`indexIVF_stats.ndis`) plus nlist for the coarse quantiser, which FAISS doesn't count there. For IVF-PQ an entry is a table-lookup distance, much cheaper than a full one, so its counts aren't comparable with the others' in cost.
  - **Exact search:** N.
- These counts explain QPS by mechanism. For example, Part 3 can show whether a query's work grows like N, √N or log N.

## 2026-10-23: Part 3 (`03_scaling.ipynb`), choices fixed before it first runs
- **Sizes are prefixes of the SIFT base set:** the first 100K, 300K and 1M vectors (quick mode: 10K, 30K, 100K). The queries are the same at every size; ground truth is recomputed for each size.
- **HNSW** uses M 16 and efConstruction 200 at every size.
- **IVF-Flat uses nlist = round(4√N):** 1,265, 2,191 and 4,000 (quick mode: 400, 693, 1,265). This makes the average list size (N / nlist = √N / 4) grow exactly like √N, which the hypothesis assumes. Powers of two (1024, 2048, 4096) would only grow it roughly like √N. At 10K vectors, FAISS warns that it has fewer than 39 training points per centroid; that affects quick mode only.
- **Exact search** is timed one query at a time on queries 5,000–5,999, as in Part 1.
- **Same grids, sweep stop and selection rule as Part 2.** The cost of recall 0.95 at each size is the report-half latency (1000 / QPS) of the fastest setting whose tune-half recall reaches 0.95, along with that index's build time and bytes per vector.
- **Growth rates** are the slope of a least-squares line through log(latency) against log(N) over the three sizes. The same is done for distance counts. Predicted slopes: 1 for exact search, 0.5 for IVF-Flat if the nprobe needed stays the same, close to 0 for HNSW.
- **Q4 inputs come from the same fit.** Latency at 150K is interpolated; latency at 10M is extrapolated, 10× beyond the largest size measured, and is labelled as an extrapolation. Memory at 10M is bytes per vector at the largest size × 10M.
- **Exact search at 1M is measured twice:** in Part 1 and again here, in separate processes. The gap between the two is one estimate of run-to-run timing noise (Q5).
- **Finding from the first quick run: a cache effect.** At 10K, 30K and 100K vectors, exact search's distance count grew exactly like N (slope 1.00), but its latency grew faster (slope 1.32). Almost all the excess came between 30K and 100K: 3.3× more vectors took 7.6× longer. The L3 cache is 24 MiB. 30K SIFT vectors (15 MB) fit in it and 100K (51 MB) don't, so the smaller sizes were probably served from cache and 100K from RAM. This is consistent with a cache effect but doesn't prove one. The full-mode sizes (51, 154 and 512 MB) are all beyond L3, so the full run's slopes measure the RAM-bound regime only. Q5 candidate: a benchmark on data small enough to fit in cache flatters search speed. Check with `lscpu | grep L3`.

## 2026-10-23: Part 4 (`04_hard_geometry.ipynb`), choices fixed before it first runs
- **Data.** The first 150,000 SIFT base vectors (quick mode: 50,000) and all 10,000 queries. Setting σ adds σ · s · ε to every vector:
  - s is the mean per-coordinate standard deviation of the clean base set.
  - ε ~ N(0, I) comes from `numpy.random.default_rng(42)`; the base noise is drawn first, then the query noise, so the two are independent.
  - The same ε is used at every σ, so the only thing that changes between settings is σ.
- **Size: 150K, not the 200K in the plan.** The assignment allows "at most 500K synthetic vectors". Counting strictly, that's every generated vector across the three noisy settings, queries included. That gives 3 × (150K + 10K) = 480K, which is within the limit; 200K would have made 630K. σ = 0 is the unchanged real data.
- **Settings:** σ ∈ {0 (control), 0.1, 0.3, 1.0}.
- **Ground truth is recomputed at each σ on the noisy data.** Recall therefore measures how well an index finds the true neighbours *of the noisy data*. It isn't a denoising test.
- **Relative contrast** measures how hard the geometry is. Per query, it's the mean L2 distance to 1,000 base vectors (sampled with seed 42) divided by the L2 distance to the true nearest neighbour. We report the median over report-half queries, and every Part 4 row stores it.
- **Indexes:** HNSW (M 16, efConstruction 200) and IVF-Flat (nlist 1024; quick mode 256), rebuilt from scratch at each σ, so IVF's k-means is retrained on that σ's data. This measures the geometry, not drift. Exact search is timed at each σ as a control: N and d don't change, so its time shouldn't either.
- **Longer sweeps than Part 2:** efSearch goes up to 2048, and nprobe up to nlist (every list). IVF-Flat can therefore always reach 0.95 in the worst case, by scanning everything, and HNSW gets a long sweep before it's declared "not reached".
- **Two measures of breaking:**
  1. **Recall at fixed effort.** Each index's 0.95 setting, chosen on the control's tune half, is applied at every σ.
  2. **Cost of getting back to 0.95.** The QPS and distance computations at each σ's own operating point.

## 2026-10-23: background load, found in the second quick run of Part 4
- **What happened.** Recall was identical across two quick runs, as it must be, but QPS at σ = 0 fell by up to 40% in the second. The raw passes for exact search were 0.975, 0.864 and 0.723 s, against a steady ~0.67 s later in the same run. Two of the three passes were slow, so the median couldn't absorb it.
- **Cause.** Firefox was using about 80% of a core at the time. CPU 2, which the timing thread is pinned to, shares a physical core with CPU 3. Whenever other work runs on either one, a single-threaded timing slows down. Pinning stops our thread from migrating; it doesn't keep other processes off the core.
- **Response.**
  - Every row now records `load_avg_1m` (`os.getloadavg()[0]` when its header is made). The full run can then show whether the machine was idle, and rows measured under load can be found.
  - For the full run, close the browser and other busy applications.
  - The protocol is unchanged: median of 3, as the assignment asks.
  - Q5 candidate: one-at-a-time QPS on a shared desktop depends on what else is running, even with pinning.

## 2026-10-24: report assets (`05_report_assets.ipynb`), fixed before it first runs
- **Every figure and table is rebuilt from `results.csv` alone** by `report_assets()` in `00_core`: the same functions the part notebooks call. `bash run_all.sh --only 05` redraws everything without repeating a benchmark.
- **The machine table** lists every distinct value of each machine field across all rows. One value per field shows that one machine ran everything; a test fails if the rows name more than one CPU. From now on, rows also record the h5py, pandas and matplotlib versions and the BLAS libraries loaded in the process (FAISS bundles its own OpenBLAS; numpy has another), since BLAS mattered for the d = 100 finding.
- **The timing-steadiness table (Q5)** reports:
  - the spread between the 3 timed passes of every one-at-a-time setting, defined as (slowest − fastest) / fastest, as a median, a 90th percentile and the share above 10%
  - the 1-minute load average while rows were measured (median and maximum)
  - the ratio of the two independent exact-search measurements on SIFT at the same N (Part 3 over Part 1)
- **Follow-up to the d = 100 finding (Part 1).** The BLAS field now in every row shows two OpenBLAS libraries in the process. numpy's is OpenBLAS 0.3.34 using its Haswell (AVX2) kernels. FAISS's bundled one is OpenBLAS 0.3.15 using its Prescott kernels: a generic SSE3 build, presumably chosen so the wheel runs on any x86-64 CPU. Batched exact search runs its matrix product through FAISS's library. That fits both observations: numpy's d = 100 product was fast, and FAISS's batched search at d = 100 was slow. It's an inference: we haven't swapped the library to prove it. Check with `cat report/tables/machine.md` (BLAS row) and the dimension-check rows in `report/tables/part1_timing.md`. Q5 candidate: batched exact-search speed depends on which BLAS build the FAISS wheel ships, not only on the hardware.
- **Correction, from the full run: `load_avg_1m` doesn't show outside load.** It's read once per build, when the sweep's header is made, right after the build. The 1-minute load average decays slowly, so it mostly reflects the build's own 12 threads. On full-run SIFT it tracked build time: 5.0 after a 4-second IVF build, 7–9 after the 50–70-second builds. Timings aren't affected, because the build threads have finished before timing starts, but the column can't show whether other programs were running. After the full run, the run-quality table will drop it. The steadiness evidence is the spread between timed passes, and exact search measured twice at the same N (Parts 1 and 3). The column stays in `results.csv`, described here.

## 2026-10-24: after the full run
- **Correction: the d = 100 batch finding is specific to quick mode.** In quick mode (1,000 queries in one batch against 100K vectors), FAISS's single-thread batch was no faster than one query at a time on GloVe, and padding to 128 dimensions doubled its speed. In the full run (5,000 queries against 1M and 1.18M vectors):
  - single-thread batching gives 3.2× on SIFT and 3.1× on GloVe;
  - SIFT cut to 100 dimensions is a little faster than at 128, not slower;
  - GloVe padded to 128 is slower (132 against 164 QPS), roughly in line with its 28% more arithmetic.

  So the slow case depends on the problem's shape, not on d = 100 alone. Batch size and base size both changed between the two modes, and we didn't test which matters. The facts about the two OpenBLAS builds stand, but they no longer explain a full-run result. Q5 candidate, with a different lesson: a quick-mode measurement didn't carry over to full scale. Check with `cat results_quick/tables/part1_timing.md report/tables/part1_timing.md`.
- **The run-quality table drops the load-average row**, as planned in the correction above. Its value (median 6.47) measured our own builds.
- **Part 2 grids extended after the full run, and Part 2 rerun.** Three GloVe builds ran out of grid before reaching about 0.95, which the assignment asks of every build's sweep. On the tune half, all three were still rising at the last step:
  - HNSW M 8 reached 0.850 at efSearch 768, up 0.024 from 512;
  - HNSW M 16 reached 0.939, up 0.019;
  - IVF-Flat nlist 4096 reached 0.932 at nprobe 256, up 0.016.

  The full-mode grids now go up to efSearch 2048 (adding 1024 and 1536) and nprobe 1024 (adding 384, 512 and 768). Part 2 skips nprobe values above `ivf_max_probe_fraction` × nlist: 0.25 in full mode, so IVF never scans more than a quarter of the lists, and 0.5 in quick mode, which leaves quick mode's grid unchanged. Without the cap, nlist 1024 on GloVe, already at 0.980, would keep sweeping toward a full scan on its way to 0.995.

  Only tune-half recall informed this. The sweep stop at 0.995 and every other rule are unchanged. Part 3 shares these grids, but all six of its sweeps stopped at 0.995 by efSearch 192 or nprobe 192, so the extension doesn't change what Part 3 measured. Part 4 has its own grids. Part 2 is rerun in full (`--only 02`, then `--only 05`) on the same machine, so its rows come from one consistent run.
- **The machine was rebooted between the overnight run and the Part 2 rerun.** It's the same hardware, and the rows show the same kernel (7.2.10), libraries and governor (`powersave`) in both. Part 2's rows are therefore from a later boot than Parts 1, 3 and 4. Check with `cat report/tables/machine.md`: every field should still have one value.

## 2026-10-24: quick mode on macOS
- **`00_core` now runs on macOS.** On an Apple M1 Pro it stopped at the machine-record tests: RAM came out as 0 GB and no BLAS library was found. The record read the CPU and RAM from `/proc`, which macOS doesn't have, and the test expected OpenBLAS. Where `/proc` is missing, the CPU now comes from `sysctl` and the RAM from `sysconf`. The BLAS check accepts Apple's Accelerate, which numpy and FAISS both use on macOS and threadpoolctl doesn't list. On Linux the record is read exactly as before, so the full-run rows are unaffected.
- **A macOS quick run measures differently** (choices that could bias a measurement):
  - The timing thread isn't pinned. macOS has no `sched_setaffinity`, so `timing_cpu` is empty and the scheduler may move the thread between cores, including onto the efficiency cores.
  - Builds use every core (`os.cpu_count()`, 8 on the M1 Pro: 6 performance, 2 efficiency), because `performance_cores()` only reads the Linux sysfs file.
  - The frequency governor is recorded as `unknown`: macOS manages CPU frequency itself.
  - BLAS is Accelerate, not OpenBLAS, so the notes above about FAISS's OpenBLAS build don't apply there.
- **threadpoolctl can't limit Accelerate's threads**, so on macOS Part 1's single-thread batch wasn't single-threaded, and was slower for it. On SIFT it ran at 6,752 QPS, against 12,987 with `VECLIB_MAXIMUM_THREADS=1` (`bash run_all.sh --quick --only 01` on the M1 Pro, with and without that variable). One query at a time was unchanged (962 and 948 QPS). The fix: `single_thread_pinned` also makes Accelerate single-threaded, with its own per-thread switch `BLASSetThreading` (macOS 15 and later), and restores it afterwards. Multi-threaded batches leave Accelerate to choose its own thread count, so on macOS their recorded thread count covers FAISS only. Before macOS 15 the switch doesn't exist, and single-thread batches run as they did before the fix. After the fix, the single-thread batch on SIFT ran at 12,545 QPS without the variable and 12,567 with it. Check with `bash run_all.sh --quick --only 01` run with and without `VECLIB_MAXIMUM_THREADS=1`: the one-batch, 1-thread rows of `results_quick/tables/part1_timing.md` should match.
- **The quick-mode d = 100 batch slowdown shows up with Accelerate too.** On the M1 Pro, a single-thread batch at d = 100 was no faster than one query at a time (GloVe: 1,128 against 1,116 QPS), while SIFT at 128 dimensions ran at 12,545 and GloVe zero-padded to 128 at 12,985. Linux quick mode showed the same pattern with OpenBLAS, so in quick mode the slowdown isn't specific to FAISS's OpenBLAS build. Check with the same command.

  No reported number is affected: they all come from the full run on the Linux machine. Check with `sysctl hw.perflevel0.logicalcpu hw.perflevel1.logicalcpu`, and with `cat results_quick/tables/machine.md` after `bash run_all.sh --quick` on a Mac.
