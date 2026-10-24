"""Tests for scripts/package.py on a throwaway git repository."""
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import package  # noqa: E402


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def make_repo(root, mode="full"):
    """A committed repository laid out like ours, plus the untracked report.pdf and ai_log/."""
    (root / "results" / "figures").mkdir(parents=True)
    (root / "results" / "results.csv").write_text(f"part,mode,qps\n1,{mode},10.0\n")
    (root / "results" / "figures" / "f.pdf").write_text("figure")
    (root / "run_all.sh").write_text("echo hi\n")
    (root / ".gitignore").write_text("ai_log/\nreport.pdf\ndata/\n")
    run("git", "init", "--quiet", cwd=root)
    run("git", "add", ".", cwd=root)
    run("git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "--quiet", "-m", "init", cwd=root)
    run("git", "remote", "add", "origin", "https://example.com/repo.git", cwd=root)
    (root / "ai_log").mkdir()
    (root / "ai_log" / "ai_statement.md").write_text("statement")
    (root / "report" / "report.pdf").parent.mkdir()
    (root / "report" / "report.pdf").write_text("report")
    return root


def build(root, tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    return package.write_zip(package.stage(root, staging), tmp_path / "out" / "x_A3.zip")


def test_zip_holds_exactly_the_four_entries(tmp_path):
    out = build(make_repo(tmp_path / "repo"), tmp_path)
    names = zipfile.ZipFile(out).namelist()
    assert {name.split("/")[0] for name in names} == set(package.TOP_LEVEL)
    assert "code/.git/HEAD" in names and "code/run_all.sh" in names and "results/results.csv" in names
    assert "report.pdf" in names and not any(name.startswith("code/report") for name in names)


def test_clone_has_no_remote(tmp_path):
    repo = make_repo(tmp_path / "repo")
    staging = package.stage(repo, tmp_path / "staging")
    assert package.git("remote", cwd=staging / "code").strip() == ""


def test_ignored_files_stay_out_of_code(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "data").mkdir()
    (repo / "data" / "sift.hdf5").write_text("vectors")  # ignored, so the clone never sees it
    names = zipfile.ZipFile(build(repo, tmp_path)).namelist()
    assert not any(name.endswith(".hdf5") for name in names)


def test_uncommitted_changes_are_refused(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "run_all.sh").write_text("changed\n")
    with pytest.raises(SystemExit, match="Uncommitted"):
        package.stage(repo, tmp_path / "staging")


def test_quick_results_are_refused(tmp_path):
    with pytest.raises(SystemExit, match="full run"):
        package.stage(make_repo(tmp_path / "repo", mode="quick"), tmp_path / "staging")


def test_forbidden_paths_are_found(tmp_path):
    (tmp_path / "cache").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "gt.npy").write_text("ids")
    assert package.forbidden(tmp_path) == [Path("cache"), Path("results/gt.npy")]
