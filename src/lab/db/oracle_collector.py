"""Live Oracle metadata collection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import importlib
import importlib.util
from typing import Any, Iterable

from lab.shared_utils import utc_now_iso


ORACLE_DICTIONARY_VIEWS = [
    "ALL_COL_COMMENTS",
    "ALL_CONS_COLUMNS",
    "ALL_CONSTRAINTS",
    "ALL_TAB_COLUMNS",
    "ALL_TAB_COMMENTS",
    "ALL_TABLES",
]

DEFAULT_SYSTEM_OWNERS = [
    "ANONYMOUS",
    "APPQOSSYS",
    "AUDSYS",
    "CTXSYS",
    "DBSFWUSER",
    "DBSNMP",
    "DIP",
    "DVF",
    "DVSYS",
    "GGSYS",
    "GSMADMIN_INTERNAL",
    "LBACSYS",
    "MDSYS",
    "OJVMSYS",
    "OLAPSYS",
    "ORDDATA",
    "ORDPLUGINS",
    "ORDSYS",
    "OUTLN",
    "REMOTE_SCHEDULER_AGENT",
    "SI_INFORMTN_SCHEMA",
    "SYS",
    "SYSBACKUP",
    "SYSDG",
    "SYSKM",
    "SYSRAC",
    "SYSTEM",
    "WMSYS",
    "XDB",
    "XS$NULL",
]


TABLE_LIST_SQL = """
SELECT
  t.OWNER AS owner,
  t.TABLE_NAME AS table_name,
  t.STATUS AS table_status,
  t.TEMPORARY AS temporary,
  t.NESTED AS nested,
  t.IOT_TYPE AS iot_type
FROM ALL_TABLES t
WHERE {owner_filter}
ORDER BY t.OWNER, t.TABLE_NAME
"""

COLUMN_LIST_SQL = """
SELECT
  c.OWNER AS owner,
  c.TABLE_NAME AS table_name,
  c.COLUMN_NAME AS column_name,
  c.COLUMN_ID AS ordinal_position,
  c.DATA_TYPE AS data_type,
  c.DATA_LENGTH AS data_length,
  c.DATA_PRECISION AS data_precision,
  c.DATA_SCALE AS data_scale,
  c.NULLABLE AS nullable_flag,
  c.DATA_DEFAULT AS data_default
FROM ALL_TAB_COLUMNS c
WHERE {owner_filter}
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID, c.COLUMN_NAME
"""

PRIMARY_KEY_SQL = """
SELECT
  p.OWNER AS owner,
  p.TABLE_NAME AS table_name,
  p.CONSTRAINT_NAME AS constraint_name,
  pc.COLUMN_NAME AS column_name,
  pc.POSITION AS column_position,
  p.STATUS AS constraint_status,
  p.DEFERRABLE AS deferrable,
  p.DEFERRED AS deferred
FROM ALL_CONSTRAINTS p
JOIN ALL_CONS_COLUMNS pc
  ON pc.OWNER = p.OWNER
 AND pc.TABLE_NAME = p.TABLE_NAME
 AND pc.CONSTRAINT_NAME = p.CONSTRAINT_NAME
WHERE p.CONSTRAINT_TYPE = 'P'
  AND {owner_filter}
ORDER BY p.OWNER, p.TABLE_NAME, p.CONSTRAINT_NAME, pc.POSITION, pc.COLUMN_NAME
"""

FOREIGN_KEY_SQL = """
SELECT
  fk.OWNER AS owner,
  fk.TABLE_NAME AS table_name,
  fk.CONSTRAINT_NAME AS constraint_name,
  fkc.COLUMN_NAME AS local_column,
  fkc.POSITION AS column_position,
  pk.OWNER AS referenced_owner,
  pk.TABLE_NAME AS referenced_table,
  pk.CONSTRAINT_NAME AS referenced_constraint_name,
  pkc.COLUMN_NAME AS referenced_column,
  fk.STATUS AS constraint_status,
  fk.DELETE_RULE AS delete_rule,
  fk.DEFERRABLE AS deferrable,
  fk.DEFERRED AS deferred
FROM ALL_CONSTRAINTS fk
JOIN ALL_CONS_COLUMNS fkc
  ON fkc.OWNER = fk.OWNER
 AND fkc.TABLE_NAME = fk.TABLE_NAME
 AND fkc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
JOIN ALL_CONSTRAINTS pk
  ON pk.OWNER = fk.R_OWNER
 AND pk.CONSTRAINT_NAME = fk.R_CONSTRAINT_NAME
JOIN ALL_CONS_COLUMNS pkc
  ON pkc.OWNER = pk.OWNER
 AND pkc.TABLE_NAME = pk.TABLE_NAME
 AND pkc.CONSTRAINT_NAME = pk.CONSTRAINT_NAME
 AND pkc.POSITION = fkc.POSITION
WHERE fk.CONSTRAINT_TYPE = 'R'
  AND {owner_filter}
ORDER BY fk.OWNER, fk.TABLE_NAME, fk.CONSTRAINT_NAME, fkc.POSITION, fkc.COLUMN_NAME
"""

TABLE_COMMENT_SQL = """
SELECT
  tc.OWNER AS owner,
  tc.TABLE_NAME AS table_name,
  tc.TABLE_TYPE AS table_type,
  tc.COMMENTS AS table_comment
FROM ALL_TAB_COMMENTS tc
WHERE {owner_filter}
  AND tc.TABLE_TYPE = 'TABLE'
ORDER BY tc.OWNER, tc.TABLE_NAME
"""

COLUMN_COMMENT_SQL = """
SELECT
  cc.OWNER AS owner,
  cc.TABLE_NAME AS table_name,
  cc.COLUMN_NAME AS column_name,
  cc.COMMENTS AS column_comment
FROM ALL_COL_COMMENTS cc
WHERE {owner_filter}
ORDER BY cc.OWNER, cc.TABLE_NAME, cc.COLUMN_NAME
"""


class OracleDependencyError(RuntimeError):
    """Raised when the optional Oracle DB driver is unavailable."""


class OracleCollectionError(RuntimeError):
    """Raised when live Oracle metadata collection fails."""


@dataclass(frozen=True)
class OracleConnectionConfig:
    host: str
    port: int
    service_name: str | None
    sid: str | None
    username: str
    password: str
    password_mode: str
    password_env_name: str | None
    owners: list[str]
    output_dir: str
    timeout: int
    include_comments: bool
    system_owners: list[str]

    @property
    def target(self) -> str:
        return self.service_name if self.service_name is not None else str(self.sid)

    @property
    def target_mode(self) -> str:
        return "service_name" if self.service_name is not None else "sid"


def load_oracle_driver() -> Any:
    """Load the optional python-oracledb driver."""

    if importlib.util.find_spec("oracledb") is None:
        raise OracleDependencyError("Oracle driver unavailable. Install the optional dependency with `pip install -e .[oracle]` or install `oracledb`.")
    return importlib.import_module("oracledb")


def normalize_owner_list(values: Iterable[str]) -> list[str]:
    return sorted({str(value).strip().upper() for value in values if str(value).strip()})


def _owner_filter(alias: str, owners: list[str], system_owners: list[str]) -> tuple[str, dict[str, str]]:
    binds: dict[str, str] = {}
    owner_placeholders: list[str] = []
    for idx, owner in enumerate(owners):
        key = f"owner_{idx}"
        owner_placeholders.append(f":{key}")
        binds[key] = owner

    system_placeholders: list[str] = []
    for idx, owner in enumerate(system_owners):
        key = f"system_owner_{idx}"
        system_placeholders.append(f":{key}")
        binds[key] = owner

    include_clause = f"{alias}.OWNER IN ({', '.join(owner_placeholders)})"
    exclude_clause = f"{alias}.OWNER NOT IN ({', '.join(system_placeholders)})" if system_placeholders else "1 = 1"
    return f"{include_clause}\n  AND {exclude_clause}", binds


def _sql(template: str, alias: str, owners: list[str], system_owners: list[str]) -> tuple[str, dict[str, str]]:
    owner_filter, binds = _owner_filter(alias, owners, system_owners)
    return template.format(owner_filter=owner_filter), binds


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    read = getattr(value, "read", None)
    if callable(read):
        return read()
    return str(value)


def _fetch_rows(connection: Any, sql: str, binds: dict[str, str]) -> list[dict[str, Any]]:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, binds)
        names = [str(column[0]).lower() for column in cursor.description]
        return [{name: _json_safe(value) for name, value in zip(names, row)} for row in cursor.fetchall()]
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()


def _evidence(source_view: str, row: dict[str, Any], *, column_key: str | None = None) -> dict[str, Any]:
    column_name = row.get(column_key) if column_key is not None else row.get("column_name")
    return {
        "source_view": source_view,
        "owner": row.get("owner", "UNKNOWN"),
        "object_name": row.get("table_name", "UNKNOWN"),
        "column_name": column_name,
        "constraint_name": row.get("constraint_name"),
        "row_ref": dict(row),
    }


def _table_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("owner", "UNKNOWN")).upper(), str(row.get("table_name", "UNKNOWN")).upper()


def _assemble_tables(raw: dict[str, list[dict[str, Any]]], *, include_comments: bool) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    tables: dict[tuple[str, str], dict[str, Any]] = {}

    for row in raw["tables"]:
        owner, table_name = _table_key(row)
        tables[(owner, table_name)] = {
            "owner": owner,
            "table_name": table_name,
            "table_comment": None,
            "columns": [],
            "primary_key": None,
            "foreign_keys": [],
            "evidence": [_evidence("ALL_TABLES", row)],
            "needs_review": False,
            "unknown": False,
        }

    for row in raw["columns"]:
        owner, table_name = _table_key(row)
        table = tables.get((owner, table_name))
        if table is None:
            notes.append(f"Skipped column metadata for non-table object {owner}.{table_name}.")
            continue
        nullable_flag = str(row.get("nullable_flag", "Y")).upper()
        unknown = row.get("ordinal_position") is None or row.get("data_type") in {None, ""} or nullable_flag not in {"Y", "N"}
        table["columns"].append(
            {
                "name": str(row.get("column_name", "UNKNOWN")).upper(),
                "ordinal_position": row.get("ordinal_position"),
                "data_type": str(row.get("data_type", "UNKNOWN")).upper(),
                "data_length": row.get("data_length"),
                "data_precision": row.get("data_precision"),
                "data_scale": row.get("data_scale"),
                "nullable": nullable_flag == "Y",
                "default": row.get("data_default"),
                "comment": None,
                "evidence": [_evidence("ALL_TAB_COLUMNS", row)],
                "needs_review": unknown,
                "unknown": unknown,
            }
        )

    pk_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in raw["primary_keys"]:
        owner, table_name = _table_key(row)
        constraint_name = str(row.get("constraint_name", "UNKNOWN")).upper()
        pk_groups.setdefault((owner, table_name, constraint_name), []).append(row)

    for (owner, table_name, constraint_name), rows in sorted(pk_groups.items()):
        table = tables.get((owner, table_name))
        if table is None:
            notes.append(f"Skipped PK metadata for non-table object {owner}.{table_name}.{constraint_name}.")
            continue
        ordered = sorted(rows, key=lambda item: (item.get("column_position") or 0, str(item.get("column_name", ""))))
        columns = [str(row.get("column_name", "UNKNOWN")).upper() for row in ordered]
        evidence = []
        for row in ordered:
            evidence.append(_evidence("ALL_CONSTRAINTS", row))
            evidence.append(_evidence("ALL_CONS_COLUMNS", row))
        table["primary_key"] = {
            "constraint_name": constraint_name,
            "columns": columns,
            "evidence": evidence,
            "needs_review": not columns,
            "unknown": not columns,
        }

    fk_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in raw["foreign_keys"]:
        owner, table_name = _table_key(row)
        constraint_name = str(row.get("constraint_name", "UNKNOWN")).upper()
        fk_groups.setdefault((owner, table_name, constraint_name), []).append(row)

    for (owner, table_name, constraint_name), rows in sorted(fk_groups.items()):
        table = tables.get((owner, table_name))
        if table is None:
            notes.append(f"Skipped FK metadata for non-table object {owner}.{table_name}.{constraint_name}.")
            continue
        ordered = sorted(rows, key=lambda item: (item.get("column_position") or 0, str(item.get("local_column", ""))))
        local_columns = [str(row.get("local_column", "UNKNOWN")).upper() for row in ordered]
        column_mapping = [
            {
                "local_column": str(row.get("local_column", "UNKNOWN")).upper(),
                "referenced_column": str(row.get("referenced_column", "UNKNOWN")).upper(),
            }
            for row in ordered
        ]
        evidence = []
        for row in ordered:
            evidence.append(_evidence("ALL_CONSTRAINTS", row, column_key="local_column"))
            evidence.append(_evidence("ALL_CONS_COLUMNS", row, column_key="local_column"))
        referenced_owner = str(ordered[0].get("referenced_owner", "UNKNOWN")).upper() if ordered else "UNKNOWN"
        referenced_table = str(ordered[0].get("referenced_table", "UNKNOWN")).upper() if ordered else "UNKNOWN"
        unknown = not local_columns or referenced_owner == "UNKNOWN" or referenced_table == "UNKNOWN"
        table["foreign_keys"].append(
            {
                "fk_id": f"{owner}.{table_name}.{constraint_name}",
                "constraint_name": constraint_name,
                "columns": local_columns,
                "referenced_owner": referenced_owner,
                "referenced_table": referenced_table,
                "column_mapping": column_mapping,
                "evidence": evidence,
                "needs_review": unknown,
                "unknown": unknown,
            }
        )

    if include_comments:
        for row in raw["table_comments"]:
            owner, table_name = _table_key(row)
            table = tables.get((owner, table_name))
            if table is None:
                notes.append(f"Skipped table comment for non-table object {owner}.{table_name}.")
                continue
            table["table_comment"] = row.get("table_comment")
            table["evidence"].append(_evidence("ALL_TAB_COMMENTS", row))

        columns_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
        for table in tables.values():
            for column in table["columns"]:
                columns_by_key[(table["owner"], table["table_name"], column["name"])] = column
        for row in raw["column_comments"]:
            owner, table_name = _table_key(row)
            column_name = str(row.get("column_name", "UNKNOWN")).upper()
            column = columns_by_key.get((owner, table_name, column_name))
            if column is None:
                notes.append(f"Skipped column comment for non-table column {owner}.{table_name}.{column_name}.")
                continue
            column["comment"] = row.get("column_comment")
            column["evidence"].append(_evidence("ALL_COL_COMMENTS", row))

    for table in tables.values():
        table["columns"] = sorted(table["columns"], key=lambda col: (col.get("ordinal_position") or 999999, col.get("name", "UNKNOWN")))
        table["foreign_keys"] = sorted(table["foreign_keys"], key=lambda fk: fk["fk_id"])
        if len(table["columns"]) == 0:
            table["needs_review"] = True
            table["unknown"] = True
            notes.append(f"No columns collected for table {table['owner']}.{table['table_name']}.")

    return sorted(tables.values(), key=lambda table: (table["owner"], table["table_name"])), sorted(set(notes))


def collect_oracle_metadata(config: OracleConnectionConfig, *, driver: Any | None = None) -> dict[str, Any]:
    oracle_driver = driver if driver is not None else load_oracle_driver()
    dsn = oracle_driver.makedsn(config.host, config.port, service_name=config.service_name) if config.service_name else oracle_driver.makedsn(config.host, config.port, sid=config.sid)

    try:
        connection = oracle_driver.connect(
            user=config.username,
            password=config.password,
            dsn=dsn,
            tcp_connect_timeout=config.timeout,
        )
    except Exception as exc:
        raise OracleCollectionError("Oracle connection failed before metadata collection started.") from exc

    try:
        if hasattr(connection, "call_timeout"):
            connection.call_timeout = config.timeout * 1000
        table_sql, table_binds = _sql(TABLE_LIST_SQL, "t", config.owners, config.system_owners)
        column_sql, column_binds = _sql(COLUMN_LIST_SQL, "c", config.owners, config.system_owners)
        pk_sql, pk_binds = _sql(PRIMARY_KEY_SQL, "p", config.owners, config.system_owners)
        fk_sql, fk_binds = _sql(FOREIGN_KEY_SQL, "fk", config.owners, config.system_owners)

        raw = {
            "tables": _fetch_rows(connection, table_sql, table_binds),
            "columns": _fetch_rows(connection, column_sql, column_binds),
            "primary_keys": _fetch_rows(connection, pk_sql, pk_binds),
            "foreign_keys": _fetch_rows(connection, fk_sql, fk_binds),
            "table_comments": [],
            "column_comments": [],
        }
        if config.include_comments:
            table_comment_sql, table_comment_binds = _sql(TABLE_COMMENT_SQL, "tc", config.owners, config.system_owners)
            column_comment_sql, column_comment_binds = _sql(COLUMN_COMMENT_SQL, "cc", config.owners, config.system_owners)
            raw["table_comments"] = _fetch_rows(connection, table_comment_sql, table_comment_binds)
            raw["column_comments"] = _fetch_rows(connection, column_comment_sql, column_comment_binds)
    except Exception as exc:
        raise OracleCollectionError("Oracle metadata query failed.") from exc
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()

    tables, notes = _assemble_tables(raw, include_comments=config.include_comments)
    return {
        "metadata": {
            "source_type": "oracle_live_collection",
            "source_path": f"oracle://{config.host}:{config.port}/{config.target}",
            "snapshot_id": "live",
            "collected_at_utc": utc_now_iso(),
            "collection_mode": "live_query",
            "dictionary_views": ORACLE_DICTIONARY_VIEWS,
            "connection": {
                "host": config.host,
                "port": config.port,
                "target_mode": config.target_mode,
                "target": config.target,
                "username": config.username,
                "owner_filters": config.owners,
                "system_owner_filters": config.system_owners,
                "timeout_seconds": config.timeout,
                "include_comments": config.include_comments,
                "password_mode": config.password_mode,
                "password_env_name": config.password_env_name,
            },
        },
        "raw_metadata": raw,
        "tables": tables,
        "notes": notes,
        "needs_review": [],
    }
