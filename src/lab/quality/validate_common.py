"""Common validation utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lab.cli_shared import load_json_file


Finding = dict[str, str]


def collect_payloads(run_dir: Path, required_files: list[str], optional_files: list[str]) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    findings: list[Finding] = []
    loaded_payloads: dict[str, dict[str, Any]] = {}

    def add(level: str, code: str, target: str, detail: str) -> None:
        findings.append({"level": level, "code": code, "target": target, "detail": detail})

    for filename in required_files:
        path = run_dir / filename
        if not path.exists():
            add("ERROR", "QR-COMMON-001", str(path), "missing required file")
            continue
        payload, error = load_json_file(path)
        if error:
            add("ERROR", "QR-COMMON-001", str(path), error)
            continue
        if payload is not None:
            loaded_payloads[filename] = payload

    for filename in optional_files:
        path = run_dir / filename
        if path.exists():
            if path.suffix.lower() == ".md":
                continue
            payload, error = load_json_file(path)
            if error:
                add("ERROR", "QR-COMMON-001", str(path), error)
            elif payload is not None:
                loaded_payloads[filename] = payload
        else:
            add("INFO", "QR-COMMON-003", str(path), "optional file not found")

    return loaded_payloads, findings


def validate_run_context(run_context: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if run_context and "schema_version" not in run_context:
        findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": "run_context.json", "detail": "missing required key: schema_version"})
    if run_context and "execution" not in run_context:
        findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": "run_context.json", "detail": "missing required key: execution"})
    return findings


def validate_changed_files(changed_files: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if not changed_files:
        return findings
    files = changed_files.get("files")
    summary = changed_files.get("summary")
    if not isinstance(files, list):
        findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": "changed_files.json", "detail": "invalid key type: files must be array"})
    if not isinstance(summary, dict):
        findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": "changed_files.json", "detail": "invalid key type: summary must be object"})
    if isinstance(files, list) and isinstance(summary, dict):
        total_files = summary.get("total_files")
        if isinstance(total_files, int) and total_files != len(files):
            findings.append({"level": "ERROR", "code": "QR-COMMON-002", "target": "changed_files.json", "detail": "integrity mismatch: summary.total_files != len(files)"})
    return findings


def validate_features(features: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if not features:
        return findings
    feature_list = features.get("features")
    if not isinstance(feature_list, list):
        findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": "features.json", "detail": "features must be array"})
        return findings

    pattern = re.compile(r"^feat_[0-9a-f]{16}(?:_[0-9]{2})?$")
    for idx, feature in enumerate(feature_list):
        target = f"features.json:features[{idx}]"
        if not isinstance(feature, dict):
            findings.append({"level": "ERROR", "code": "QR-COMMON-001", "target": target, "detail": "feature must be object"})
            continue
        feature_id = str(feature.get("feature_id", ""))
        if not pattern.match(feature_id):
            findings.append({"level": "ERROR", "code": "QR-FEAT-001", "target": target, "detail": "invalid feature_id format"})
        evidence = feature.get("evidence")
        if not isinstance(evidence, list) or len(evidence) == 0:
            findings.append({"level": "ERROR", "code": "QR-FEAT-002", "target": target, "detail": "evidence must contain at least one entry"})
        for key in ("name", "category", "status"):
            if str(feature.get(key, "UNKNOWN")) == "UNKNOWN":
                findings.append({"level": "WARN", "code": "QR-FEAT-003", "target": target, "detail": f"core field is UNKNOWN: {key}"})
    return findings
