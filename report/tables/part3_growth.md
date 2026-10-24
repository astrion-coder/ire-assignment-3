| Method | Latency slope | Distance slope | N grows | Latency grows | ms/query at 150K (fit) | GB at 150K | ms/query at 10M (fit) | GB at 10M |
|---|---|---|---|---|---|---|---|---|
| Exact search | 1.05 | 1.00 | 10x | 11.2x | 2.83 | 0.08 | 232.52 | 5.12 |
| IVF-Flat | 0.66 | 0.62 | 10x | 4.6x | 0.11 | 0.08 | 1.84 | 5.22 |
| HNSW | 0.42 | 0.31 | 10x | 2.6x | 0.05 | 0.10 | 0.27 | 6.56 |
