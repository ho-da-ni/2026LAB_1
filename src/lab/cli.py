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

from lab.controller_detection import detect_endpoints_from_fixture

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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collect_repo_meta(repo: str) -> dict[str, Any]:
    remotes: dict[str, dict[str, str]] = {}
    try:
        remote_lines = _run_git(repo, ["remote", "-v"]).splitlines()
    except (RuntimeError, GitUnavailableError):
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

    default_branch_raw = _git_value(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    default_branch = default_branch_raw.split("/")[-1] if default_branch_raw != "UNKNOWN" else "UNKNOWN"

    head_commit = _git_value(repo, "rev-parse", "HEAD")
    head_branch = _git_value(repo, "rev-parse", "--abbrev-ref", "HEAD")
    head_tag = _git_value(repo, "describe", "--tags", "--exact-match", "HEAD")
    dirty_raw = _git_value(repo, "status", "--porcelain")
    dirty = "UNKNOWN" if dirty_raw == "UNKNOWN" else ("true" if dirty_raw else "false")

    repo_path = Path(repo)
    tracked_files_output = _git_value(repo, "ls-files")
    tracked_files = sorted([_normalize_path(line) for line in tracked_files_output.splitlines() if line.strip()]) if tracked_files_output != "UNKNOWN" else []

    language_bytes: dict[str, int] = {}
    language_files: dict[str, int] = {}
    for rel in tracked_files:
        if _is_default_excluded(rel):
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

    codeowners_candidates = ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
    codeowners_path = "UNKNOWN"
    for candidate in codeowners_candidates:
        if (repo_path / candidate).exists():
            codeowners_path = _normalize_path(candidate)
            break

    license_path = "UNKNOWN"
    for entry in sorted(repo_path.iterdir(), key=lambda p: p.name):
        if entry.is_file() and entry.name.upper().startswith("LICENSE"):
            license_path = entry.name
            break

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "repo_id": repo_id,
        "collected_at_utc": _utc_now_iso(),
        "vcs": "git",
        "default_branch": default_branch,
        "remotes": remote_list,
        "head": {
            "commit": head_commit,
            "branch": head_branch,
            "tag": head_tag,
            "dirty": dirty,
        },
        "history_window": {
            "base_commit": "UNKNOWN",
            "target_commit": head_commit,
            "commit_count": "UNKNOWN",
        },
        "code_stats": {
            "file_count": sum(language_files.values()),
            "language_bytes": dict(sorted(language_bytes.items())),
            "language_files": dict(sorted(language_files.items())),
        },
        "ownership": {
            "codeowners_path": codeowners_path,
            "teams": [],
        },
        "constraints": {
            "license": license_path,
            "runtime_versions": {"python": "UNKNOWN", "node": "UNKNOWN"},
        },
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy_version": "1.0.0",
        },
        "needs_review": [],
    }
    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("collected_at_utc", None)
    fingerprint_source = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    payload["integrity"]["fingerprint"] = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    return payload


def _build_scan_index(output_dir: Path) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for file_path in sorted([p for p in output_dir.rglob("*") if p.is_file()], key=lambda p: p.as_posix()):
        rel_path = _normalize_path(str(file_path.relative_to(output_dir)))
        artifacts.append(
            {
                "path": rel_path,
                "size_bytes": file_path.stat().st_size,
                "sha256": _sha256_file(file_path),
            }
        )

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": _utc_now_iso(),
        "root": _normalize_path(str(output_dir)),
        "summary": {"total_files": len(artifacts)},
        "artifacts": artifacts,
        "integrity": {"fingerprint": "UNKNOWN", "fingerprint_policy_version": "1.0.0"},
    }
    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("generated_at_utc", None)
    fingerprint_source = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    payload["integrity"]["fingerprint"] = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    return payload


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
        repo_meta = _collect_repo_meta(args.repo)
        _atomic_write_json(output_dir / "run_context.json", run_context)
        _atomic_write_json(output_dir / "repo_meta.json", repo_meta)
        scan_index = _build_scan_index(output_dir)
        _atomic_write_json(output_dir / "scan_index.json", scan_index)
    except OSError as exc:
        print(f"[ERROR] failed to write analyze artifacts: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_dir / 'run_context.json'}")
    print(f"Generated: {output_dir / 'repo_meta.json'}")
    print(f"Generated: {output_dir / 'scan_index.json'}")
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
    optional_files = ["ir_merged.json", "features.json", "API.md", "SPEC.md"]

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
            if path.suffix.lower() == ".md":
                continue
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

    for markdown_name, required_markers in {
        "API.md": ["# API Overview", "## Endpoint Index", "## Endpoints", "## needs_review", "## Appendix: Source Evidence Summary"],
        "SPEC.md": ["# Change Specification Overview", "## Diff Summary", "## Feature Changes", "## Validation Plan", "## needs_review"],
    }.items():
        markdown_path = run_dir / markdown_name
        if not markdown_path.exists():
            add_finding("INFO", "QR-COMMON-003", str(markdown_path), "optional file not found")
            continue
        try:
            content = markdown_path.read_text(encoding="utf-8")
        except OSError as exc:
            add_finding("ERROR", "QR-COMMON-001", str(markdown_path), f"failed to read markdown: {exc}")
            continue
        for marker in required_markers:
            if marker not in content:
                code = "QR-API-001" if markdown_name == "API.md" else "QR-SPEC-001"
                add_finding("ERROR", code, markdown_name, f"missing required section marker: {marker}")
        if markdown_name == "API.md":
            if "### * " in content:
                add_finding("WARN", "QR-API-002", markdown_name, "wildcard method endpoint section detected")
            if "#### Source Evidence\n- `UNKNOWN`" in content:
                add_finding("ERROR", "QR-API-004", markdown_name, "endpoint contains missing source evidence block")
        if markdown_name == "SPEC.md":
            if "#### Evidence\n- File: `UNKNOWN`" in content:
                add_finding("ERROR", "QR-SPEC-001", markdown_name, "feature change evidence missing")

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


def _render_api_markdown(ir_payload: dict[str, Any], features_payload: dict[str, Any] | None = None) -> str:
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

    feature_by_endpoint: dict[str, str] = {}
    if isinstance(features_payload, dict):
        raw_features = features_payload.get("features", [])
        if isinstance(raw_features, list):
            for feature in raw_features:
                if not isinstance(feature, dict):
                    continue
                feature_id = str(feature.get("feature_id", "UNKNOWN"))
                signals = feature.get("signals", {})
                endpoint_ids = signals.get("endpoints", []) if isinstance(signals, dict) else []
                if not isinstance(endpoint_ids, list):
                    continue
                for endpoint_id in endpoint_ids:
                    feature_by_endpoint[str(endpoint_id)] = feature_id

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
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        feature_id = feature_by_endpoint.get(endpoint_id, "UNKNOWN")
        lines.append(
            f"| {ep.get('endpoint_id', 'UNKNOWN')} | {ep.get('method', 'UNKNOWN')} | {ep.get('path', 'UNKNOWN')} | "
            f"{signature} | UNKNOWN | {feature_id} |"
        )

    lines.append("")
    lines.append("## Endpoints")
    for ep in endpoints_sorted:
        endpoint_id = ep.get("endpoint_id", "UNKNOWN")
        method = ep.get("method", "UNKNOWN")
        path = ep.get("path", "UNKNOWN")
        handler = ep.get("handler", {})
        signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
        feature_id = feature_by_endpoint.get(str(endpoint_id), "UNKNOWN")
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
        lines.append(f"- Feature: `{feature_id}`")
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
        if method == "*":
            lines.append("- `needs_review.http_wildcard`")
        if method in {"UNKNOWN", "UNKNOWN_METHOD"}:
            lines.append("- `needs_review.method_unknown`")
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

    features_payload: dict[str, Any] | None = None
    if getattr(args, "features", None):
        feature_payload, feature_error = _load_json_file(Path(args.features))
        if feature_error or feature_payload is None:
            print(f"[ERROR] failed to load features input: {feature_error}", file=sys.stderr)
            return 4
        features_payload = feature_payload

    markdown = _render_api_markdown(payload, features_payload=features_payload)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write api markdown: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_path}")
    return 0


def _render_spec_markdown(changed_files_payload: dict[str, Any], features_payload: dict[str, Any], ir_payload: dict[str, Any]) -> str:
    repo = changed_files_payload.get("repo", {})
    base = repo.get("base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    head = repo.get("head", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    merge_base = repo.get("merge_base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    files = changed_files_payload.get("files", [])
    file_rows = sorted((item for item in files if isinstance(item, dict)), key=lambda item: str(item.get("path", "UNKNOWN"))) if isinstance(files, list) else []
    features = features_payload.get("features", [])
    features_rows = sorted(
        (item for item in features if isinstance(item, dict)),
        key=lambda item: (str(item.get("category", "UNKNOWN")), str(item.get("name", "UNKNOWN")), str(item.get("feature_id", "UNKNOWN"))),
    ) if isinstance(features, list) else []

    ir_endpoints = ir_payload.get("endpoints", [])
    endpoint_map: dict[str, dict[str, Any]] = {}
    if isinstance(ir_endpoints, list):
        endpoint_map = {str(ep.get("endpoint_id", "")): ep for ep in ir_endpoints if isinstance(ep, dict)}

    lines: list[str] = []
    lines.append("# Change Specification Overview")
    lines.append("- Project: `UNKNOWN`")
    lines.append(f"- Feature Change Count: `{len(features_rows)}`")
    lines.append(f"- Changed Files: `{len(file_rows)}`")
    lines.append(f"- Generated At: `{_utc_now_iso()}`")
    lines.append("")
    lines.append("## Metadata")
    lines.append("- schema_version: `1.0.0`")
    lines.append(f"- base/head/merge_base: `{base}` / `{head}` / `{merge_base}`")
    lines.append("- inputs: `changed_files.json`, `features.json`, `ir_merged.json`")
    lines.append("")
    lines.append("## Diff Summary")
    lines.append("| path | change_type | language | feature_id | evidence_ref |")
    lines.append("|---|---|---|---|---|")
    for row in file_rows:
        lines.append(
            f"| {row.get('path', 'UNKNOWN')} | {row.get('status', 'UNKNOWN')} | {row.get('language', 'UNKNOWN')} | UNKNOWN | {row.get('path', 'UNKNOWN')} |"
        )
    lines.append("")
    lines.append("## Feature Changes")
    for feature in features_rows:
        feature_id = str(feature.get("feature_id", "UNKNOWN"))
        name = str(feature.get("name", "UNKNOWN"))
        lines.append(f"### {name} (`{feature_id}`)")
        lines.append("")
        lines.append("#### Change Intent")
        lines.append("- 변경 목적: `UNKNOWN`")
        lines.append("")
        lines.append("#### Affected Files")
        evidence = feature.get("evidence", [])
        evidence_rows = evidence if isinstance(evidence, list) else []
        if evidence_rows:
            for ev in evidence_rows:
                if not isinstance(ev, dict):
                    continue
                source = ev.get("source", {})
                source_file = source.get("file", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                lines.append(f"- `{source_file}` (`UNKNOWN`)")
        else:
            lines.append("- `UNKNOWN` (`UNKNOWN`)")
        lines.append("")
        lines.append("#### Behavior Delta")
        lines.append("- Before: `UNKNOWN`")
        lines.append("- After: `UNKNOWN`")
        lines.append("- Trigger/Condition: `UNKNOWN`")
        lines.append("")
        lines.append("#### Contract Delta")
        lines.append("- Input Contract: `UNKNOWN`")
        lines.append("- Output Contract: `UNKNOWN`")
        lines.append("- Error/Exception Contract: `UNKNOWN`")
        lines.append("")
        lines.append("#### Dependency/Impact")
        lines.append("- Upstream Impact: `UNKNOWN`")
        lines.append("- Downstream Impact: `UNKNOWN`")
        lines.append("")
        lines.append("#### Evidence")
        if evidence_rows:
            for ev in evidence_rows:
                if not isinstance(ev, dict):
                    continue
                source = ev.get("source", {})
                source_file = source.get("file", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                symbol = source.get("symbol", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                line_start = source.get("line_start", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                line_end = source.get("line_end", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                lines.append(f"- File: `{source_file}`")
                lines.append(f"- Symbol: `{symbol}`")
                lines.append(f"- Lines: `L{line_start}-L{line_end}`")
                lines.append("- Diff Hunk: `UNKNOWN`")
        else:
            lines.append("- File: `UNKNOWN`")
            lines.append("- Symbol: `UNKNOWN`")
            lines.append("- Lines: `UNKNOWN`")
            lines.append("- Diff Hunk: `UNKNOWN`")
        lines.append("")
        lines.append("#### needs_review")
        if not evidence_rows:
            lines.append("- `needs_review.evidence_missing`")
        lines.append("- `needs_review.spec_unknown_contract`")
        lines.append("")

    lines.append("## Interface/API Changes (Optional)")
    lines.append("| endpoint_id | method | path | handler | feature_id |")
    lines.append("|---|---|---|---|---|")
    for feature in features_rows:
        feature_id = str(feature.get("feature_id", "UNKNOWN"))
        signals = feature.get("signals", {})
        endpoint_ids = signals.get("endpoints", []) if isinstance(signals, dict) else []
        if not isinstance(endpoint_ids, list):
            continue
        for endpoint_id in sorted(str(item) for item in endpoint_ids):
            endpoint = endpoint_map.get(endpoint_id, {})
            handler = endpoint.get("handler", {})
            signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
            lines.append(
                f"| {endpoint_id} | {endpoint.get('method', 'UNKNOWN')} | {endpoint.get('path', 'UNKNOWN')} | {signature} | {feature_id} |"
            )
    lines.append("")
    lines.append("## Data/Schema Changes (Optional)")
    lines.append("- `UNKNOWN`")
    lines.append("")
    lines.append("## Risk & Compatibility")
    lines.append("- breaking_change: `unknown`")
    lines.append("- rollout_risk: `unknown`")
    lines.append("- rollback_plan: `UNKNOWN`")
    lines.append("")
    lines.append("## Validation Plan")
    lines.append("- Command: `PYTHONPATH=src pytest -q`")
    lines.append("- Expected: `PASS`")
    lines.append("- Actual: `UNKNOWN`")
    lines.append("")
    lines.append("## needs_review")
    lines.append("| code | target | detail | evidence_ref |")
    lines.append("|---|---|---|---|")
    lines.append("| needs_review.spec_unknown_contract | SPEC | UNKNOWN contract fields included | SPEC.md |")
    lines.append("")
    lines.append("## Appendix: Evidence Index")
    lines.append("| file path | ref_count | symbols |")
    lines.append("|---|---:|---|")
    evidence_index: dict[str, set[str]] = {}
    for feature in features_rows:
        evidence = feature.get("evidence", [])
        if not isinstance(evidence, list):
            continue
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            source = ev.get("source", {})
            if not isinstance(source, dict):
                continue
            file_path = str(source.get("file", "UNKNOWN"))
            symbol = str(source.get("symbol", "UNKNOWN"))
            evidence_index.setdefault(file_path, set()).add(symbol)
    for file_path in sorted(evidence_index):
        symbols = sorted(evidence_index[file_path])
        lines.append(f"| {file_path} | {len(symbols)} | {', '.join(symbols)} |")
    if not evidence_index:
        lines.append("| UNKNOWN | 0 | UNKNOWN |")
    return "\n".join(lines) + "\n"


def _handle_generate_spec(args: argparse.Namespace) -> int:
    changed_payload, changed_error = _load_json_file(Path(args.changed_files))
    if changed_error or changed_payload is None:
        print(f"[ERROR] failed to load changed_files input: {changed_error}", file=sys.stderr)
        return 4
    features_payload, features_error = _load_json_file(Path(args.features))
    if features_error or features_payload is None:
        print(f"[ERROR] failed to load features input: {features_error}", file=sys.stderr)
        return 4
    ir_payload, ir_error = _load_json_file(Path(args.ir))
    if ir_error or ir_payload is None:
        print(f"[ERROR] failed to load ir input: {ir_error}", file=sys.stderr)
        return 4

    markdown = _render_spec_markdown(changed_payload, features_payload, ir_payload)
    output_path = Path(args.output)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write spec markdown: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_path}")
    return 0


def _handle_detect_endpoints(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    case_ids = args.case_id or []
    try:
        payload = detect_endpoints_from_fixture(input_path, case_ids=case_ids)
    except OSError as exc:
        print(f"[ERROR] failed to read fixture input: {exc}", file=sys.stderr)
        return 4
    except json.JSONDecodeError as exc:
        print(f"[ERROR] invalid fixture json: {exc}", file=sys.stderr)
        return 4
    except ValueError as exc:
        print(f"[ERROR] invalid fixture format: {exc}", file=sys.stderr)
        return 4

    try:
        _atomic_write_json(output_path, payload)
    except OSError as exc:
        print(f"[ERROR] failed to write endpoints.json: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_path}")
    return 0


def _normalize_endpoint_evidence(evidence: Any) -> list[dict[str, Any]]:
    items = evidence if isinstance(evidence, list) else []
    normalized: list[dict[str, Any]] = []
    for ev in items:
        if not isinstance(ev, dict):
            continue
        normalized.append(
            {
                "file": str(ev.get("file", "UNKNOWN")),
                "symbol": str(ev.get("symbol", "UNKNOWN")),
                "line_start": ev.get("line_start", "UNKNOWN"),
                "line_end": ev.get("line_end", "UNKNOWN"),
                "annotation": str(ev.get("annotation", "UNKNOWN")),
            }
        )
    normalized = sorted(
        normalized,
        key=lambda ev: (str(ev["file"]), str(ev["symbol"]), str(ev["line_start"]), str(ev["line_end"])),
    )
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for ev in normalized:
        key = (str(ev["file"]), str(ev["symbol"]), str(ev["line_start"]), str(ev["line_end"]), str(ev["annotation"]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    return unique


def _build_ir_merged(endpoints_payload: dict[str, Any], repo_base: str, repo_head: str, repo_merge_base: str) -> dict[str, Any]:
    raw_endpoints = endpoints_payload.get("endpoints", [])
    endpoints = raw_endpoints if isinstance(raw_endpoints, list) else []

    merged_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: dict[tuple[str, str], set[str]] = {}

    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        method = str(ep.get("method", "UNKNOWN")).upper()
        path = str(ep.get("path", "UNKNOWN"))
        framework = str(ep.get("framework", "UNKNOWN"))
        handler_signature = str(ep.get("handler", "UNKNOWN"))
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        needs_review = ep.get("needs_review", [])
        if not isinstance(needs_review, list):
            needs_review = []
        source_evidence = _normalize_endpoint_evidence(ep.get("source_evidence", []))
        key = (method, path)

        if key in merged_by_key:
            current = merged_by_key[key]
            current_handler = current["handler"]["signature"]
            if current_handler != handler_signature:
                conflicts.setdefault(key, {current_handler}).add(handler_signature)
                continue
            current["source_evidence"] = _normalize_endpoint_evidence(current["source_evidence"] + source_evidence)
            current["needs_review"] = sorted(set(current["needs_review"]) | set(str(item) for item in needs_review))
            continue

        merged_by_key[key] = {
            "endpoint_id": endpoint_id,
            "handler": {"signature": handler_signature, "framework": framework},
            "method": method,
            "path": path,
            "paths": [path],
            "methods": [method],
            "produces": [],
            "consumes": [],
            "source_evidence": source_evidence,
            "needs_review": sorted(set(str(item) for item in needs_review)),
        }

    merged_endpoints = sorted(
        merged_by_key.values(),
        key=lambda item: (str(item["path"]), str(item["method"]), str(item["endpoint_id"])),
    )
    top_needs_review: list[dict[str, Any]] = []
    for (method, path), handlers in sorted(conflicts.items(), key=lambda item: (item[0][1], item[0][0])):
        top_needs_review.append(
            {
                "code": "needs_review.mapping_route_conflict",
                "method": method,
                "path": path,
                "handlers": sorted(handlers),
                "detail": "동일 METHOD+PATH에 handler 충돌",
            }
        )

    return {
        "schema_version": "1.0.0",
        "generated_at": _utc_now_iso(),
        "repo": {"base": repo_base, "head": repo_head, "merge_base": repo_merge_base},
        "endpoints": merged_endpoints,
        "needs_review": top_needs_review,
    }


def _build_feature_id(category: str, name: str, endpoint_ids: list[str], tables: list[str], tags: list[str]) -> str:
    normalized_name = name.strip().lower()
    source = json.dumps(
        [category, normalized_name, sorted(set(endpoint_ids)), sorted(set(tables)), sorted(set(tags))],
        ensure_ascii=False,
        sort_keys=True,
    )
    return "feat_" + hashlib.sha1(source.encode("utf-8")).hexdigest()[:16]


def _build_features(ir_merged_payload: dict[str, Any]) -> dict[str, Any]:
    endpoints = ir_merged_payload.get("endpoints", [])
    endpoint_list = endpoints if isinstance(endpoints, list) else []
    features: list[dict[str, Any]] = []

    for ep in endpoint_list:
        if not isinstance(ep, dict):
            continue
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        path = str(ep.get("path", "UNKNOWN"))
        method = str(ep.get("method", "UNKNOWN"))
        handler = ep.get("handler", {})
        signature = str(handler.get("signature", "UNKNOWN")) if isinstance(handler, dict) else "UNKNOWN"
        feature_name = path if path != "UNKNOWN" else signature
        category = "api"
        tags = sorted(set([method.lower()])) if method != "UNKNOWN" else []
        evidence: list[dict[str, Any]] = []
        for ev in ep.get("source_evidence", []):
            if not isinstance(ev, dict):
                continue
            evidence.append(
                {
                    "type": "code",
                    "source": {
                        "file": str(ev.get("file", "UNKNOWN")),
                        "symbol": str(ev.get("symbol", "UNKNOWN")),
                        "line_start": ev.get("line_start", "UNKNOWN"),
                        "line_end": ev.get("line_end", "UNKNOWN"),
                    },
                    "snippet_hash": "UNKNOWN",
                    "confidence": "medium",
                    "note": str(ev.get("annotation", "UNKNOWN")),
                }
            )
        evidence = sorted(
            evidence,
            key=lambda item: (
                str(item["type"]),
                str(item["source"]["file"]),
                str(item["source"]["symbol"]),
                str(item["source"]["line_start"]),
                str(item["source"]["line_end"]),
            ),
        )
        feature = {
            "feature_id": _build_feature_id(category, feature_name, [endpoint_id], [], tags),
            "name": feature_name if feature_name else "UNKNOWN",
            "category": category,
            "status": "unknown",
            "description": "UNKNOWN",
            "tags": tags,
            "owners": [],
            "signals": {"endpoints": [endpoint_id], "tables": [], "jobs": []},
            "evidence": evidence,
            "needs_review": [],
        }
        if not evidence:
            feature["needs_review"].append("needs_review.evidence_missing")
        if feature["name"] == "UNKNOWN":
            feature["needs_review"].append("needs_review.feature_name_unknown")
        features.append(feature)

    features = sorted(features, key=lambda item: (str(item["category"]), str(item["name"]), str(item["feature_id"])))
    return {
        "schema_version": "1.0.0",
        "generated_at": _utc_now_iso(),
        "repo": ir_merged_payload.get("repo", {"base": "UNKNOWN", "head": "UNKNOWN", "merge_base": "UNKNOWN"}),
        "features": features,
    }


def _handle_build_w4(args: argparse.Namespace) -> int:
    endpoints_payload, error = _load_json_file(Path(args.endpoints_input))
    if error or endpoints_payload is None:
        print(f"[ERROR] failed to load endpoints input: {error}", file=sys.stderr)
        return 4

    ir_merged_payload = _build_ir_merged(endpoints_payload, args.base, args.head, args.merge_base)
    features_payload = _build_features(ir_merged_payload)
    output_dir = Path(args.output_dir)
    try:
        _atomic_write_json(output_dir / "ir_merged.json", ir_merged_payload)
        _atomic_write_json(output_dir / "features.json", features_payload)
    except OSError as exc:
        print(f"[ERROR] failed to write W4 artifacts: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_dir / 'ir_merged.json'}")
    print(f"Generated: {output_dir / 'features.json'}")
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
    generate_api_parser.add_argument("--features", help="Optional features.json path for endpoint-feature mapping")
    generate_spec_parser = generate_subparsers.add_parser("spec", help="Generate SPEC.md")
    generate_spec_parser.add_argument("--changed-files", required=True, help="Input changed_files.json path")
    generate_spec_parser.add_argument("--features", required=True, help="Input features.json path")
    generate_spec_parser.add_argument("--ir", required=True, help="Input ir_merged.json path")
    generate_spec_parser.add_argument("--output", required=True, help="Output SPEC.md path")
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

    detect_parser = subparsers.add_parser("detect-endpoints", help="Detect endpoints from controller fixtures")
    detect_parser.add_argument("--input", required=True, help="Input fixture json path")
    detect_parser.add_argument("--output", required=True, help="Output endpoints.json path")
    detect_parser.add_argument("--case-id", action="append", help="Fixture case id filter (repeatable)")

    w4_parser = subparsers.add_parser("build-w4", help="Build W4 artifacts (ir_merged.json, features.json)")
    w4_parser.add_argument("--endpoints-input", required=True, help="Input endpoints.json path")
    w4_parser.add_argument("--output-dir", required=True, help="Output directory")
    w4_parser.add_argument("--base", default="UNKNOWN", help="Repo base ref")
    w4_parser.add_argument("--head", default="UNKNOWN", help="Repo head ref")
    w4_parser.add_argument("--merge-base", default="UNKNOWN", help="Repo merge-base ref")

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
    if args.command == "detect-endpoints":
        return _handle_detect_endpoints(args)
    if args.command == "build-w4":
        return _handle_build_w4(args)
    if args.command == "generate" and args.generate_command == "api":
        return _handle_generate_api(args)
    if args.command == "generate" and args.generate_command == "spec":
        return _handle_generate_spec(args)

    # Command implementations will be added in subsequent milestones.
    print(f"[TODO] '{args.command}' command is not implemented yet.")
    return 0
