| Dataset | Index | Setting for 0.90 | Recall (0.90) | QPS (0.90) | Setting for 0.95 | Recall (0.95) | QPS (0.95) |
|---|---|---|---|---|---|---|---|
| SIFT | HNSW | M=32, efSearch=24 | 0.916 | 17,617 | M=16, efSearch=64 | 0.971 | 10,951 |
| SIFT | IVF-Flat | nlist=4096, nprobe=32 | 0.930 | 4,177 | nlist=4096, nprobe=48 | 0.960 | 2,993 |
| SIFT | IVF-PQ | not reached |  |  | not reached |  |  |
| SIFT | Exact search | full scan | 1.000 | 47.8 | full scan | 1.000 | 47.8 |
| GloVe-100 | HNSW | M=32, efSearch=192 | 0.918 | 2,314 | M=32, efSearch=384 | 0.955 | 1,198 |
| GloVe-100 | IVF-Flat | nlist=4096, nprobe=192 | 0.915 | 1,046 | nlist=4096, nprobe=384 | 0.953 | 552 |
| GloVe-100 | IVF-PQ | not reached |  |  | not reached |  |  |
| GloVe-100 | Exact search | full scan | 1.000 | 53.4 | full scan | 1.000 | 53.4 |
