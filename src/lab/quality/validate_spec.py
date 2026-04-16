"""SPEC artifact validation rules."""

from __future__ import annotations

from pathlib import Path


Finding = dict[str, str]


def validate_spec_markdown(run_dir: Path) -> list[Finding]:
    markdown_path = run_dir / "SPEC.md"
    if not markdown_path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(markdown_path), "detail": "optional file not found"}]

    try:
        content = markdown_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [{"level": "ERROR", "code": "QR-COMMON-001", "target": str(markdown_path), "detail": f"failed to read markdown: {exc}"}]

    findings: list[Finding] = []
    for marker in ["# Change Specification Overview", "## Diff Summary", "## Feature Changes", "## Validation Plan", "## needs_review"]:
        if marker not in content:
            findings.append({"level": "ERROR", "code": "QR-SPEC-001", "target": "SPEC.md", "detail": f"missing required section marker: {marker}"})
    if "#### Evidence\n- File: `UNKNOWN`" in content:
        findings.append({"level": "ERROR", "code": "QR-SPEC-001", "target": "SPEC.md", "detail": "feature change evidence missing"})
    return findings
