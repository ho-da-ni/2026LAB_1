"""DB schema artifact validation rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.quality.validate_common import validate_integrity_fingerprint
from lab.shared_utils import load_json_file


Finding = dict[str, str]


TABLE_REQUIRED_KEYS = (
    "table_name",
    "schema_name",
    "columns",
    "primary_key",
    "foreign_keys",
    "indexes",
    "source_evidence",
    "needs_review",
)


COLUMN_REQUIRED_KEYS = (
    "name",
    "data_type",
    "nullable",
    "default",
    "is_primary_key",
    "is_foreign_key",
    "references",
)


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

    for key in ("schema_version", "metadata", "tables", "needs_review", "integrity"):
        if key not in db_schema:
            findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": f"missing required key: {key}"})

    metadata = db_schema.get("metadata")
    if not isinstance(metadata, dict):
        findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": "metadata must be object"})
    elif "generated_at_utc" not in metadata:
        findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": "missing required key: metadata.generated_at_utc"})

    tables = db_schema.get("tables")
    if not isinstance(tables, list):
        findings.append({"level": "ERROR", "code": "QR-DB-001", "target": "db_schema.json", "detail": "tables must be array"})
        return findings

    for index, table in enumerate(tables):
        target = f"db_schema.json:tables[{index}]"
        if not isinstance(table, dict):
            findings.append({"level": "ERROR", "code": "QR-DB-001", "target": target, "detail": "table must be object"})
            continue
        for key in TABLE_REQUIRED_KEYS:
            if key not in table:
                findings.append({"level": "ERROR", "code": "QR-DB-001", "target": target, "detail": f"missing required key: {key}"})

        table_name = str(table.get("table_name", "UNKNOWN"))
        if not table_name:
            findings.append({"level": "ERROR", "code": "QR-DB-002", "target": target, "detail": "table_name must not be empty"})

        columns = table.get("columns")
        if not isinstance(columns, list):
            findings.append({"level": "ERROR", "code": "QR-DB-002", "target": target, "detail": "columns must be array"})
            continue

        table_needs_review = table.get("needs_review", [])
        if not isinstance(table_needs_review, list):
            findings.append({"level": "ERROR", "code": "QR-DB-002", "target": target, "detail": "needs_review must be array"})
            table_needs_review = []

        if table_name == "UNKNOWN" and "needs_review.table_name_unknown" not in table_needs_review:
            findings.append(
                {
                    "level": "WARN",
                    "code": "QR-DB-003",
                    "target": target,
                    "detail": "table_name is UNKNOWN but corresponding needs_review code is missing",
                }
            )
        if len(columns) == 0 and "needs_review.columns_missing" not in table_needs_review:
            findings.append({"level": "WARN", "code": "QR-DB-003", "target": target, "detail": "columns empty without needs_review.columns_missing"})

        source_evidence = table.get("source_evidence")
        if not isinstance(source_evidence, list):
            findings.append({"level": "ERROR", "code": "QR-DB-002", "target": target, "detail": "source_evidence must be array"})
        elif len(source_evidence) == 0:
            findings.append({"level": "WARN", "code": "QR-DB-006", "target": target, "detail": "source_evidence is empty"})

        for col_index, column in enumerate(columns):
            col_target = f"{target}:columns[{col_index}]"
            if not isinstance(column, dict):
                findings.append({"level": "ERROR", "code": "QR-DB-002", "target": col_target, "detail": "column must be object"})
                continue
            for key in COLUMN_REQUIRED_KEYS:
                if key not in column:
                    findings.append({"level": "ERROR", "code": "QR-DB-002", "target": col_target, "detail": f"missing required key: {key}"})
            references = column.get("references")
            if references is not None and not isinstance(references, dict):
                findings.append({"level": "ERROR", "code": "QR-DB-002", "target": col_target, "detail": "references must be object"})

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
        "## Integrity",
        "## Table Index",
        "## Tables",
        "## needs_review",
        "## Appendix: Source Evidence Summary",
    ]:
        if marker not in content:
            findings.append({"level": "ERROR", "code": "QR-DB-004", "target": "DB_SCHEMA.md", "detail": f"missing required section marker: {marker}"})

    if "### " not in content:
        findings.append({"level": "WARN", "code": "QR-DB-005", "target": "DB_SCHEMA.md", "detail": "table detail section is missing"})

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
