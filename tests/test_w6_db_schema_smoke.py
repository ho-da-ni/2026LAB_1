from __future__ import annotations

import json
from pathlib import Path

from lab.cli import build_parser, main
from lab.runtime.fingerprint import stable_sha256


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_validate_required_files(run_dir: Path) -> None:
    run_context = {
        "schema_version": "1.0.0",
        "execution": {"exit_code": 0},
        "integrity": {
            "output_fingerprint": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": ["integrity.output_fingerprint"],
            },
        },
    }
    run_context["integrity"]["output_fingerprint"] = stable_sha256(run_context, exclude_paths=["integrity.output_fingerprint"])
    _write_json(run_dir / "run_context.json", run_context)

    changed_files = {
        "schema_version": "1.0.0",
        "summary": {"total_files": 0},
        "files": [],
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": ["integrity.fingerprint"],
            },
        },
    }
    changed_files["integrity"]["fingerprint"] = stable_sha256(changed_files, exclude_paths=["integrity.fingerprint"])
    _write_json(run_dir / "changed_files.json", changed_files)


def test_w6_db_schema_smoke_from_fixture(tmp_path: Path) -> None:
    fixture_path = Path("tests/fixtures/db/sample_db_input.json")
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_out = run_dir / "db_schema.json"
    md_out = run_dir / "DB_SCHEMA.md"

    assert main(["generate", "db-schema", "--input", str(fixture_path), "--json-output", str(json_out), "--output", str(md_out)]) == 0

    db_schema = json.loads(json_out.read_text(encoding="utf-8"))
    assert db_schema["schema_version"] == "w6.db_schema.v1"
    assert db_schema["source"]["collector"] == "lab collect db"
    assert db_schema["database"]["vendor"] == "oracle"
    assert isinstance(db_schema["owners"], list)
    assert db_schema["tables"][0]["table_id"] == "PUBLIC.USERS"
    assert db_schema["tables"][0]["foreign_keys"][0]["fk_id"] == "PUBLIC.USERS.FK_USERS_ORG"
    assert isinstance(db_schema["tables"][0]["evidence"], list) and len(db_schema["tables"][0]["evidence"]) >= 1

    markdown = md_out.read_text(encoding="utf-8")
    assert "# DB Schema Overview" in markdown
    assert "## Source" in markdown
    assert "## Database" in markdown
    assert "## Owners" in markdown
    assert "### PUBLIC.USERS" in markdown


def test_w6_db_schema_validate_strict_passes_for_schema_compliant_output(tmp_path: Path) -> None:
    fixture_path = Path("tests/fixtures/db/sample_db_input.json")
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_validate_required_files(run_dir)

    assert (
        main(
            [
                "generate",
                "db-schema",
                "--input",
                str(fixture_path),
                "--json-output",
                str(run_dir / "db_schema.json"),
                "--output",
                str(run_dir / "DB_SCHEMA.md"),
            ]
        )
        == 0
    )
    assert main(["validate", "--run-dir", str(run_dir), "--strict"]) == 0


def test_w6_db_schema_validate_detects_schema_contract_violation(tmp_path: Path) -> None:
    fixture_path = Path("tests/fixtures/db/sample_db_input.json")
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_validate_required_files(run_dir)

    assert (
        main(
            [
                "generate",
                "db-schema",
                "--input",
                str(fixture_path),
                "--json-output",
                str(run_dir / "db_schema.json"),
                "--output",
                str(run_dir / "DB_SCHEMA.md"),
            ]
        )
        == 0
    )

    db_schema = json.loads((run_dir / "db_schema.json").read_text(encoding="utf-8"))
    db_schema["tables"][0]["table_id"] = "invalid-format"
    _write_json(run_dir / "db_schema.json", db_schema)

    assert main(["validate", "--run-dir", str(run_dir), "--strict"]) == 4
    report = json.loads((run_dir / "quality_gate_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["error_count"] >= 1
    assert any(item["code"] == "QR-DB-002" for item in report["errors"])


def test_w6_db_schema_cli_contract_maps_flags_to_command_namespace(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    json_output_path = tmp_path / "db_schema.json"
    markdown_output_path = tmp_path / "DB_SCHEMA.md"

    parser = build_parser()
    args = parser.parse_args(
        [
            "generate",
            "db-schema",
            "--input",
            str(input_path),
            "--json-output",
            str(json_output_path),
            "--output",
            str(markdown_output_path),
        ]
    )

    assert args.db_schema_input == str(input_path)
    assert args.db_schema_json_output == str(json_output_path)
    assert args.db_schema_output == str(markdown_output_path)



class _FakeOracleCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self._rows = []

    def execute(self, sql, binds):
        self.connection.executed.append((sql, dict(binds)))
        owner_values = {value for key, value in binds.items() if key.startswith("owner_")}
        assert owner_values == {"APP"}
        assert "dummy-password" not in sql
        if "FROM ALL_TABLES" in sql:
            self.description = [("OWNER",), ("TABLE_NAME",), ("TABLE_STATUS",), ("TEMPORARY",), ("NESTED",), ("IOT_TYPE",)]
            self._rows = [("APP", "ORDERS", "VALID", "N", "NO", None)]
        elif "FROM ALL_TAB_COLUMNS" in sql:
            self.description = [
                ("OWNER",),
                ("TABLE_NAME",),
                ("COLUMN_NAME",),
                ("ORDINAL_POSITION",),
                ("DATA_TYPE",),
                ("DATA_LENGTH",),
                ("DATA_PRECISION",),
                ("DATA_SCALE",),
                ("NULLABLE_FLAG",),
                ("DATA_DEFAULT",),
            ]
            self._rows = [
                ("APP", "ORDERS", "ORDER_ID", 1, "NUMBER", 22, 10, 0, "N", None),
                ("APP", "ORDERS", "CUSTOMER_ID", 2, "NUMBER", 22, 10, 0, "N", None),
            ]
        elif "fk.CONSTRAINT_TYPE = 'R'" in sql:
            self.description = [
                ("OWNER",),
                ("TABLE_NAME",),
                ("CONSTRAINT_NAME",),
                ("LOCAL_COLUMN",),
                ("COLUMN_POSITION",),
                ("REFERENCED_OWNER",),
                ("REFERENCED_TABLE",),
                ("REFERENCED_CONSTRAINT_NAME",),
                ("REFERENCED_COLUMN",),
                ("CONSTRAINT_STATUS",),
                ("DELETE_RULE",),
                ("DEFERRABLE",),
                ("DEFERRED",),
            ]
            self._rows = [("APP", "ORDERS", "FK_ORDERS_CUSTOMER", "CUSTOMER_ID", 1, "APP", "CUSTOMERS", "PK_CUSTOMERS", "CUSTOMER_ID", "ENABLED", "NO ACTION", "NOT DEFERRABLE", "IMMEDIATE")]
        elif "p.CONSTRAINT_TYPE = 'P'" in sql:
            self.description = [
                ("OWNER",),
                ("TABLE_NAME",),
                ("CONSTRAINT_NAME",),
                ("COLUMN_NAME",),
                ("COLUMN_POSITION",),
                ("CONSTRAINT_STATUS",),
                ("DEFERRABLE",),
                ("DEFERRED",),
            ]
            self._rows = [("APP", "ORDERS", "PK_ORDERS", "ORDER_ID", 1, "ENABLED", "NOT DEFERRABLE", "IMMEDIATE")]
        elif "FROM ALL_TAB_COMMENTS" in sql:
            self.description = [("OWNER",), ("TABLE_NAME",), ("TABLE_TYPE",), ("TABLE_COMMENT",)]
            self._rows = [("APP", "ORDERS", "TABLE", "Orders header")]
        elif "FROM ALL_COL_COMMENTS" in sql:
            self.description = [("OWNER",), ("TABLE_NAME",), ("COLUMN_NAME",), ("COLUMN_COMMENT",)]
            self._rows = [("APP", "ORDERS", "ORDER_ID", "Order identifier")]
        else:
            raise AssertionError(f"unexpected SQL: {sql}")

    def fetchall(self):
        return self._rows

    def close(self):
        return None


class _FakeOracleConnection:
    def __init__(self):
        self.executed = []
        self.call_timeout = None
        self.closed = False

    def cursor(self):
        return _FakeOracleCursor(self)

    def close(self):
        self.closed = True


class _FakeOracleDriver:
    def __init__(self):
        self.connection = _FakeOracleConnection()
        self.connect_kwargs = None

    def makedsn(self, host, port, service_name=None, sid=None):
        return f"{host}:{port}/{service_name or sid}"

    def connect(self, **kwargs):
        self.connect_kwargs = dict(kwargs)
        assert kwargs["password"] == "dummy-password"
        return self.connection


class _FailingOracleDriver(_FakeOracleDriver):
    def connect(self, **kwargs):
        self.connect_kwargs = dict(kwargs)
        raise RuntimeError("authentication failed for dummy-password")

def test_w6_collect_db_cli_contract_maps_flags_to_command_namespace(tmp_path: Path) -> None:
    output_dir = tmp_path / "collect"
    parser = build_parser()
    args = parser.parse_args(
        [
            "collect",
            "db",
            "--host",
            "10.10.20.15",
            "--port",
            "1521",
            "--service-name",
            "ORCLPDB1",
            "--username",
            "app_reader",
            "--password-env",
            "DB_PASSWORD",
            "--owner",
            "APP",
            "--owner",
            "COMMON",
            "--output-dir",
            str(output_dir),
            "--timeout",
            "60",
            "--include-comments",
            "--format",
            "json",
        ]
    )
    assert args.host == "10.10.20.15"
    assert args.port == 1521
    assert args.service_name == "ORCLPDB1"
    assert args.sid is None
    assert args.username == "app_reader"
    assert args.password_env == "DB_PASSWORD"
    assert args.owner == ["APP", "COMMON"]
    assert args.output_dir == str(output_dir)
    assert args.timeout == 60
    assert args.include_comments is True
    assert args.db_collect_format == "json"


def test_w6_collect_db_and_generate_db_schema_role_split(tmp_path: Path, monkeypatch) -> None:
    from lab.db import oracle_collector

    run_dir = tmp_path / "run"
    fake_driver = _FakeOracleDriver()
    monkeypatch.setattr(oracle_collector, "load_oracle_driver", lambda: fake_driver)
    monkeypatch.setenv("DB_PASSWORD", "dummy-password")

    assert (
        main(
            [
                "collect",
                "db",
                "--host",
                "db.internal.local",
                "--service-name",
                "ORCLPDB1",
                "--username",
                "app_reader",
                "--password-env",
                "DB_PASSWORD",
                "--owner",
                "APP",
                "--output-dir",
                str(run_dir),
                "--include-comments",
                "--format",
                "json",
            ]
        )
        == 0
    )

    collected_path = run_dir / "db_collection.json"
    assert collected_path.exists()
    collected = json.loads(collected_path.read_text(encoding="utf-8"))
    assert collected["metadata"]["source_type"] == "oracle_live_collection"
    assert collected["metadata"]["collection_mode"] == "live_query"
    assert collected["metadata"]["connection"]["password_mode"] == "env"
    assert collected["metadata"]["connection"]["password_env_name"] == "DB_PASSWORD"
    assert collected["metadata"]["connection"]["owner_filters"] == ["APP"]
    assert "dummy-password" not in json.dumps(collected)
    assert "_".join(["placeholder", "no", "live", "query"]) not in json.dumps(collected)
    assert collected["raw_metadata"]["tables"][0]["table_name"] == "ORDERS"
    assert collected["raw_metadata"]["columns"][0]["column_name"] == "ORDER_ID"
    assert collected["raw_metadata"]["primary_keys"][0]["constraint_name"] == "PK_ORDERS"
    assert collected["raw_metadata"]["foreign_keys"][0]["constraint_name"] == "FK_ORDERS_CUSTOMER"
    assert collected["raw_metadata"]["table_comments"][0]["table_comment"] == "Orders header"
    assert collected["raw_metadata"]["column_comments"][0]["column_comment"] == "Order identifier"

    assert main(["generate", "db-schema", "--input", str(collected_path), "--json-output", str(run_dir / "db_schema.json"), "--output", str(run_dir / "DB_SCHEMA.md")]) == 0

    generated = json.loads((run_dir / "db_schema.json").read_text(encoding="utf-8"))
    assert generated["schema_version"] == "w6.db_schema.v1"
    assert generated["database"]["service_name"] == "ORCLPDB1"
    assert generated["owners"] == ["APP"]
    assert generated["tables"][0]["table_id"] == "APP.ORDERS"
    assert generated["tables"][0]["primary_key"]["columns"] == ["ORDER_ID"]
    assert generated["tables"][0]["foreign_keys"][0]["referenced_table"] == "CUSTOMERS"
    assert generated["needs_review"] is False


def test_w6_collect_db_connection_failure_is_fail_fast_and_secret_safe(tmp_path: Path, monkeypatch, capsys) -> None:
    from lab.db import oracle_collector

    fake_driver = _FailingOracleDriver()
    monkeypatch.setattr(oracle_collector, "load_oracle_driver", lambda: fake_driver)
    monkeypatch.setenv("DB_PASSWORD", "dummy-password")

    exit_code = main(
        [
            "collect",
            "db",
            "--host",
            "db.internal.local",
            "--service-name",
            "ORCLPDB1",
            "--username",
            "app_reader",
            "--password-env",
            "DB_PASSWORD",
            "--owner",
            "APP",
            "--output-dir",
            str(tmp_path / "run"),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert not (tmp_path / "run" / "db_collection.json").exists()
    assert "DB_CONN_FAILED" in captured.err
    assert "dummy-password" not in captured.err


def test_w6_oracle_raw_mapper_handles_composite_keys_and_schema_contract() -> None:
    from lab.db.normalizer import normalize
    from lab.db.oracle_collector import ORACLE_DICTIONARY_VIEWS, _assemble_tables
    from lab.quality.validate_db import validate_db_schema_json

    raw = {
        "tables": [("APP", "ORDER_LINES", "VALID", "N", "NO", None)],
        "columns": [
            ("APP", "ORDER_LINES", "ORDER_ID", 1, "NUMBER", 22, 10, 0, "N", None),
            ("APP", "ORDER_LINES", "LINE_NO", 2, "NUMBER", 22, 10, 0, "N", None),
            ("APP", "ORDER_LINES", "PRODUCT_ID", 3, "NUMBER", 22, 10, 0, "N", None),
            ("APP", "ORDER_LINES", "PRODUCT_VERSION", 4, "NUMBER", 22, 10, 0, "N", None),
        ],
        "primary_keys": [
            ("APP", "ORDER_LINES", "PK_ORDER_LINES", "ORDER_ID", 1, "ENABLED", "NOT DEFERRABLE", "IMMEDIATE"),
            ("APP", "ORDER_LINES", "PK_ORDER_LINES", "LINE_NO", 2, "ENABLED", "NOT DEFERRABLE", "IMMEDIATE"),
        ],
        "foreign_keys": [
            ("APP", "ORDER_LINES", "FK_ORDER_LINES_PRODUCT", "PRODUCT_ID", 1, "APP", "PRODUCTS", "PK_PRODUCTS", "PRODUCT_ID", "ENABLED", "NO ACTION", "NOT DEFERRABLE", "IMMEDIATE"),
            ("APP", "ORDER_LINES", "FK_ORDER_LINES_PRODUCT", "PRODUCT_VERSION", 2, "APP", "PRODUCTS", "PK_PRODUCTS", "PRODUCT_VERSION", "ENABLED", "NO ACTION", "NOT DEFERRABLE", "IMMEDIATE"),
        ],
        "table_comments": [("APP", "ORDER_LINES", "TABLE", "Order line items")],
        "column_comments": [("APP", "ORDER_LINES", "PRODUCT_VERSION", "Product version")],
    }
    descriptions = {
        "tables": [("OWNER",), ("TABLE_NAME",), ("TABLE_STATUS",), ("TEMPORARY",), ("NESTED",), ("IOT_TYPE",)],
        "columns": [
            ("OWNER",),
            ("TABLE_NAME",),
            ("COLUMN_NAME",),
            ("ORDINAL_POSITION",),
            ("DATA_TYPE",),
            ("DATA_LENGTH",),
            ("DATA_PRECISION",),
            ("DATA_SCALE",),
            ("NULLABLE_FLAG",),
            ("DATA_DEFAULT",),
        ],
        "primary_keys": [("OWNER",), ("TABLE_NAME",), ("CONSTRAINT_NAME",), ("COLUMN_NAME",), ("COLUMN_POSITION",), ("CONSTRAINT_STATUS",), ("DEFERRABLE",), ("DEFERRED",)],
        "foreign_keys": [
            ("OWNER",),
            ("TABLE_NAME",),
            ("CONSTRAINT_NAME",),
            ("LOCAL_COLUMN",),
            ("COLUMN_POSITION",),
            ("REFERENCED_OWNER",),
            ("REFERENCED_TABLE",),
            ("REFERENCED_CONSTRAINT_NAME",),
            ("REFERENCED_COLUMN",),
            ("CONSTRAINT_STATUS",),
            ("DELETE_RULE",),
            ("DEFERRABLE",),
            ("DEFERRED",),
        ],
        "table_comments": [("OWNER",), ("TABLE_NAME",), ("TABLE_TYPE",), ("TABLE_COMMENT",)],
        "column_comments": [("OWNER",), ("TABLE_NAME",), ("COLUMN_NAME",), ("COLUMN_COMMENT",)],
    }
    raw_rows = {
        name: [{column[0].lower(): value for column, value in zip(descriptions[name], row)} for row in rows]
        for name, rows in raw.items()
    }

    tables, notes = _assemble_tables(raw_rows, include_comments=True)

    assert notes == []
    table = tables[0]
    assert table["table_id"] == "APP.ORDER_LINES"
    assert [column["name"] for column in table["columns"]] == ["ORDER_ID", "LINE_NO", "PRODUCT_ID", "PRODUCT_VERSION"]
    assert table["primary_key"]["columns"] == ["ORDER_ID", "LINE_NO"]
    fk = table["foreign_keys"][0]
    assert fk["fk_id"] == "APP.ORDER_LINES.FK_ORDER_LINES_PRODUCT"
    assert fk["columns"] == ["PRODUCT_ID", "PRODUCT_VERSION"]
    assert fk["column_mapping"] == [
        {"local_column": "PRODUCT_ID", "referenced_column": "PRODUCT_ID"},
        {"local_column": "PRODUCT_VERSION", "referenced_column": "PRODUCT_VERSION"},
    ]
    assert table["table_comment"] == "Order line items"
    assert table["columns"][3]["comment"] == "Product version"
    assert table["needs_review"] is False
    assert table["unknown"] is False
    assert table["evidence"]
    assert all(column["evidence"] for column in table["columns"])
    assert table["primary_key"]["evidence"]
    assert fk["evidence"]

    db_schema = normalize(
        {
            "metadata": {
                "source_type": "oracle_live_collection",
                "collected_at_utc": "2026-05-07T00:00:00Z",
                "dictionary_views": ORACLE_DICTIONARY_VIEWS,
                "connection": {
                    "host": "db.internal.local",
                    "port": 1521,
                    "target_mode": "service_name",
                    "target": "ORCLPDB1",
                    "owner_filters": ["APP"],
                },
            },
            "tables": tables,
            "notes": notes,
        }
    )
    findings = validate_db_schema_json(db_schema)
    assert [finding for finding in findings if finding["level"] == "ERROR"] == []
    assert db_schema["tables"][0]["columns"][0]["ordinal_position"] == 1
    assert db_schema["tables"][0]["columns"][3]["ordinal_position"] == 4


def test_w6_oracle_mapper_marks_unknown_when_column_metadata_is_incomplete() -> None:
    from lab.db.oracle_collector import _assemble_tables

    tables, notes = _assemble_tables(
        {
            "tables": [{"owner": "APP", "table_name": "BROKEN", "table_status": "VALID"}],
            "columns": [{"owner": "APP", "table_name": "BROKEN", "column_name": "", "ordinal_position": None, "data_type": None, "nullable_flag": "?"}],
            "primary_keys": [],
            "foreign_keys": [],
            "table_comments": [],
            "column_comments": [],
        },
        include_comments=False,
    )

    assert notes == []
    column = tables[0]["columns"][0]
    assert column["name"] == "UNKNOWN"
    assert column["ordinal_position"] == 1
    assert column["needs_review"] is True
    assert column["unknown"] is True
    assert column["evidence"]
    assert tables[0]["needs_review"] is True
    assert tables[0]["unknown"] is True
