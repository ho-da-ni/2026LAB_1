"""API artifact validation rules."""

from __future__ import annotations

from pathlib import Path

from lab.quality.validate_common import validate_integrity_fingerprint

Finding = dict[str, str]


def validate_ir_merged(ir_merged: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not ir_merged:
        return findings
    findings.extend(
        validate_integrity_fingerprint(
            ir_merged,
            target="ir_merged.json",
            required_excludes=["metadata.generated_at_utc"],
        )
    )
    endpoints = ir_merged.get("endpoints")
    if not isinstance(endpoints, list):
        findings.append({"level": "ERROR", "code": "QR-IR-001", "target": "ir_merged.json", "detail": "endpoints must be array"})
        return findings

    for idx, endpoint in enumerate(endpoints):
        target = f"ir_merged.json:endpoints[{idx}]"
        if not isinstance(endpoint, dict):
            findings.append({"level": "ERROR", "code": "QR-IR-001", "target": target, "detail": "endpoint must be object"})
            continue
        for key in ("endpoint_id", "method", "path", "source_evidence"):
            if key not in endpoint:
                findings.append({"level": "ERROR", "code": "QR-IR-001", "target": target, "detail": f"missing required field: {key}"})
        method = str(endpoint.get("method", ""))
        if method in {"UNKNOWN", "UNKNOWN_METHOD"}:
            findings.append({"level": "WARN", "code": "QR-IR-002", "target": target, "detail": "method is unknown"})
        if method == "*":
            findings.append({"level": "WARN", "code": "QR-IR-003", "target": target, "detail": "http wildcard method detected"})
        source_evidence = endpoint.get("source_evidence")
        if not isinstance(source_evidence, list) or len(source_evidence) == 0:
            findings.append({"level": "ERROR", "code": "QR-IR-004", "target": target, "detail": "source_evidence must contain at least one entry"})
    return findings


def validate_api_markdown(run_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    markdown_path = run_dir / "API.md"
    if not markdown_path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(markdown_path), "detail": "optional file not found"}]

    try:
        content = markdown_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [{"level": "ERROR", "code": "QR-COMMON-001", "target": str(markdown_path), "detail": f"failed to read markdown: {exc}"}]

    for marker in ["# API Overview", "## Endpoint Index", "## Endpoints", "## needs_review", "## Appendix: Source Evidence Summary"]:
        if marker not in content:
            findings.append({"level": "ERROR", "code": "QR-API-001", "target": "API.md", "detail": f"missing required section marker: {marker}"})
    if "### * " in content:
        findings.append({"level": "WARN", "code": "QR-API-002", "target": "API.md", "detail": "wildcard method endpoint section detected"})
    if "#### Source Evidence\n- `UNKNOWN`" in content:
        findings.append({"level": "ERROR", "code": "QR-API-004", "target": "API.md", "detail": "endpoint contains missing source evidence block"})
    return findings
