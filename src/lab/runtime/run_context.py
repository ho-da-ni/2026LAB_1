"""Run context construction."""

from __future__ import annotations

import argparse
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from lab.shared_utils import DEFAULT_EXCLUDES, git_value, utc_now_iso
from lab.runtime.fingerprint import stable_sha256


def build_run_context(args: argparse.Namespace, start_time: datetime, end_time: datetime) -> dict[str, Any]:
    fingerprint_excludes = [
        "metadata.run.run_id",
        "metadata.run.created_at_utc",
        "metadata.workspace.root_path",
        "metadata.workspace.os",
        "metadata.workspace.python_version",
        "execution.start_time_utc",
        "execution.end_time_utc",
        "execution.duration_ms",
        "outputs.artifact_dir",
        "integrity.output_fingerprint",
    ]
    command_argv = ["analyze", "--repo", args.repo, "--output-dir", args.output_dir]
    dirty_raw = git_value(args.repo, "status", "--porcelain")
    dirty = "UNKNOWN" if dirty_raw == "UNKNOWN" else ("true" if dirty_raw else "false")
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "tool": {"name": "lab", "version": "UNKNOWN"},
        "inputs": {
            "repo": {
                "vcs": "git",
                "commit": git_value(args.repo, "rev-parse", "HEAD"),
                "branch": git_value(args.repo, "rev-parse", "--abbrev-ref", "HEAD"),
                "dirty": dirty,
                "diff_base": "UNKNOWN",
                "diff_target": "HEAD",
            },
            "db_metadata": {
                "source_type": "UNKNOWN",
                "source_path": "UNKNOWN",
                "snapshot_id": "UNKNOWN",
                "collected_at_utc": "UNKNOWN",
            },
            "config": {"path": "UNKNOWN", "hash_sha256": "UNKNOWN", "profile": "UNKNOWN"},
        },
        "execution": {
            "command": "lab analyze",
            "argv": command_argv,
            "start_time_utc": start_time.isoformat().replace("+00:00", "Z"),
            "end_time_utc": end_time.isoformat().replace("+00:00", "Z"),
            "duration_ms": int((end_time - start_time).total_seconds() * 1000),
            "timezone": "UTC",
            "exit_code": 0,
            "exit_code_policy_version": "1.0.0",
        },
        "analysis_scope": {
            "include_paths": [],
            "exclude_paths": DEFAULT_EXCLUDES,
            "file_count": "UNKNOWN",
            "language_set": [],
            "module_count": "UNKNOWN",
        },
        "outputs": {
            "ir_path": "UNKNOWN",
            "api_md_path": "UNKNOWN",
            "spec_md_path": "UNKNOWN",
            "db_schema_md_path": "UNKNOWN",
            "changed_files_path": "UNKNOWN",
            "fingerprint": "UNKNOWN",
            "artifact_dir": args.output_dir,
        },
        "quality_checks": {
            "checks": [],
            "summary": {"passed": "UNKNOWN", "failed": "UNKNOWN", "warnings": "UNKNOWN"},
            "rubric_version": "1.0.0",
            "test_scenario_set_version": "1.0.0",
        },
        "integrity": {
            "input_fingerprint": "UNKNOWN",
            "output_fingerprint": "UNKNOWN",
            "determinism_key": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "include": [],
                "exclude": fingerprint_excludes,
                "path_normalization_version": "1.0.0",
            },
        },
        "metadata": {
            "run": {
                "run_id": str(uuid.uuid4()),
                "created_at_utc": utc_now_iso(),
            },
            "workspace": {
                "root_path": str(Path.cwd()),
                "os": platform.platform(),
                "python_version": platform.python_version(),
            },
        },
        "notes": ["UNKNOWN"],
        "needs_review": [],
    }
    payload["integrity"]["output_fingerprint"] = stable_sha256(
        payload,
        exclude_paths=fingerprint_excludes,
    )
    return payload
