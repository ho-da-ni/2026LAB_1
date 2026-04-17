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
    run_dir = tmp_path / "run"
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
    assert "dummy-password" not in json.dumps(collected)

    assert main(["generate", "db-schema", "--input", str(collected_path), "--json-output", str(run_dir / "db_schema.json"), "--output", str(run_dir / "DB_SCHEMA.md")]) == 0

    generated = json.loads((run_dir / "db_schema.json").read_text(encoding="utf-8"))
    assert generated["schema_version"] == "w6.db_schema.v1"
    assert generated["database"]["service_name"] == "ORCLPDB1"
    assert generated["owners"] == ["APP"]
    assert generated["needs_review"] is True
