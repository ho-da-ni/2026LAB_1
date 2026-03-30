"""LAB CLI entrypoint."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

DEFAULT_EXCLUDES = [".git/", "build/", "target/"]


class GitUnavailableError(RuntimeError):
    """Raised when git executable is not available."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_git(repo: str, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise GitUnavailableError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or exc.stdout.strip() or "git command failed") from exc
    return result.stdout.strip()


def _git_value(repo: str, *args: str) -> str:
    try:
        output = _run_git(repo, list(args))
    except (RuntimeError, GitUnavailableError):
        return "UNKNOWN"
    return output or "UNKNOWN"


def _build_run_context(args: argparse.Namespace, start_time: datetime, end_time: datetime) -> dict[str, Any]:
    command_argv = ["analyze", "--repo", args.repo, "--output-dir", args.output_dir]
    dirty_raw = _git_value(args.repo, "status", "--porcelain")
    dirty = "UNKNOWN" if dirty_raw == "UNKNOWN" else ("true" if dirty_raw else "false")

    return {
        "schema_version": "1.0.0",
        "run_id": str(uuid.uuid4()),
        "created_at_utc": _utc_now_iso(),
        "tool": {"name": "lab", "version": "UNKNOWN"},
        "workspace": {
            "root_path": str(Path.cwd()),
            "os": platform.platform(),
            "python_version": platform.python_version(),
        },
        "inputs": {
            "repo": {
                "vcs": "git",
                "commit": _git_value(args.repo, "rev-parse", "HEAD"),
                "branch": _git_value(args.repo, "rev-parse", "--abbrev-ref", "HEAD"),
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
            "config": {
                "path": "UNKNOWN",
                "hash_sha256": "UNKNOWN",
                "profile": "UNKNOWN",
            },
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
                "exclude": [],
                "path_normalization_version": "1.0.0",
            },
        },
        "notes": ["UNKNOWN"],
        "needs_review": [],
    }


def _atomic_write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(output_path)


def _normalize_path(path: str) -> str:
    return str(Path(path).as_posix()).lstrip("./")


def _match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _is_excluded(path: str, excludes: list[str]) -> bool:
    for prefix in DEFAULT_EXCLUDES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    return _match_any(path, excludes)


def _is_included(path: str, includes: list[str]) -> bool:
    if not includes:
        return True
    return _match_any(path, includes)


def _build_changed_files(repo: str, base: str, head: str, includes: list[str], excludes: list[str]) -> dict[str, Any]:
    merge_base = _run_git(repo, ["merge-base", base, head])
    diff_output = _run_git(repo, ["diff", "--name-status", base, head])

    files: list[dict[str, Any]] = []
    summary = {"A": 0, "M": 0, "D": 0, "R": 0}

    for raw in diff_output.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        code = parts[0][0]

        old_path = "UNKNOWN"
        if code == "R" and len(parts) >= 3:
            old_path = _normalize_path(parts[1])
            path = _normalize_path(parts[2])
        elif len(parts) >= 2:
            path = _normalize_path(parts[1])
        else:
            continue

        if _is_excluded(path, excludes):
            continue
        if not _is_included(path, includes):
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
                "evidence": {
                    "diff_header": raw,
                    "blob_before": "UNKNOWN",
                    "blob_after": "UNKNOWN",
                },
            }
        )

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": _utc_now_iso(),
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

    fingerprint_source = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["integrity"]["fingerprint"] = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    return payload


def _handle_analyze(args: argparse.Namespace) -> int:
    start = datetime.now(timezone.utc)
    output_dir = Path(args.output_dir)
    try:
        run_context = _build_run_context(args, start, datetime.now(timezone.utc))
        _atomic_write_json(output_dir / "run_context.json", run_context)
    except OSError as exc:
        print(f"[ERROR] failed to write run_context.json: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_dir / 'run_context.json'}")
    return 0


def _handle_diff(args: argparse.Namespace) -> int:
    includes = args.include or []
    excludes = args.exclude or []

    try:
        payload = _build_changed_files(args.repo, args.base, args.head, includes, excludes)
    except GitUnavailableError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 8
    except RuntimeError as exc:
        print(f"[ERROR] diff ref resolution failed: {exc}", file=sys.stderr)
        return 3

    if payload["summary"]["total_files"] != len(payload["files"]):
        print("[ERROR] changed_files integrity mismatch", file=sys.stderr)
        return 7

    try:
        _atomic_write_json(Path(args.output), payload)
    except OSError as exc:
        print(f"[ERROR] failed to write changed_files.json: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="LAB CLI")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository and build run context")
    analyze_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    analyze_parser.add_argument("--output-dir", required=True, help="Output directory for analysis artifacts")

    generate_parser = subparsers.add_parser("generate", help="Generate markdown artifacts")
    generate_subparsers = generate_parser.add_subparsers(dest="generate_command", metavar="TARGET")
    generate_subparsers.add_parser("api", help="Generate API.md")
    generate_subparsers.add_parser("spec", help="Generate SPEC.md")
    generate_subparsers.add_parser("db-schema", help="Generate DB_SCHEMA.md")

    diff_parser = subparsers.add_parser("diff", help="Collect changed files between refs")
    diff_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    diff_parser.add_argument("--base", required=True, help="Base git ref")
    diff_parser.add_argument("--head", required=True, help="Head git ref")
    diff_parser.add_argument("--output", required=True, help="Path to write changed_files.json")
    diff_parser.add_argument("--include", action="append", help="Include path/glob pattern")
    diff_parser.add_argument("--exclude", action="append", help="Exclude path/glob pattern")

    subparsers.add_parser("validate", help="Validate generated artifacts")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "generate" and args.generate_command is None:
        parser.parse_args(["generate", "--help"])
        return 0

    if args.command == "analyze":
        return _handle_analyze(args)
    if args.command == "diff":
        return _handle_diff(args)

    # Command implementations will be added in subsequent milestones.
    print(f"[TODO] '{args.command}' command is not implemented yet.")
    return 0
