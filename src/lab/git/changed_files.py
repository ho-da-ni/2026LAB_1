"""Changed files collection from git diff."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lab.cli_shared import DEFAULT_EXCLUDES, git_value, is_default_excluded, is_excluded, is_included, normalize_path, run_git, utc_now_iso
from lab.runtime.fingerprint import stable_sha256


def build_changed_files(repo: str, base: str, head: str, includes: list[str], excludes: list[str]) -> dict[str, Any]:
    merge_base = run_git(repo, ["merge-base", base, head])
    diff_output = run_git(repo, ["diff", "--name-status", base, head])
    generated_at_utc = git_value(repo, "log", "-1", "--format=%cI", head)
    if generated_at_utc != "UNKNOWN":
        parsed = datetime.fromisoformat(generated_at_utc)
        generated_at_utc = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        generated_at_utc = utc_now_iso()

    files: list[dict[str, Any]] = []
    default_excluded_paths: list[str] = []
    summary = {"A": 0, "M": 0, "D": 0, "R": 0}

    for raw in diff_output.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        code = parts[0][0]

        old_path = "UNKNOWN"
        if code == "R" and len(parts) >= 3:
            old_path = normalize_path(parts[1])
            path = normalize_path(parts[2])
        elif len(parts) >= 2:
            path = normalize_path(parts[1])
        else:
            continue

        if is_excluded(path, excludes):
            if is_default_excluded(path):
                default_excluded_paths.append(path)
            continue
        if not is_included(path, includes):
            continue

        if code in summary:
            summary[code] += 1

        files.append(
            {
                "path": path,
                "old_path": old_path,
                "status": code if code in {"A", "M", "D", "R", "C", "T"} else "UNKNOWN",
                "language": "UNKNOWN",
                "hunks": "UNKNOWN",
                "lines_added": "UNKNOWN",
                "lines_deleted": "UNKNOWN",
                "is_binary": "UNKNOWN",
                "evidence": {"diff_header": raw, "blob_before": "UNKNOWN", "blob_after": "UNKNOWN"},
            }
        )

    files = sorted(files, key=lambda item: (str(item["path"]), str(item["status"]), str(item["old_path"])))
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "repo": {"vcs": "git", "base": base, "head": head, "merge_base": merge_base or "UNKNOWN"},
        "summary": {
            "total_files": len(files),
            "added": summary["A"],
            "modified": summary["M"],
            "deleted": summary["D"],
            "renamed": summary["R"],
        },
        "files": files,
        "filters": {"include_paths": includes, "exclude_paths": excludes},
        "integrity": {"fingerprint": "UNKNOWN", "fingerprint_policy_version": "1.0.0"},
        "needs_review": [],
    }

    if default_excluded_paths:
        payload["needs_review"].append(
            {
                "check": "default_excludes_applied",
                "status": "pass",
                "evidence": {
                    "default_excludes": DEFAULT_EXCLUDES,
                    "excluded_count": len(default_excluded_paths),
                    "sample_paths": sorted(set(default_excluded_paths))[:10],
                },
            }
        )

    payload["integrity"]["fingerprint"] = stable_sha256(payload, exclude_keys=["generated_at_utc"])
    return payload
