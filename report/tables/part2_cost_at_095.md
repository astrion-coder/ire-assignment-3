| Dataset | Index | Setting | Recall | QPS | Dist./query | Build (s) | Size (MB) | B/vector | PQ table (MB) |
|---|---|---|---|---|---|---|---|---|---|
| SIFT | HNSW | M=16, efSearch=64 | 0.971 | 10,951 | 1,245 | 52.0 | 656.3 | 656 | 0.0 |
| SIFT | IVF-Flat | nlist=4096, nprobe=48 | 0.960 | 2,993 | 17,030 | 48.3 | 522.1 | 522 | 0.0 |
| SIFT | IVF-PQ | nlist=4096, m=64, nprobe=768* | 0.887 | 179 | 193,357 | 68.8 | 74.3 | 74 | 268.4 |
| SIFT | Exact search | full scan | 1.000 | 47.8 | 1,000,000 | 0.1 | 512.0 | 512 | 0.0 |
| GloVe-100 | HNSW | M=32, efSearch=384 | 0.955 | 1,198 | 11,889 | 107.4 | 795.5 | 672 | 0.0 |
| GloVe-100 | IVF-Flat | nlist=4096, nprobe=384 | 0.953 | 552 | 103,191 | 43.5 | 484.5 | 409 | 0.0 |
| GloVe-100 | IVF-PQ | nlist=4096, m=50, nprobe=1024* | 0.868 | 165 | 266,164 | 57.4 | 70.4 | 59 | 209.7 |
| GloVe-100 | Exact search | full scan | 1.000 | 53.4 | 1,183,514 | 0.1 | 473.4 | 400 | 0.0 |
