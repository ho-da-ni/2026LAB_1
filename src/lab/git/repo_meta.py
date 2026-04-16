"""Repository metadata builders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lab.cli_shared import git_value, is_default_excluded, normalize_path, run_git, sha256_file, utc_now_iso
from lab.runtime.fingerprint import stable_sha256


def collect_repo_meta(repo: str) -> dict[str, Any]:
    remotes: dict[str, dict[str, str]] = {}
    try:
        remote_lines = run_git(repo, ["remote", "-v"]).splitlines()
    except RuntimeError:
        remote_lines = []

    for line in remote_lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, kind = parts[0], parts[1], parts[2].strip("()")
        if name not in remotes:
            remotes[name] = {"name": name, "url": url, "fetch": "UNKNOWN", "push": "UNKNOWN"}
        if kind == "fetch":
            remotes[name]["fetch"] = url
        elif kind == "push":
            remotes[name]["push"] = url

    remote_list = sorted(remotes.values(), key=lambda x: x["name"])
    origin_url = next((item["url"] for item in remote_list if item["name"] == "origin"), "UNKNOWN")
    repo_id = "UNKNOWN"
    if origin_url != "UNKNOWN":
        cleaned = re.sub(r"\.git$", "", origin_url)
        if ":" in cleaned and "://" not in cleaned:
            repo_id = cleaned.rsplit(":", 1)[-1]
        else:
            repo_id = cleaned.rstrip("/").split("/")[-2:] if "/" in cleaned else ["UNKNOWN"]
            repo_id = "/".join(repo_id) if isinstance(repo_id, list) and len(repo_id) == 2 else "UNKNOWN"

    default_branch_raw = git_value(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    default_branch = default_branch_raw.split("/")[-1] if default_branch_raw != "UNKNOWN" else "UNKNOWN"

    head_commit = git_value(repo, "rev-parse", "HEAD")
    head_branch = git_value(repo, "rev-parse", "--abbrev-ref", "HEAD")
    head_tag = git_value(repo, "describe", "--tags", "--exact-match", "HEAD")
    dirty_raw = git_value(repo, "status", "--porcelain")
    dirty = "UNKNOWN" if dirty_raw == "UNKNOWN" else ("true" if dirty_raw else "false")

    repo_path = Path(repo)
    tracked_files_output = git_value(repo, "ls-files")
    tracked_files = (
        sorted([normalize_path(line) for line in tracked_files_output.splitlines() if line.strip()])
        if tracked_files_output != "UNKNOWN"
        else []
    )

    language_bytes: dict[str, int] = {}
    language_files: dict[str, int] = {}
    for rel in tracked_files:
        if is_default_excluded(rel):
            continue
        abs_path = repo_path / rel
        if not abs_path.exists() or not abs_path.is_file():
            continue
        ext = abs_path.suffix.lower().lstrip(".") or "no_ext"
        try:
            file_size = abs_path.stat().st_size
        except OSError:
            continue
        language_bytes[ext] = language_bytes.get(ext, 0) + file_size
        language_files[ext] = language_files.get(ext, 0) + 1

    codeowners_path = "UNKNOWN"
    for candidate in ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]:
        if (repo_path / candidate).exists():
            codeowners_path = normalize_path(candidate)
            break

    license_path = "UNKNOWN"
    for entry in sorted(repo_path.iterdir(), key=lambda p: p.name):
        if entry.is_file() and entry.name.upper().startswith("LICENSE"):
            license_path = entry.name
            break

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "repo_id": repo_id,
        "collected_at_utc": utc_now_iso(),
        "vcs": "git",
        "default_branch": default_branch,
        "remotes": remote_list,
        "head": {"commit": head_commit, "branch": head_branch, "tag": head_tag, "dirty": dirty},
        "history_window": {"base_commit": "UNKNOWN", "target_commit": head_commit, "commit_count": "UNKNOWN"},
        "code_stats": {
            "file_count": sum(language_files.values()),
            "language_bytes": dict(sorted(language_bytes.items())),
            "language_files": dict(sorted(language_files.items())),
        },
        "ownership": {"codeowners_path": codeowners_path, "teams": []},
        "constraints": {"license": license_path, "runtime_versions": {"python": "UNKNOWN", "node": "UNKNOWN"}},
        "integrity": {"fingerprint": "UNKNOWN", "fingerprint_policy_version": "1.0.0"},
        "needs_review": [],
    }
    payload["integrity"]["fingerprint"] = stable_sha256(payload, exclude_keys=["collected_at_utc"])
    return payload


def build_scan_index(output_dir: Path) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for file_path in sorted([p for p in output_dir.rglob("*") if p.is_file()], key=lambda p: p.as_posix()):
        rel_path = normalize_path(str(file_path.relative_to(output_dir)))
        artifacts.append({"path": rel_path, "size_bytes": file_path.stat().st_size, "sha256": sha256_file(file_path)})

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": utc_now_iso(),
        "root": normalize_path(str(output_dir)),
        "summary": {"total_files": len(artifacts)},
        "artifacts": artifacts,
        "integrity": {"fingerprint": "UNKNOWN", "fingerprint_policy_version": "1.0.0"},
    }
    payload["integrity"]["fingerprint"] = stable_sha256(payload, exclude_keys=["generated_at_utc"])
    return payload
