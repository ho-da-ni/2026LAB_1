"""Database normalization and db_schema payload builder."""

from __future__ import annotations

from typing import Any

from lab.runtime.fingerprint import stable_sha256
from lab.shared_utils import utc_now_iso

FINGERPRINT_EXCLUDES = ["metadata.generated_at_utc", "integrity.fingerprint"]


def _normalize_column(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    references = item.get("references", {})
    refs = references if isinstance(references, dict) else {}
    return {
        "name": str(item.get("name", "UNKNOWN")),
        "data_type": str(item.get("data_type", "UNKNOWN")),
        "nullable": item.get("nullable", "UNKNOWN"),
        "default": item.get("default", "UNKNOWN"),
        "is_primary_key": bool(item.get("is_primary_key", False)),
        "is_foreign_key": bool(item.get("is_foreign_key", False)),
        "references": {
            "table": str(refs.get("table", "UNKNOWN")),
            "column": str(refs.get("column", "UNKNOWN")),
        },
    }


def _normalize_table(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    columns_raw = item.get("columns", [])
    columns = [_normalize_column(col) for col in columns_raw] if isinstance(columns_raw, list) else []
    columns = sorted(columns, key=lambda col: str(col.get("name", "UNKNOWN")))

    pk = item.get("primary_key", {})
    primary_key = pk if isinstance(pk, dict) else {}
    pk_columns = primary_key.get("columns", [])
    primary_key_columns = sorted(str(col) for col in pk_columns) if isinstance(pk_columns, list) else []

    fks = item.get("foreign_keys", [])
    foreign_keys = sorted(
        (fk for fk in fks if isinstance(fk, dict)),
        key=lambda fk: (str(fk.get("name", "UNKNOWN")), str(fk.get("column", "UNKNOWN"))),
    )
    idx = item.get("indexes", [])
    indexes = sorted((index for index in idx if isinstance(index, dict)), key=lambda index: str(index.get("name", "UNKNOWN")))
    source_evidence = item.get("source_evidence", [])
    evidence_rows = sorted(
        (ev for ev in source_evidence if isinstance(ev, dict)),
        key=lambda ev: (str(ev.get("file", "UNKNOWN")), str(ev.get("symbol", "UNKNOWN"))),
    )
    needs_review_raw = item.get("needs_review", [])
    needs_review = sorted(str(code) for code in needs_review_raw) if isinstance(needs_review_raw, list) else []

    table = {
        "table_name": str(item.get("table_name", item.get("name", "UNKNOWN"))),
        "schema_name": str(item.get("schema_name", item.get("schema", "UNKNOWN"))),
        "columns": columns,
        "primary_key": {"columns": primary_key_columns},
        "foreign_keys": foreign_keys,
        "indexes": indexes,
        "source_evidence": evidence_rows,
        "needs_review": needs_review,
    }
    if table["table_name"] == "UNKNOWN" and "needs_review.table_name_unknown" not in table["needs_review"]:
        table["needs_review"].append("needs_review.table_name_unknown")
    if not table["columns"] and "needs_review.columns_missing" not in table["needs_review"]:
        table["needs_review"].append("needs_review.columns_missing")
    table["needs_review"] = sorted(table["needs_review"])
    return table


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    meta = raw.get("metadata", {})
    metadata = meta if isinstance(meta, dict) else {}
    tables_raw = raw.get("tables", [])
    tables = [_normalize_table(table) for table in tables_raw] if isinstance(tables_raw, list) else []
    tables = sorted(tables, key=lambda table: (str(table.get("schema_name", "UNKNOWN")), str(table.get("table_name", "UNKNOWN"))))

    needs_review_raw = raw.get("needs_review", [])
    needs_review = sorted(str(code) for code in needs_review_raw) if isinstance(needs_review_raw, list) else []
    if not tables and "needs_review.db_schema.empty" not in needs_review:
        needs_review.append("needs_review.db_schema.empty")

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "metadata": {
            "generated_at_utc": utc_now_iso(),
            "source_type": str(metadata.get("source_type", raw.get("source_type", "UNKNOWN"))),
            "source_path": str(metadata.get("source_path", raw.get("source_path", "UNKNOWN"))),
            "snapshot_id": str(metadata.get("snapshot_id", raw.get("snapshot_id", "UNKNOWN"))),
            "collected_at_utc": str(metadata.get("collected_at_utc", raw.get("collected_at_utc", "UNKNOWN"))),
        },
        "tables": tables,
        "needs_review": sorted(needs_review),
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy_version": "1.0.0",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": FINGERPRINT_EXCLUDES,
            },
        },
    }
    payload["integrity"]["fingerprint"] = stable_sha256(payload, exclude_paths=FINGERPRINT_EXCLUDES)
    return payload
