"""Builds the submission zip, dist/<ROLL>_A3.zip, holding exactly:

    report.pdf    the report
    code/         a clone of this repository at HEAD, .git included
    results/      results.csv and figures/ from the full run
    ai_log/       prompts, responses and ai_statement.md

Usage:  python scripts/package.py --roll <ROLLNUMBER>

It refuses to package uncommitted work (code/ is a clone of HEAD), quick-mode results, or anything that looks like a
dataset, cache or index file.
"""
import argparse
import csv
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOP_LEVEL = ["report.pdf", "code", "results", "ai_log"]
REQUIRED = ["report.pdf", "results/results.csv", "ai_log/ai_statement.md"]
FORBIDDEN_SUFFIXES = {".hdf5", ".h5", ".npy", ".npz", ".index", ".faiss"}
FORBIDDEN_DIRS = {"data", "cache", "results_quick", "dist", ".venv"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def forbidden(root):
    """Paths under `root` that must never be submitted: datasets, caches, index files, environments."""
    found = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if (path.is_file() and path.suffix in FORBIDDEN_SUFFIXES) or (path.is_dir() and path.name in FORBIDDEN_DIRS):
            found.append(relative)
    return found


def check_source(root):
    """Stops with a message if `root` is not ready to package."""
    if git("status", "--porcelain", cwd=root).strip():
        raise SystemExit("Uncommitted changes: code/ is a clone of HEAD, so commit (or stash) them first.")
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if missing:
        raise SystemExit(f"Missing: {', '.join(missing)}")
    with open(root / "results" / "results.csv", newline="") as file:
        modes = {row["mode"] for row in csv.DictReader(file)}
    if modes != {"full"}:
        raise SystemExit(f"results/results.csv must come from a full run only; found modes {sorted(modes)}")


def stage(root, staging):
    """Lays the submission out in `staging`: the four top-level entries and nothing else."""
    check_source(root)
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(root), str(staging / "code")], check=True)
    git("remote", "remove", "origin", cwd=staging / "code")
    shutil.copytree(root / "results", staging / "results")
    shutil.copytree(root / "ai_log", staging / "ai_log")
    shutil.copy2(root / "report.pdf", staging / "report.pdf")
    bad = forbidden(staging)
    if bad:
        raise SystemExit("Refusing to package these paths:\n  " + "\n  ".join(map(str, bad)))
    return staging


def write_zip(staging, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging.rglob("*")):
            archive.write(path, path.relative_to(staging))
    return out


def summary(out):
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
    top = sorted({name.split("/")[0] for name in names})
    lines = [f"{out} ({out.stat().st_size / 1e6:.1f} MB, {len(names)} entries)", f"top level: {', '.join(top)}"]
    for entry in TOP_LEVEL:
        inside = [name for name in names if name == entry or name.startswith(entry + "/")]
        lines.append(f"  {entry}: {len(inside)} entries")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--roll", required=True, help="your roll number; the zip is named <roll>_A3.zip")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        staging = stage(ROOT, Path(directory))
        out = write_zip(staging, ROOT / "dist" / f"{args.roll}_A3.zip")
    print(summary(out))


if __name__ == "__main__":
    main()
