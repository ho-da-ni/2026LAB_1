"""LAB CLI entrypoint."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import posixpath
import platform
import re
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


def _normalize_match_pattern(pattern: str) -> str:
    normalized = posixpath.normpath(pattern.replace("\\", "/"))
    return normalized.lstrip("./")


def _match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _is_excluded(path: str, excludes: list[str]) -> bool:
    for prefix in DEFAULT_EXCLUDES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    return _match_any(path, excludes)


def _is_default_excluded(path: str) -> bool:
    for prefix in DEFAULT_EXCLUDES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    return False


def _is_included(path: str, includes: list[str]) -> bool:
    if not includes:
        return True
    return _match_any(path, includes)


def _build_changed_files(repo: str, base: str, head: str, includes: list[str], excludes: list[str]) -> dict[str, Any]:
    merge_base = _run_git(repo, ["merge-base", base, head])
    diff_output = _run_git(repo, ["diff", "--name-status", base, head])
    generated_at_utc = _git_value(repo, "log", "-1", "--format=%cI", head)
    if generated_at_utc != "UNKNOWN":
        parsed_generated_at = datetime.fromisoformat(generated_at_utc)
        generated_at_utc = parsed_generated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        generated_at_utc = _utc_now_iso()

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
            old_path = _normalize_path(parts[1])
            path = _normalize_path(parts[2])
        elif len(parts) >= 2:
            path = _normalize_path(parts[1])
        else:
            continue

        if _is_excluded(path, excludes):
            if _is_default_excluded(path):
                default_excluded_paths.append(path)
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

    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("generated_at_utc", None)
    fingerprint_source = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
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
    includes = [_normalize_match_pattern(pattern) for pattern in (args.include or [])]
    excludes = [_normalize_match_pattern(pattern) for pattern in (args.exclude or [])]

    try:
        payload = _build_changed_files(args.repo, args.base, args.head, includes, excludes)
    except GitUnavailableError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 8
    except RuntimeError as exc:
        print(f"[ERROR] diff ref resolution failed: {exc}", file=sys.stderr)
        return 3

    if args.test_hook_force_integrity_mismatch:
        payload["summary"]["total_files"] += 1

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


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except OSError as exc:
        return None, f"failed to read {path}: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid json in {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"invalid json root type in {path}: expected object"
    return payload, None


def _handle_validate(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    required_files = ["run_context.json", "changed_files.json"]
    optional_files = ["ir_merged.json", "features.json"]

    findings: list[dict[str, str]] = []

    def add_finding(level: str, code: str, target: str, detail: str) -> None:
        findings.append({"level": level, "code": code, "target": target, "detail": detail})

    if not run_dir.exists() or not run_dir.is_dir():
        print(f"[ERROR] run directory not found: {run_dir}", file=sys.stderr)
        return 4

    loaded_payloads: dict[str, dict[str, Any]] = {}

    for filename in required_files:
        path = run_dir / filename
        if not path.exists():
            add_finding("ERROR", "QR-COMMON-001", str(path), "missing required file")
            continue
        payload, error = _load_json_file(path)
        if error:
            add_finding("ERROR", "QR-COMMON-001", str(path), error)
            continue
        if payload is not None:
            loaded_payloads[filename] = payload

    for filename in optional_files:
        path = run_dir / filename
        if path.exists():
            payload, error = _load_json_file(path)
            if error:
                add_finding("ERROR", "QR-COMMON-001", str(path), error)
            elif payload is not None:
                loaded_payloads[filename] = payload
        else:
            add_finding("INFO", "QR-COMMON-003", str(path), "optional file not found")

    run_context = loaded_payloads.get("run_context.json", {})
    if run_context and "schema_version" not in run_context:
        add_finding("ERROR", "QR-COMMON-001", "run_context.json", "missing required key: schema_version")
    if run_context and "execution" not in run_context:
        add_finding("ERROR", "QR-COMMON-001", "run_context.json", "missing required key: execution")

    changed_files = loaded_payloads.get("changed_files.json", {})
    if changed_files:
        files = changed_files.get("files")
        summary = changed_files.get("summary")
        if not isinstance(files, list):
            add_finding("ERROR", "QR-COMMON-001", "changed_files.json", "invalid key type: files must be array")
        if not isinstance(summary, dict):
            add_finding("ERROR", "QR-COMMON-001", "changed_files.json", "invalid key type: summary must be object")
        if isinstance(files, list) and isinstance(summary, dict):
            total_files = summary.get("total_files")
            if isinstance(total_files, int) and total_files != len(files):
                add_finding(
                    "ERROR",
                    "QR-COMMON-002",
                    "changed_files.json",
                    "integrity mismatch: summary.total_files != len(files)",
                )

    ir_merged = loaded_payloads.get("ir_merged.json", {})
    if ir_merged:
        endpoints = ir_merged.get("endpoints")
        if not isinstance(endpoints, list):
            add_finding("ERROR", "QR-IR-001", "ir_merged.json", "endpoints must be array")
        else:
            for idx, endpoint in enumerate(endpoints):
                target = f"ir_merged.json:endpoints[{idx}]"
                if not isinstance(endpoint, dict):
                    add_finding("ERROR", "QR-IR-001", target, "endpoint must be object")
                    continue
                for key in ("endpoint_id", "method", "path", "source_evidence"):
                    if key not in endpoint:
                        add_finding("ERROR", "QR-IR-001", target, f"missing required field: {key}")
                method = str(endpoint.get("method", ""))
                if method in {"UNKNOWN", "UNKNOWN_METHOD"}:
                    add_finding("WARN", "QR-IR-002", target, "method is unknown")
                if method == "*":
                    add_finding("WARN", "QR-IR-003", target, "http wildcard method detected")
                source_evidence = endpoint.get("source_evidence")
                if not isinstance(source_evidence, list) or len(source_evidence) == 0:
                    add_finding("ERROR", "QR-IR-004", target, "source_evidence must contain at least one entry")

    features = loaded_payloads.get("features.json", {})
    if features:
        feature_list = features.get("features")
        if not isinstance(feature_list, list):
            add_finding("ERROR", "QR-COMMON-001", "features.json", "features must be array")
        else:
            feature_id_pattern = re.compile(r"^feat_[0-9a-f]{16}(?:_[0-9]{2})?$")
            for idx, feature in enumerate(feature_list):
                target = f"features.json:features[{idx}]"
                if not isinstance(feature, dict):
                    add_finding("ERROR", "QR-COMMON-001", target, "feature must be object")
                    continue
                feature_id = str(feature.get("feature_id", ""))
                if not feature_id_pattern.match(feature_id):
                    add_finding("ERROR", "QR-FEAT-001", target, "invalid feature_id format")
                evidence = feature.get("evidence")
                if not isinstance(evidence, list) or len(evidence) == 0:
                    add_finding("ERROR", "QR-FEAT-002", target, "evidence must contain at least one entry")
                for core_key in ("name", "category", "status"):
                    if str(feature.get(core_key, "UNKNOWN")) == "UNKNOWN":
                        add_finding("WARN", "QR-FEAT-003", target, f"core field is UNKNOWN: {core_key}")

    errors = [item for item in findings if item["level"] == "ERROR"]
    warnings = [item for item in findings if item["level"] == "WARN"]
    infos = [item for item in findings if item["level"] == "INFO"]

    for item in infos:
        print(f"[INFO] {item['code']} {item['target']}: {item['detail']}")

    for item in warnings:
        print(f"[WARN] {item['code']} {item['target']}: {item['detail']}")
    for item in errors:
        print(f"[ERROR] {item['code']} {item['target']}: {item['detail']}", file=sys.stderr)

    if errors:
        _atomic_write_json(
            run_dir / "quality_gate_report.json",
            {
                "status": "error",
                "errors": errors,
                "warnings": warnings,
                "infos": infos,
                "summary": {"error_count": len(errors), "warning_count": len(warnings), "info_count": len(infos)},
            },
        )
        return 4
    if args.strict and warnings:
        print("[ERROR] strict mode enabled and warnings detected", file=sys.stderr)
        _atomic_write_json(
            run_dir / "quality_gate_report.json",
            {
                "status": "error",
                "errors": [],
                "warnings": warnings,
                "infos": infos,
                "summary": {"error_count": 0, "warning_count": len(warnings), "info_count": len(infos)},
            },
        )
        return 4

    _atomic_write_json(
        run_dir / "quality_gate_report.json",
        {
            "status": "ok",
            "errors": [],
            "warnings": warnings,
            "infos": infos,
            "summary": {"error_count": 0, "warning_count": len(warnings), "info_count": len(infos)},
        },
    )
    print(
        "[OK] validation passed "
        f"(required={len(required_files)}, optional_present={len(loaded_payloads) - len(required_files)}, warnings={len(warnings)}, infos={len(infos)})"
    )
    return 0


def _render_api_markdown(ir_payload: dict[str, Any]) -> str:
    schema_version = ir_payload.get("schema_version", "UNKNOWN")
    generated_at = ir_payload.get("generated_at", "UNKNOWN")
    repo = ir_payload.get("repo", {})
    base = repo.get("base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    head = repo.get("head", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    merge_base = repo.get("merge_base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"

    endpoints_raw = ir_payload.get("endpoints", [])
    endpoints: list[dict[str, Any]] = endpoints_raw if isinstance(endpoints_raw, list) else []
    endpoints_sorted = sorted(
        (ep for ep in endpoints if isinstance(ep, dict)),
        key=lambda ep: (
            str(ep.get("path", "UNKNOWN")),
            str(ep.get("method", "UNKNOWN")),
            str(ep.get("endpoint_id", "UNKNOWN")),
        ),
    )

    lines: list[str] = []
    lines.append("# API Overview")
    lines.append(f"- Endpoint Count: `{len(endpoints_sorted)}`")
    lines.append(f"- Generated At: `{generated_at}`")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- schema_version: `{schema_version}`")
    lines.append("- source: `ir_merged.json`")
    lines.append(f"- base/head/merge_base: `{base}` / `{head}` / `{merge_base}`")
    lines.append("")
    lines.append("## Endpoint Index")
    lines.append("| endpoint_id | method | path | handler | auth | feature_id |")
    lines.append("|---|---|---|---|---|---|")
    for ep in endpoints_sorted:
        handler = ep.get("handler", {})
        signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
        lines.append(
            f"| {ep.get('endpoint_id', 'UNKNOWN')} | {ep.get('method', 'UNKNOWN')} | {ep.get('path', 'UNKNOWN')} | "
            f"{signature} | UNKNOWN | UNKNOWN |"
        )

    lines.append("")
    lines.append("## Endpoints")
    for ep in endpoints_sorted:
        endpoint_id = ep.get("endpoint_id", "UNKNOWN")
        method = ep.get("method", "UNKNOWN")
        path = ep.get("path", "UNKNOWN")
        handler = ep.get("handler", {})
        signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
        evidence = ep.get("source_evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        needs_review = ep.get("needs_review", [])
        if not isinstance(needs_review, list):
            needs_review = []

        lines.append(f"### {method} {path} (`{endpoint_id}`)")
        lines.append("")
        lines.append("#### Summary")
        lines.append(f"- Handler: `{signature}`")
        lines.append("- Feature: `UNKNOWN`")
        lines.append("- Status: `unknown`")
        lines.append("")
        lines.append("#### Request")
        lines.append("- Content-Type: `UNKNOWN`")
        lines.append("- Path Params: `UNKNOWN`")
        lines.append("- Query Params: `UNKNOWN`")
        lines.append("- Headers: `UNKNOWN`")
        lines.append("- Body Schema: `UNKNOWN`")
        lines.append("")
        lines.append("#### Response")
        lines.append("- Success: `UNKNOWN`")
        lines.append("- Error: `UNKNOWN`")
        lines.append("- Response Schema: `UNKNOWN`")
        lines.append("")
        lines.append("#### Security")
        lines.append("- Auth Required: `UNKNOWN`")
        lines.append("- Roles/Scopes: `UNKNOWN`")
        lines.append("")
        lines.append("#### Exceptions")
        lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Source Evidence")
        if evidence:
            for ev in evidence:
                if not isinstance(ev, dict):
                    continue
                file_path = ev.get("file", "UNKNOWN")
                symbol = ev.get("symbol", "UNKNOWN")
                line_start = ev.get("line_start", "UNKNOWN")
                line_end = ev.get("line_end", "UNKNOWN")
                annotation = ev.get("annotation", "UNKNOWN")
                lines.append(f"- File: `{file_path}`")
                lines.append(f"- Symbol: `{symbol}`")
                lines.append(f"- Lines: `L{line_start}-L{line_end}`")
                lines.append(f"- Annotation/Signature: `{annotation}`")
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### needs_review")
        if needs_review:
            for item in needs_review:
                lines.append(f"- `{item}`")
        else:
            lines.append("- 없음")
        lines.append("")

    top_needs_review = ir_payload.get("needs_review", [])
    if not isinstance(top_needs_review, list):
        top_needs_review = []

    lines.append("## needs_review")
    if top_needs_review:
        lines.append("| code | endpoint_id/target | detail |")
        lines.append("|---|---|---|")
        for item in top_needs_review:
            if isinstance(item, dict):
                code = item.get("code", "UNKNOWN")
                target = item.get("path", "UNKNOWN")
                detail = item.get("detail", "UNKNOWN")
                lines.append(f"| {code} | {target} | {detail} |")
            else:
                lines.append(f"| UNKNOWN | UNKNOWN | {item} |")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Appendix: Source Evidence Summary")
    lines.append("- 본 문서는 `ir_merged.json` 기준 자동 생성되었다.")
    return "\n".join(lines) + "\n"


def _handle_generate_api(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    payload, error = _load_json_file(input_path)
    if error or payload is None:
        print(f"[ERROR] failed to load input: {error}", file=sys.stderr)
        return 4

    markdown = _render_api_markdown(payload)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write api markdown: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="LAB CLI")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository and build run context")
    analyze_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    analyze_parser.add_argument("--output-dir", required=True, help="Output directory for analysis artifacts")

    generate_parser = subparsers.add_parser("generate", help="Generate markdown artifacts")
    generate_subparsers = generate_parser.add_subparsers(dest="generate_command", metavar="TARGET")
    generate_api_parser = generate_subparsers.add_parser("api", help="Generate API.md")
    generate_api_parser.add_argument("--input", required=True, help="Input ir_merged.json path")
    generate_api_parser.add_argument("--output", required=True, help="Output API.md path")
    generate_subparsers.add_parser("spec", help="Generate SPEC.md")
    generate_subparsers.add_parser("db-schema", help="Generate DB_SCHEMA.md")

    diff_parser = subparsers.add_parser("diff", help="Collect changed files between refs")
    diff_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    diff_parser.add_argument("--base", required=True, help="Base git ref")
    diff_parser.add_argument("--head", required=True, help="Head git ref")
    diff_parser.add_argument("--output", required=True, help="Path to write changed_files.json")
    diff_parser.add_argument("--include", action="append", help="Include path/glob pattern")
    diff_parser.add_argument("--exclude", action="append", help="Exclude path/glob pattern")
    diff_parser.add_argument("--test-hook-force-integrity-mismatch", action="store_true", help=argparse.SUPPRESS)

    validate_parser = subparsers.add_parser("validate", help="Validate generated artifacts")
    validate_parser.add_argument("--run-dir", required=True, help="Directory containing generated artifacts")
    validate_parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

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
    if args.command == "validate":
        return _handle_validate(args)
    if args.command == "generate" and args.generate_command == "api":
        return _handle_generate_api(args)

    # Command implementations will be added in subsequent milestones.
    print(f"[TODO] '{args.command}' command is not implemented yet.")
    return 0
