"""Download the ann-benchmarks HDF5 files used in Assignment 3 into data/ and check their layout.

Usage:
    python scripts/download_data.py            download whatever is missing, then check both files
    python scripts/download_data.py --check    only check the files already in data/
"""
import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
N_QUERIES = 10_000
REPORT_EVERY = 100 * 2**20
# ann-benchmarks.com sits behind Cloudflare, which answers 403 to urllib's default "Python-urllib/3.x" agent.
USER_AGENT = "ann-benchmark-a3/0.1 (course assignment data download)"

# URLs are the links given in the assignment PDF.
DATASETS = {
    "sift-128-euclidean": dict(url="http://ann-benchmarks.com/sift-128-euclidean.hdf5", dim=128, min_base=1_000_000),
    "glove-100-angular": dict(url="http://ann-benchmarks.com/glove-100-angular.hdf5", dim=100, min_base=1_000_000),
}


def download(name, spec):
    target = DATA_DIR / f"{name}.hdf5"
    if target.exists():
        print(f"{target.name}: already present, skipping download")
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    partial = DATA_DIR / f"{name}.hdf5.part"
    print(f"{target.name}: downloading {spec['url']}", flush=True)
    request = urllib.request.Request(spec["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done, next_report = 0, REPORT_EVERY
        while chunk := response.read(2**20):
            out.write(chunk)
            done += len(chunk)
            if done >= next_report:
                share = f" of {total / 1e6:.0f} MB" if total else ""
                print(f"  {done / 1e6:.0f} MB{share}", flush=True)
                next_report += REPORT_EVERY
    partial.rename(target)


def check(path, spec):
    """Return a list of problems with the file's layout (empty when it looks right)."""
    import h5py

    with h5py.File(path, "r") as f:
        missing = {"train", "test", "neighbors", "distances"} - set(f)
        if missing:
            return [f"missing datasets {sorted(missing)}"]
        base, queries, neighbors, distances = (f[k].shape for k in ("train", "test", "neighbors", "distances"))
    print(f"{path.name}: base {base}, queries {queries}, neighbors {neighbors}")
    problems = []
    if base[1] != spec["dim"] or queries[1] != spec["dim"]:
        problems.append(f"expected dimension {spec['dim']}")
    if base[0] < spec["min_base"]:
        problems.append(f"expected at least {spec['min_base']:,} base vectors")
    if queries[0] != N_QUERIES:
        problems.append(f"expected {N_QUERIES:,} queries")
    if neighbors[0] != queries[0] or neighbors[1] < 10 or distances != neighbors:
        problems.append(f"ground-truth shapes look wrong (distances {distances})")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only check files already in data/")
    args = parser.parse_args()

    failed = False
    for name, spec in DATASETS.items():
        path = DATA_DIR / f"{name}.hdf5"
        if not args.check:
            try:
                download(name, spec)
            except OSError as err:
                print(f"{path.name}: download failed ({err}). Fetch it by hand from the repo root:\n"
                      f"  curl -L -o data/{path.name} {spec['url']}", file=sys.stderr)
                failed = True
                continue
        if not path.exists():
            print(f"{path.name}: missing (run without --check to download it)", file=sys.stderr)
            failed = True
            continue
        for problem in check(path, spec):
            print(f"{path.name}: {problem}", file=sys.stderr)
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
