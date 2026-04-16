"""DB schema artifact validation rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.quality.validate_common import validate_integrity_fingerprint
from lab.shared_utils import load_json_file


Finding = dict[str, str]


def validate_db_schema_json(db_schema: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if not db_schema:
        return findings

    findings.extend(
        validate_integrity_fingerprint(
            db_schema,
            target="db_schema.json",
            required_excludes=["metadata.generated_at_utc"],
        )
    )

    for key in ("schema_version", "metadata", "tables", "needs_review"):
        if key not in db_schema:
            findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": f"missing required key: {key}"})

    tables = db_schema.get("tables")
    if not isinstance(tables, list):
        findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": "tables must be array"})
        return findings

    for index, table in enumerate(tables):
        target = f"db_schema.json:tables[{index}]"
        if not isinstance(table, dict):
            findings.append({"level": "ERROR", "code": "QR-DB-001", "target": target, "detail": "table must be object"})
            continue
        for key in ("table_name", "schema_name", "columns", "primary_key", "foreign_keys", "indexes", "needs_review"):
            if key not in table:
                findings.append({"level": "ERROR", "code": "QR-DB-001", "target": target, "detail": f"missing required key: {key}"})
        columns = table.get("columns")
        if not isinstance(columns, list):
            findings.append({"level": "ERROR", "code": "QR-DB-002", "target": target, "detail": "columns must be array"})
            continue
        if str(table.get("table_name", "UNKNOWN")) == "UNKNOWN" and "needs_review.table_name_unknown" not in table.get("needs_review", []):
            findings.append(
                {
                    "level": "WARN",
                    "code": "QR-DB-003",
                    "target": target,
                    "detail": "table_name is UNKNOWN but corresponding needs_review code is missing",
                }
            )
        if len(columns) == 0 and "needs_review.columns_missing" not in table.get("needs_review", []):
            findings.append({"level": "WARN", "code": "QR-DB-003", "target": target, "detail": "columns empty without needs_review.columns_missing"})
        for col_index, column in enumerate(columns):
            col_target = f"{target}:columns[{col_index}]"
            if not isinstance(column, dict):
                findings.append({"level": "ERROR", "code": "QR-DB-002", "target": col_target, "detail": "column must be object"})
                continue
            for key in ("name", "data_type", "nullable", "default", "is_primary_key", "is_foreign_key", "references"):
                if key not in column:
                    findings.append({"level": "ERROR", "code": "QR-DB-002", "target": col_target, "detail": f"missing required key: {key}"})
    return findings


def validate_db_markdown(run_dir: Path) -> list[Finding]:
    markdown_path = run_dir / "DB_SCHEMA.md"
    if not markdown_path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(markdown_path), "detail": "optional file not found"}]

    try:
        content = markdown_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [{"level": "ERROR", "code": "QR-COMMON-001", "target": str(markdown_path), "detail": f"failed to read markdown: {exc}"}]

    findings: list[Finding] = []
    for marker in [
        "# DB Schema Overview",
        "## Metadata",
        "## Table Index",
        "## Tables",
        "## needs_review",
        "## Appendix: Source Evidence Summary",
    ]:
        if marker not in content:
            findings.append({"level": "ERROR", "code": "QR-DB-004", "target": "DB_SCHEMA.md", "detail": f"missing required section marker: {marker}"})

    if "`UNKNOWN`" in content and "needs_review" in content and "## needs_review\n- 없음" in content:
        findings.append(
            {
                "level": "WARN",
                "code": "QR-DB-005",
                "target": "DB_SCHEMA.md",
                "detail": "UNKNOWN value exists but top-level needs_review is empty",
            }
        )
    return findings


def load_and_validate_db_schema_json(run_dir: Path) -> list[Finding]:
    path = run_dir / "db_schema.json"
    if not path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(path), "detail": "optional file not found"}]
    payload, error = load_json_file(path)
    if error or payload is None:
        return [{"level": "ERROR", "code": "QR-COMMON-001", "target": str(path), "detail": error or "failed to load db_schema.json"}]
    return validate_db_schema_json(payload)
