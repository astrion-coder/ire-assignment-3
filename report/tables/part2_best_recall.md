| Dataset | Index | Build | Best search setting | Largest swept | Tune recall | Report recall |
|---|---|---|---|---|---|---|
| SIFT | HNSW | M=8 | efSearch=1024 | 1024 | 0.996 | 0.997 |
| SIFT | HNSW | M=16 | efSearch=192 | 192 | 0.996 | 0.996 |
| SIFT | HNSW | M=32 | efSearch=128 | 128 | 0.995 | 0.996 |
| SIFT | IVF-Flat | nlist=1024 | nprobe=64 | 64 | 0.996 | 0.997 |
| SIFT | IVF-Flat | nlist=4096 | nprobe=192 | 192 | 0.998 | 0.998 |
| SIFT | IVF-PQ | nlist=4096, m=16 | nprobe=512 | 1024 | 0.586 | 0.596 |
| SIFT | IVF-PQ | nlist=4096, m=32 | nprobe=768 | 1024 | 0.736 | 0.746 |
| SIFT | IVF-PQ | nlist=4096, m=64 | nprobe=768 | 1024 | 0.884 | 0.887 |
| GloVe-100 | HNSW | M=8 | efSearch=2048 | 2048 | 0.898 | 0.897 |
| GloVe-100 | HNSW | M=16 | efSearch=2048 | 2048 | 0.973 | 0.972 |
| GloVe-100 | HNSW | M=32 | efSearch=2048 | 2048 | 0.994 | 0.994 |
| GloVe-100 | IVF-Flat | nlist=1024 | nprobe=256 | 256 | 0.980 | 0.981 |
| GloVe-100 | IVF-Flat | nlist=4096 | nprobe=1024 | 1024 | 0.987 | 0.987 |
| GloVe-100 | IVF-PQ | nlist=4096, m=20 | nprobe=1024 | 1024 | 0.540 | 0.540 |
| GloVe-100 | IVF-PQ | nlist=4096, m=50 | nprobe=1024 | 1024 | 0.869 | 0.868 |
