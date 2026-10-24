| σ | Rel. contrast | Method | Setting for 0.95 | Recall | QPS | Distances/query | Recall at control's setting |
|---|---|---|---|---|---|---|---|
| 0 | 2.423 | Exact search | full scan | 1.000 | 351 | 150,000 |  |
| 0 | 2.423 | IVF-Flat | nlist=1024, nprobe=32 | 0.968 | 7,862 | 6,101 | 0.968 |
| 0 | 2.423 | HNSW | M=16, efSearch=48 | 0.976 | 17,123 | 843 | 0.976 |
| 0.1 | 2.381 | Exact search | full scan | 1.000 | 345 | 150,000 |  |
| 0.1 | 2.381 | IVF-Flat | nlist=1024, nprobe=32 | 0.968 | 7,859 | 6,115 | 0.968 |
| 0.1 | 2.381 | HNSW | M=16, efSearch=48 | 0.976 | 16,858 | 850 | 0.976 |
| 0.3 | 2.125 | Exact search | full scan | 1.000 | 344 | 150,000 |  |
| 0.3 | 2.125 | IVF-Flat | nlist=1024, nprobe=32 | 0.960 | 7,827 | 6,101 | 0.960 |
| 0.3 | 2.125 | HNSW | M=16, efSearch=48 | 0.966 | 15,912 | 931 | 0.966 |
| 1 | 1.522 | Exact search | full scan | 1.000 | 346 | 150,000 |  |
| 1 | 1.522 | IVF-Flat | nlist=1024, nprobe=128 | 0.977 | 2,184 | 20,662 | 0.806 |
| 1 | 1.522 | HNSW | M=16, efSearch=256 | 0.959 | 2,108 | 4,711 | 0.728 |
