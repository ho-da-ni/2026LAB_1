"""Database normalization and db_schema payload builder."""

from __future__ import annotations

from typing import Any


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return default


def _normalize_evidence(raw_list: Any, *, fallback_view: str, owner: str, object_name: str) -> list[dict[str, Any]]:
    evidence_rows: list[dict[str, Any]] = []
    if isinstance(raw_list, list):
        for row in raw_list:
            if not isinstance(row, dict):
                continue
            evidence_rows.append(
                {
                    "source_view": str(row.get("source_view", fallback_view)),
                    "owner": str(row.get("owner", owner)),
                    "object_name": str(row.get("object_name", object_name)),
                    "column_name": row.get("column_name"),
                    "constraint_name": row.get("constraint_name"),
                    "row_ref": row.get("row_ref", {}),
                }
            )
    if evidence_rows:
        return sorted(evidence_rows, key=lambda e: (e["source_view"], e["owner"], e["object_name"], str(e.get("column_name") or "")))
    return [
        {
            "source_view": fallback_view,
            "owner": owner,
            "object_name": object_name,
            "column_name": None,
            "constraint_name": None,
            "row_ref": {"status": "MISSING_SOURCE_EVIDENCE"},
        }
    ]


def _normalize_column(raw: Any, *, owner: str, table_name: str, ordinal_default: int) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    name = str(item.get("name", "UNKNOWN")).upper()
    data_type = str(item.get("data_type", "UNKNOWN")).upper()
    ordinal_position = item.get("ordinal_position", ordinal_default)
    if not isinstance(ordinal_position, int) or ordinal_position < 1:
        ordinal_position = ordinal_default

    evidence = _normalize_evidence(
        item.get("evidence"),
        fallback_view="ALL_TAB_COLUMNS",
        owner=owner,
        object_name=table_name,
    )

    unknown = name == "UNKNOWN" or data_type == "UNKNOWN"
    needs_review = _to_bool(item.get("needs_review"), default=unknown)

    return {
        "name": name,
        "ordinal_position": ordinal_position,
        "data_type": data_type,
        "data_length": item.get("data_length"),
        "data_precision": item.get("data_precision"),
        "data_scale": item.get("data_scale"),
        "nullable": _to_bool(item.get("nullable"), default=True),
        "default": item.get("default"),
        "comment": item.get("comment"),
        "needs_review": needs_review,
        "unknown": unknown,
        "evidence": evidence,
    }


def _normalize_pk(raw: Any, *, owner: str, table_name: str, columns: list[dict[str, Any]]) -> dict[str, Any] | None:
    if raw is None:
        return None
    item = raw if isinstance(raw, dict) else {}
    constraint_name = str(item.get("constraint_name", item.get("name", "UNKNOWN"))).upper()
    cols = item.get("columns")
    if isinstance(cols, list) and cols:
        pk_columns = [str(c).upper() for c in cols]
    else:
        pk_columns = [c["name"] for c in columns if c.get("name") != "UNKNOWN" and _to_bool(c.get("is_primary_key"))]

    evidence = _normalize_evidence(
        item.get("evidence"),
        fallback_view="ALL_CONSTRAINTS",
        owner=owner,
        object_name=table_name,
    )
    unknown = constraint_name == "UNKNOWN" or len(pk_columns) == 0
    needs_review = _to_bool(item.get("needs_review"), default=unknown)

    return {
        "constraint_name": constraint_name,
        "columns": pk_columns,
        "evidence": evidence,
        "needs_review": needs_review,
        "unknown": unknown,
    }


def _normalize_fk(raw: Any, *, owner: str, table_name: str) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    constraint_name = str(item.get("constraint_name", item.get("name", "UNKNOWN"))).upper()

    columns_raw = item.get("columns")
    if isinstance(columns_raw, list) and columns_raw:
        columns = [str(c).upper() for c in columns_raw]
    else:
        one_col = str(item.get("column", "UNKNOWN")).upper()
        columns = [] if one_col == "UNKNOWN" else [one_col]

    ref_owner = str(item.get("referenced_owner", owner)).upper()
    ref_table = str(item.get("referenced_table", item.get("references_table", "UNKNOWN"))).upper()

    mapping_raw = item.get("column_mapping")
    if isinstance(mapping_raw, list) and mapping_raw:
        column_mapping = [
            {
                "local_column": str(m.get("local_column", "UNKNOWN")).upper(),
                "referenced_column": str(m.get("referenced_column", "UNKNOWN")).upper(),
            }
            for m in mapping_raw
            if isinstance(m, dict)
        ]
    else:
        local_column = columns[0] if columns else "UNKNOWN"
        referenced_column = str(item.get("referenced_column", item.get("references_column", "UNKNOWN"))).upper()
        column_mapping = [{"local_column": local_column, "referenced_column": referenced_column}]

    evidence = _normalize_evidence(
        item.get("evidence"),
        fallback_view="ALL_CONSTRAINTS",
        owner=owner,
        object_name=table_name,
    )

    fk_id = f"{owner}.{table_name}.{constraint_name}"
    unknown = constraint_name == "UNKNOWN" or ref_table == "UNKNOWN"
    needs_review = _to_bool(item.get("needs_review"), default=unknown)

    return {
        "fk_id": fk_id,
        "constraint_name": constraint_name,
        "columns": columns,
        "referenced_owner": ref_owner,
        "referenced_table": ref_table,
        "column_mapping": column_mapping,
        "evidence": evidence,
        "needs_review": needs_review,
        "unknown": unknown,
    }


def _normalize_table(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    owner = str(item.get("owner", item.get("schema_name", item.get("schema", "UNKNOWN"))).upper())
    table_name = str(item.get("table_name", item.get("name", "UNKNOWN"))).upper()
    table_id = f"{owner}.{table_name}"

    columns_raw = item.get("columns")
    columns = []
    if isinstance(columns_raw, list):
        for idx, col in enumerate(columns_raw, start=1):
            columns.append(_normalize_column(col, owner=owner, table_name=table_name, ordinal_default=idx))
    columns = sorted(columns, key=lambda c: (int(c.get("ordinal_position", 999999)), c.get("name", "UNKNOWN")))

    primary_key = _normalize_pk(item.get("primary_key"), owner=owner, table_name=table_name, columns=columns)

    foreign_keys_raw = item.get("foreign_keys")
    foreign_keys = [_normalize_fk(fk, owner=owner, table_name=table_name) for fk in foreign_keys_raw] if isinstance(foreign_keys_raw, list) else []
    foreign_keys = sorted(foreign_keys, key=lambda fk: fk.get("fk_id", "UNKNOWN"))

    evidence = _normalize_evidence(
        item.get("evidence", item.get("source_evidence")),
        fallback_view="ALL_TABLES",
        owner=owner,
        object_name=table_name,
    )

    has_unknown_column = any(_to_bool(col.get("unknown")) for col in columns)
    has_unknown_fk = any(_to_bool(fk.get("unknown")) for fk in foreign_keys)
    pk_unknown = _to_bool(primary_key.get("unknown")) if isinstance(primary_key, dict) else False

    unknown = owner == "UNKNOWN" or table_name == "UNKNOWN" or len(columns) == 0 or has_unknown_column or has_unknown_fk or pk_unknown
    needs_review = _to_bool(item.get("needs_review"), default=unknown)

    return {
        "table_id": table_id,
        "owner": owner,
        "table_name": table_name,
        "table_comment": item.get("table_comment"),
        "columns": columns,
        "primary_key": primary_key,
        "foreign_keys": foreign_keys,
        "evidence": evidence,
        "needs_review": needs_review,
        "unknown": unknown,
    }


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    connection = metadata.get("connection") if isinstance(metadata.get("connection"), dict) else {}

    host = str(connection.get("host", raw.get("host", "UNKNOWN")))
    port = connection.get("port", raw.get("port", 1521))
    if not isinstance(port, int):
        port = 1521
    service_name = connection.get("target") if connection.get("target_mode") == "service_name" else raw.get("service_name")
    sid = connection.get("target") if connection.get("target_mode") == "sid" else raw.get("sid")

    owners_raw = connection.get("owner_filters", raw.get("owners", []))
    owners = sorted({str(owner).upper() for owner in owners_raw if str(owner).strip()}) if isinstance(owners_raw, list) else []

    tables_raw = raw.get("tables") if isinstance(raw.get("tables"), list) else []
    tables = [_normalize_table(table) for table in tables_raw]
    tables = sorted(tables, key=lambda t: t.get("table_id", "UNKNOWN"))

    notes_raw = raw.get("notes")
    notes = [str(note) for note in notes_raw] if isinstance(notes_raw, list) else []
    if not tables:
        notes.append("No tables were collected; check owner filters and collection privileges.")

    needs_review = bool(any(table.get("needs_review") for table in tables) or len(tables) == 0)

    return {
        "schema_version": "w6.db_schema.v1",
        "source": {
            "collector": "lab collect db",
            "collected_at": str(metadata.get("collected_at_utc", raw.get("collected_at_utc", "UNKNOWN"))),
            "dictionary_views": [
                "ALL_TABLES",
                "ALL_TAB_COLUMNS",
                "ALL_CONSTRAINTS",
                "ALL_CONS_COLUMNS",
                "ALL_TAB_COMMENTS",
                "ALL_COL_COMMENTS",
            ],
        },
        "database": {
            "vendor": "oracle",
            "host": host,
            "port": port,
            "service_name": str(service_name).upper() if service_name else None,
            "sid": str(sid).upper() if sid else None,
        },
        "owners": owners,
        "tables": tables,
        "notes": sorted(set(notes)),
        "needs_review": needs_review,
    }
