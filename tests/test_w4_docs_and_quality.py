from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.cli import main
from lab.runtime.fingerprint import stable_sha256


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_w4_generate_api_and_spec_outputs_sections(tmp_path: Path) -> None:
    ir = {
        "schema_version": "1.0.0",
        "generated_at": "2026-04-01T00:00:00Z",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "endpoints": [
            {
                "endpoint_id": "ep_demo",
                "method": "*",
                "path": "/users",
                "handler": {"signature": "com.example.UserController#getUsers()", "framework": "spring_boot"},
                "source_evidence": [
                    {"file": "src/UserController.java", "symbol": "getUsers", "line_start": 1, "line_end": 10, "annotation": "@GetMapping"}
                ],
                "needs_review": [],
            }
        ],
        "needs_review": [],
    }
    features = {
        "schema_version": "1.0.0",
        "generated_at": "2026-04-01T00:00:00Z",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "features": [
            {
                "feature_id": "feat_1111111111111111",
                "name": "/users",
                "category": "api",
                "status": "unknown",
                "signals": {"endpoints": ["ep_demo"], "tables": [], "jobs": []},
                "evidence": [
                    {"type": "code", "source": {"file": "src/UserController.java", "symbol": "getUsers", "line_start": 1, "line_end": 10}}
                ],
                "needs_review": [],
            }
        ],
    }
    changed = {
        "schema_version": "1.0.0",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "summary": {"total_files": 1, "added": 0, "modified": 1, "deleted": 0, "renamed": 0},
        "files": [{"path": "src/UserController.java", "status": "M", "language": "java"}],
        "filters": {"include_paths": [], "exclude_paths": []},
    }

    ir_path = tmp_path / "ir_merged.json"
    features_path = tmp_path / "features.json"
    changed_path = tmp_path / "changed_files.json"
    api_path = tmp_path / "API.md"
    spec_path = tmp_path / "SPEC.md"
    _write_json(ir_path, ir)
    _write_json(features_path, features)
    _write_json(changed_path, changed)

    assert main(["generate", "api", "--input", str(ir_path), "--features", str(features_path), "--output", str(api_path)]) == 0
    assert main(
        [
            "generate",
            "spec",
            "--changed-files",
            str(changed_path),
            "--features",
            str(features_path),
            "--ir",
            str(ir_path),
            "--output",
            str(spec_path),
        ]
    ) == 0

    api_text = api_path.read_text(encoding="utf-8")
    assert "## Endpoint Index" in api_text
    assert "needs_review.http_wildcard" in api_text
    spec_text = spec_path.read_text(encoding="utf-8")
    assert "## Diff Summary" in spec_text
    assert "## Feature Changes" in spec_text


def test_w4_validate_strict_vs_non_strict(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
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
    _write_json(
        run_dir / "run_context.json",
        run_context,
    )
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
    _write_json(
        run_dir / "changed_files.json",
        changed_files,
    )
    ir_merged = {
        "schema_version": "1.0.0",
        "metadata": {"generated_at_utc": "2026-04-01T00:00:00Z"},
        "endpoints": [{"endpoint_id": "ep_demo", "method": "UNKNOWN", "path": "/x", "source_evidence": [{"file": "a", "symbol": "b"}]}],
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": ["metadata.generated_at_utc", "integrity.fingerprint"],
            },
        },
    }
    ir_merged["integrity"]["fingerprint"] = stable_sha256(ir_merged, exclude_paths=["metadata.generated_at_utc", "integrity.fingerprint"])
    _write_json(
        run_dir / "ir_merged.json",
        ir_merged,
    )

    assert main(["validate", "--run-dir", str(run_dir)]) == 0
    assert main(["validate", "--run-dir", str(run_dir), "--strict"]) == 4


def test_w4_generate_api_is_deterministic_for_same_input(tmp_path: Path) -> None:
    ir = {
        "schema_version": "1.0.0",
        "generated_at": "2026-04-01T00:00:00Z",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "endpoints": [
            {
                "endpoint_id": "ep_demo",
                "method": "GET",
                "path": "/deterministic",
                "handler": {"signature": "com.example.Demo#get()", "framework": "spring_boot"},
                "source_evidence": [{"file": "src/Demo.java", "symbol": "get", "line_start": 1, "line_end": 2, "annotation": "@GetMapping"}],
                "needs_review": [],
            }
        ],
        "needs_review": [],
    }
    ir_path = tmp_path / "ir_merged.json"
    _write_json(ir_path, ir)
    out1 = tmp_path / "API1.md"
    out2 = tmp_path / "API2.md"
    assert main(["generate", "api", "--input", str(ir_path), "--output", str(out1)]) == 0
    assert main(["generate", "api", "--input", str(ir_path), "--output", str(out2)]) == 0
    h1 = hashlib.sha256(out1.read_bytes()).hexdigest()
    h2 = hashlib.sha256(out2.read_bytes()).hexdigest()
    assert h1 == h2


def test_w4_generate_spec_is_deterministic_for_same_input(tmp_path: Path) -> None:
    changed = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-04-01T00:00:00Z",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "summary": {"total_files": 1, "added": 0, "modified": 1, "deleted": 0, "renamed": 0},
        "files": [{"path": "src/UserController.java", "status": "M", "language": "java"}],
        "filters": {"include_paths": [], "exclude_paths": []},
    }
    features = {
        "schema_version": "1.0.0",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "features": [
            {
                "feature_id": "feat_1111111111111111",
                "name": "/users",
                "category": "api",
                "signals": {"endpoints": ["ep_demo"], "tables": [], "jobs": []},
                "evidence": [{"type": "code", "source": {"file": "src/UserController.java", "symbol": "getUsers", "line_start": 1, "line_end": 10}}],
            }
        ],
    }
    ir = {
        "schema_version": "1.0.0",
        "repo": {"base": "main", "head": "work", "merge_base": "abc"},
        "endpoints": [
            {
                "endpoint_id": "ep_demo",
                "method": "GET",
                "path": "/users",
                "handler": {"signature": "com.example.UserController#getUsers()", "framework": "spring_boot"},
                "source_evidence": [],
                "needs_review": [],
            }
        ],
    }
    changed_path = tmp_path / "changed_files.json"
    features_path = tmp_path / "features.json"
    ir_path = tmp_path / "ir_merged.json"
    out1 = tmp_path / "SPEC1.md"
    out2 = tmp_path / "SPEC2.md"
    _write_json(changed_path, changed)
    _write_json(features_path, features)
    _write_json(ir_path, ir)
    assert main(["generate", "spec", "--changed-files", str(changed_path), "--features", str(features_path), "--ir", str(ir_path), "--output", str(out1)]) == 0
    assert main(["generate", "spec", "--changed-files", str(changed_path), "--features", str(features_path), "--ir", str(ir_path), "--output", str(out2)]) == 0
    assert hashlib.sha256(out1.read_bytes()).hexdigest() == hashlib.sha256(out2.read_bytes()).hexdigest()


def test_w4_generate_db_schema_default_like_invocation_returns_zero(tmp_path: Path) -> None:
    json_out = tmp_path / "db_schema.json"
    md_out = tmp_path / "DB_SCHEMA.md"
    assert main(["generate", "db-schema", "--json-output", str(json_out), "--output", str(md_out)]) == 0


def test_w4_validate_reproducibility_rules_detect_policy_mismatch(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

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

    ir_merged = {
        "schema_version": "1.0.0",
        "metadata": {"generated_at_utc": "2026-04-01T00:00:00Z"},
        "endpoints": [{"endpoint_id": "ep_demo", "method": "GET", "path": "/x", "source_evidence": [{"file": "a", "symbol": "b"}]}],
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": ["integrity.fingerprint"],
            },
        },
    }
    ir_merged["integrity"]["fingerprint"] = stable_sha256(ir_merged, exclude_paths=["integrity.fingerprint"])
    _write_json(run_dir / "ir_merged.json", ir_merged)

    assert main(["validate", "--run-dir", str(run_dir)]) == 4


def test_w4_generate_db_schema_outputs_json_and_markdown(tmp_path: Path) -> None:
    db_meta = {
        "source_type": "snapshot",
        "source_path": "artifacts/input/db_meta.json",
        "snapshot_id": "snap_001",
        "collected_at_utc": "2026-04-01T00:00:00Z",
        "tables": [
            {
                "table_name": "users",
                "schema_name": "public",
                "columns": [
                    {"name": "id", "data_type": "bigint", "nullable": False, "default": None, "is_primary_key": True},
                    {"name": "email", "data_type": "varchar", "nullable": False, "default": "UNKNOWN", "is_primary_key": False},
                ],
                "primary_key": {"columns": ["id"]},
                "foreign_keys": [],
                "indexes": [{"name": "idx_users_email", "unique": True, "columns": ["email"]}],
                "source_evidence": [{"file": "schema.sql", "symbol": "create table users", "line_start": 1, "line_end": 20}],
                "needs_review": [],
            }
        ],
    }
    input_path = tmp_path / "db_meta.json"
    input_path.write_text(json.dumps(db_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    json_out = tmp_path / "db_schema.json"
    md_out = tmp_path / "DB_SCHEMA.md"

    assert main(
        [
            "generate",
            "db-schema",
            "--input",
            str(input_path),
            "--json-output",
            str(json_out),
            "--output",
            str(md_out),
        ]
    ) == 0

    db_schema = json.loads(json_out.read_text(encoding="utf-8"))
    assert db_schema["schema_version"] == "1.0.0"
    assert isinstance(db_schema["integrity"]["fingerprint"], str)
    assert db_schema["tables"][0]["table_name"] == "users"
    markdown = md_out.read_text(encoding="utf-8")
    assert "# DB Schema Overview" in markdown
    assert "## Table Index" in markdown
    assert "### public.users" in markdown


def test_w4_validate_db_schema_markdown_sections_and_unknown_policy(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
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

    db_schema = {
        "schema_version": "1.0.0",
        "metadata": {
            "generated_at_utc": "2026-04-01T00:00:00Z",
            "source_type": "UNKNOWN",
            "source_path": "UNKNOWN",
            "snapshot_id": "UNKNOWN",
            "collected_at_utc": "UNKNOWN",
        },
        "tables": [],
        "needs_review": ["needs_review.db_schema.empty"],
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy": {
                "algorithm": "sha256",
                "normalization": "stable_json_canonicalization",
                "exclude": ["metadata.generated_at_utc", "integrity.fingerprint"],
            },
        },
    }
    db_schema["integrity"]["fingerprint"] = stable_sha256(db_schema, exclude_paths=["metadata.generated_at_utc", "integrity.fingerprint"])
    _write_json(run_dir / "db_schema.json", db_schema)
    (run_dir / "DB_SCHEMA.md").write_text("# bad\n- `UNKNOWN`\n", encoding="utf-8")

    assert main(["validate", "--run-dir", str(run_dir)]) == 4
