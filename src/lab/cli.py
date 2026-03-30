"""LAB CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

DEFAULT_EXCLUDES = [".git/", "build/", "target/"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_value(repo: str, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            check=True,
            text=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def _build_run_context(args: argparse.Namespace, start_time: datetime, end_time: datetime) -> dict[str, Any]:
    repo = str(Path(args.repo).resolve())
    command_argv = ["analyze", "--repo", args.repo, "--output-dir", args.output_dir]

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
                "dirty": "true" if _git_value(args.repo, "status", "--porcelain") != "UNKNOWN" and _git_value(args.repo, "status", "--porcelain") else "false",
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


def _handle_analyze(args: argparse.Namespace) -> int:
    start = datetime.now(timezone.utc)
    output_dir = Path(args.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        run_context = _build_run_context(args, start, datetime.now(timezone.utc))
        with (output_dir / "run_context.json").open("w", encoding="utf-8") as f:
            json.dump(run_context, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
    except OSError as exc:
        print(f"[ERROR] failed to write run_context.json: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_dir / 'run_context.json'}")
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

    subparsers.add_parser("diff", help="Collect changed files between refs")
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

    # Command implementations will be added in subsequent milestones.
    print(f"[TODO] '{args.command}' command is not implemented yet.")
    return 0
