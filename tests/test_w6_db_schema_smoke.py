from __future__ import annotations

import json
from pathlib import Path

from lab.cli import build_parser, main
from lab.runtime.fingerprint import stable_sha256


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_w6_db_schema_smoke_from_fixture(tmp_path: Path) -> None:
    fixture_path = Path("tests/fixtures/db/sample_db_input.json")
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_out = run_dir / "db_schema.json"
    md_out = run_dir / "DB_SCHEMA.md"

    assert main(["generate", "db-schema", "--input", str(fixture_path), "--json-output", str(json_out), "--output", str(md_out)]) == 0

    db_schema = json.loads(json_out.read_text(encoding="utf-8"))
    assert db_schema["schema_version"] == "1.0.0"
    assert db_schema["integrity"]["fingerprint"]
    assert "metadata.generated_at_utc" in db_schema["integrity"]["fingerprint_policy"]["exclude"]
    assert "integrity.fingerprint" in db_schema["integrity"]["fingerprint_policy"]["exclude"]
    assert db_schema["tables"][0]["table_name"] == "users"

    markdown = md_out.read_text(encoding="utf-8")
    assert "# DB Schema Overview" in markdown
    assert "## Integrity" in markdown
    assert "### public.users" in markdown


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


def test_w6_validate_db_detects_missing_source_evidence(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    assert main(
        [
            "generate",
            "db-schema",
            "--json-output",
            str(run_dir / "db_schema.json"),
            "--output",
            str(run_dir / "DB_SCHEMA.md"),
        ]
    ) == 0

    db_schema = json.loads((run_dir / "db_schema.json").read_text(encoding="utf-8"))
    db_schema["tables"] = [
        {
            "table_name": "users",
            "schema_name": "public",
            "columns": [{"name": "id", "data_type": "bigint", "nullable": False, "default": "UNKNOWN", "is_primary_key": True, "is_foreign_key": False, "references": {"table": "UNKNOWN", "column": "UNKNOWN"}}],
            "primary_key": {"columns": ["id"]},
            "foreign_keys": [],
            "indexes": [],
            "source_evidence": [],
            "needs_review": [],
        }
    ]
    db_schema["integrity"]["fingerprint"] = stable_sha256(
        db_schema,
        exclude_paths=db_schema["integrity"]["fingerprint_policy"]["exclude"],
    )
    _write_json(run_dir / "db_schema.json", db_schema)

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

    assert main(["validate", "--run-dir", str(run_dir), "--strict"]) == 4
