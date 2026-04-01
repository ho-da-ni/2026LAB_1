from __future__ import annotations

import json
import subprocess
from pathlib import Path

from lab.cli import _build_changed_files, main


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "lab@example.com")
    _git(repo, "config", "user.name", "LAB")

    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    return repo


def test_w2_analyze_generates_repo_meta_and_scan_index(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out = tmp_path / "out"

    rc = main(["analyze", "--repo", str(repo), "--output-dir", str(out)])
    assert rc == 0

    run_context_path = out / "run_context.json"
    repo_meta_path = out / "repo_meta.json"
    scan_index_path = out / "scan_index.json"
    assert run_context_path.exists()
    assert repo_meta_path.exists()
    assert scan_index_path.exists()

    repo_meta = json.loads(repo_meta_path.read_text(encoding="utf-8"))
    assert repo_meta["vcs"] == "git"
    assert repo_meta["head"]["branch"] == "main"
    assert repo_meta["code_stats"]["file_count"] >= 1
    assert isinstance(repo_meta["integrity"]["fingerprint"], str)

    scan_index = json.loads(scan_index_path.read_text(encoding="utf-8"))
    indexed_paths = [item["path"] for item in scan_index["artifacts"]]
    assert indexed_paths == sorted(indexed_paths)
    assert "run_context.json" in indexed_paths
    assert "repo_meta.json" in indexed_paths
    assert scan_index["summary"]["total_files"] == len(scan_index["artifacts"])


def test_w2_changed_files_is_sorted_and_normalized(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "z.py").write_text("z=1\n", encoding="utf-8")
    (repo / "a.py").write_text("a=1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "add files")

    payload = _build_changed_files(str(repo), "HEAD~1", "HEAD", [], [])
    paths = [item["path"] for item in payload["files"]]
    assert paths == sorted(paths)
    assert all("\\" not in p for p in paths)
    assert payload["summary"]["total_files"] == len(payload["files"])


def test_w2_diff_failure_ref_returns_3(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output = tmp_path / "changed_files.json"
    rc = main(["diff", "--repo", str(repo), "--base", "does-not-exist", "--head", "HEAD", "--output", str(output)])
    assert rc == 3
    assert not output.exists()


def test_w2_diff_failure_integrity_returns_7(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output = tmp_path / "changed_files.json"
    rc = main(
        [
            "diff",
            "--repo",
            str(repo),
            "--base",
            "HEAD",
            "--head",
            "HEAD",
            "--test-hook-force-integrity-mismatch",
            "--output",
            str(output),
        ]
    )
    assert rc == 7
    assert not output.exists()

