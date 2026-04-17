"""DB schema artifact validation rules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lab.shared_utils import load_json_file


Finding = dict[str, str]

TOP_LEVEL_REQUIRED = ("schema_version", "source", "database", "owners", "tables", "notes", "needs_review")
SOURCE_REQUIRED = ("collector", "collected_at", "dictionary_views")
DATABASE_REQUIRED = ("vendor", "host", "port", "service_name", "sid")
TABLE_REQUIRED = ("table_id", "owner", "table_name", "table_comment", "columns", "primary_key", "foreign_keys", "evidence", "needs_review", "unknown")
COLUMN_REQUIRED = ("name", "ordinal_position", "data_type", "nullable", "needs_review", "unknown", "evidence")
PK_REQUIRED = ("constraint_name", "columns", "evidence", "needs_review", "unknown")
FK_REQUIRED = ("fk_id", "constraint_name", "columns", "referenced_owner", "referenced_table", "column_mapping", "evidence", "needs_review", "unknown")

TABLE_ID_PATTERN = re.compile(r"^[A-Z0-9_$.]+\.[A-Z0-9_$.]+$")
FK_ID_PATTERN = re.compile(r"^[A-Z0-9_$.]+\.[A-Z0-9_$.]+\.[A-Z0-9_$.]+$")


def _add(findings: list[Finding], level: str, code: str, target: str, detail: str) -> None:
    findings.append({"level": level, "code": code, "target": target, "detail": detail})


def _validate_evidence_array(evidence: Any, *, findings: list[Finding], target: str) -> None:
    if not isinstance(evidence, list) or len(evidence) == 0:
        _add(findings, "ERROR", "QR-DB-002", target, "evidence must be non-empty array")
        return
    for idx, item in enumerate(evidence):
        row_target = f"{target}:evidence[{idx}]"
        if not isinstance(item, dict):
            _add(findings, "ERROR", "QR-DB-002", row_target, "evidence row must be object")
            continue
        for key in ("source_view", "owner", "object_name", "row_ref"):
            if key not in item:
                _add(findings, "ERROR", "QR-DB-002", row_target, f"missing required key: {key}")


def _validate_against_schema_file(db_schema: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    schema_path = Path("db_schema.schema.json")
    if not schema_path.exists():
        return [{"level": "ERROR", "code": "QR-DB-007", "target": "db_schema.schema.json", "detail": "schema file not found"}]

    payload, error = load_json_file(schema_path)
    if error or payload is None:
        return [{"level": "ERROR", "code": "QR-DB-007", "target": "db_schema.schema.json", "detail": error or "failed to load schema file"}]

    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        _add(findings, "ERROR", "QR-DB-007", "db_schema.schema.json", "unsupported $schema value")

    required = payload.get("required")
    if not isinstance(required, list):
        _add(findings, "ERROR", "QR-DB-007", "db_schema.schema.json", "schema.required must be array")
        return findings

    for key in required:
        if key not in db_schema:
            _add(findings, "ERROR", "QR-DB-001", "db_schema.json", f"missing required key (schema): {key}")
    return findings


def validate_db_schema_json(db_schema: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if not db_schema:
        return findings

    findings.extend(_validate_against_schema_file(db_schema))

    for key in TOP_LEVEL_REQUIRED:
        if key not in db_schema:
            _add(findings, "ERROR", "QR-DB-001", "db_schema.json", f"missing required key: {key}")

    if db_schema.get("schema_version") != "w6.db_schema.v1":
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "schema_version must be w6.db_schema.v1")

    source = db_schema.get("source")
    if not isinstance(source, dict):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "source must be object")
    else:
        for key in SOURCE_REQUIRED:
            if key not in source:
                _add(findings, "ERROR", "QR-DB-001", "db_schema.json:source", f"missing required key: {key}")

    database = db_schema.get("database")
    if not isinstance(database, dict):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "database must be object")
    else:
        for key in DATABASE_REQUIRED:
            if key not in database:
                _add(findings, "ERROR", "QR-DB-001", "db_schema.json:database", f"missing required key: {key}")
        port = database.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            _add(findings, "ERROR", "QR-DB-002", "db_schema.json:database.port", "port must be integer in range 1..65535")

    owners = db_schema.get("owners")
    if not isinstance(owners, list):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "owners must be array")

    if not isinstance(db_schema.get("notes"), list):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "notes must be array")

    if not isinstance(db_schema.get("needs_review"), bool):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "needs_review must be boolean")

    tables = db_schema.get("tables")
    if not isinstance(tables, list):
        _add(findings, "ERROR", "QR-DB-001", "db_schema.json", "tables must be array")
        return findings

    for idx, table in enumerate(tables):
        target = f"db_schema.json:tables[{idx}]"
        if not isinstance(table, dict):
            _add(findings, "ERROR", "QR-DB-001", target, "table must be object")
            continue
        for key in TABLE_REQUIRED:
            if key not in table:
                _add(findings, "ERROR", "QR-DB-001", target, f"missing required key: {key}")

        table_id = str(table.get("table_id", ""))
        owner = str(table.get("owner", ""))
        table_name = str(table.get("table_name", ""))
        if not TABLE_ID_PATTERN.match(table_id):
            _add(findings, "ERROR", "QR-DB-002", target, "invalid table_id format")
        if table_id != f"{owner}.{table_name}":
            _add(findings, "ERROR", "QR-DB-002", target, "table_id must equal OWNER.TABLE_NAME")
        if not isinstance(table.get("needs_review"), bool):
            _add(findings, "ERROR", "QR-DB-002", target, "needs_review must be boolean")
        if not isinstance(table.get("unknown"), bool):
            _add(findings, "ERROR", "QR-DB-002", target, "unknown must be boolean")

        _validate_evidence_array(table.get("evidence"), findings=findings, target=target)

        columns = table.get("columns")
        if not isinstance(columns, list):
            _add(findings, "ERROR", "QR-DB-002", target, "columns must be array")
            continue

        for col_idx, column in enumerate(columns):
            col_target = f"{target}:columns[{col_idx}]"
            if not isinstance(column, dict):
                _add(findings, "ERROR", "QR-DB-002", col_target, "column must be object")
                continue
            for key in COLUMN_REQUIRED:
                if key not in column:
                    _add(findings, "ERROR", "QR-DB-002", col_target, f"missing required key: {key}")
            ordinal = column.get("ordinal_position")
            if not isinstance(ordinal, int) or ordinal < 1:
                _add(findings, "ERROR", "QR-DB-002", col_target, "ordinal_position must be integer >= 1")
            if not isinstance(column.get("needs_review"), bool):
                _add(findings, "ERROR", "QR-DB-002", col_target, "needs_review must be boolean")
            if not isinstance(column.get("unknown"), bool):
                _add(findings, "ERROR", "QR-DB-002", col_target, "unknown must be boolean")
            _validate_evidence_array(column.get("evidence"), findings=findings, target=col_target)

        pk = table.get("primary_key")
        if pk is not None:
            if not isinstance(pk, dict):
                _add(findings, "ERROR", "QR-DB-002", f"{target}:primary_key", "primary_key must be object or null")
            else:
                for key in PK_REQUIRED:
                    if key not in pk:
                        _add(findings, "ERROR", "QR-DB-002", f"{target}:primary_key", f"missing required key: {key}")
                _validate_evidence_array(pk.get("evidence"), findings=findings, target=f"{target}:primary_key")

        foreign_keys = table.get("foreign_keys")
        if not isinstance(foreign_keys, list):
            _add(findings, "ERROR", "QR-DB-002", target, "foreign_keys must be array")
            continue
        for fk_idx, fk in enumerate(foreign_keys):
            fk_target = f"{target}:foreign_keys[{fk_idx}]"
            if not isinstance(fk, dict):
                _add(findings, "ERROR", "QR-DB-002", fk_target, "foreign key must be object")
                continue
            for key in FK_REQUIRED:
                if key not in fk:
                    _add(findings, "ERROR", "QR-DB-002", fk_target, f"missing required key: {key}")
            fk_id = str(fk.get("fk_id", ""))
            if not FK_ID_PATTERN.match(fk_id):
                _add(findings, "ERROR", "QR-DB-002", fk_target, "invalid fk_id format")
            if not isinstance(fk.get("needs_review"), bool):
                _add(findings, "ERROR", "QR-DB-002", fk_target, "needs_review must be boolean")
            if not isinstance(fk.get("unknown"), bool):
                _add(findings, "ERROR", "QR-DB-002", fk_target, "unknown must be boolean")
            _validate_evidence_array(fk.get("evidence"), findings=findings, target=fk_target)

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
        "## Source",
        "## Database",
        "## Owners",
        "## Table Index",
        "## Tables",
        "## Notes",
        "## Appendix: Source Evidence Summary",
    ]:
        if marker not in content:
            findings.append({"level": "ERROR", "code": "QR-DB-004", "target": "DB_SCHEMA.md", "detail": f"missing required section marker: {marker}"})

    if "### " not in content:
        findings.append({"level": "WARN", "code": "QR-DB-005", "target": "DB_SCHEMA.md", "detail": "table detail section is missing"})

    return findings


def load_and_validate_db_schema_json(run_dir: Path) -> list[Finding]:
    path = run_dir / "db_schema.json"
    if not path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(path), "detail": "optional file not found"}]
    payload, error = load_json_file(path)
    if error or payload is None:
        return [{"level": "ERROR", "code": "QR-COMMON-001", "target": str(path), "detail": error or "failed to load db_schema.json"}]
    return validate_db_schema_json(payload)
