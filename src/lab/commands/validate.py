"""Validate command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.exit_codes import EXIT_INPUT_INVALID, EXIT_OK
from lab.shared_utils import atomic_write_json
from lab.quality.validate_api import validate_api_markdown, validate_ir_merged
from lab.quality.validate_common import collect_payloads, validate_changed_files, validate_features, validate_run_context
from lab.quality.validate_db import load_and_validate_db_schema_json, validate_db_markdown
from lab.quality.validate_spec import validate_spec_markdown


Finding = dict[str, str]


def run(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    required_files = ["run_context.json", "changed_files.json"]
    optional_files = ["ir_merged.json", "features.json", "API.md", "SPEC.md", "DB_SCHEMA.md"]

    if not run_dir.exists() or not run_dir.is_dir():
        print(f"[ERROR] run directory not found: {run_dir}", file=sys.stderr)
        return EXIT_INPUT_INVALID

    loaded_payloads, findings = collect_payloads(run_dir, required_files, optional_files)
    findings.extend(validate_run_context(loaded_payloads.get("run_context.json", {})))
    findings.extend(validate_changed_files(loaded_payloads.get("changed_files.json", {})))
    findings.extend(validate_ir_merged(loaded_payloads.get("ir_merged.json", {})))
    findings.extend(validate_features(loaded_payloads.get("features.json", {})))
    findings.extend(load_and_validate_db_schema_json(run_dir))
    findings.extend(validate_api_markdown(run_dir))
    findings.extend(validate_spec_markdown(run_dir))
    findings.extend(validate_db_markdown(run_dir))

    errors = [item for item in findings if item["level"] == "ERROR"]
    warnings = [item for item in findings if item["level"] == "WARN"]
    infos = [item for item in findings if item["level"] == "INFO"]

    for item in infos:
        print(f"[INFO] {item['code']} {item['target']}: {item['detail']}")
    for item in warnings:
        print(f"[WARN] {item['code']} {item['target']}: {item['detail']}")
    for item in errors:
        print(f"[ERROR] {item['code']} {item['target']}: {item['detail']}", file=sys.stderr)

    if errors:
        atomic_write_json(
            run_dir / "quality_gate_report.json",
            {
                "status": "error",
                "errors": errors,
                "warnings": warnings,
                "infos": infos,
                "summary": {"error_count": len(errors), "warning_count": len(warnings), "info_count": len(infos)},
            },
        )
        return EXIT_INPUT_INVALID

    if args.strict and warnings:
        print("[ERROR] strict mode enabled and warnings detected", file=sys.stderr)
        atomic_write_json(
            run_dir / "quality_gate_report.json",
            {
                "status": "error",
                "errors": [],
                "warnings": warnings,
                "infos": infos,
                "summary": {"error_count": 0, "warning_count": len(warnings), "info_count": len(infos)},
            },
        )
        return EXIT_INPUT_INVALID

    atomic_write_json(
        run_dir / "quality_gate_report.json",
        {
            "status": "ok",
            "errors": [],
            "warnings": warnings,
            "infos": infos,
            "summary": {"error_count": 0, "warning_count": len(warnings), "info_count": len(infos)},
        },
    )
    print(
        "[OK] validation passed "
        f"(required={len(required_files)}, optional_present={len(loaded_payloads) - len(required_files)}, warnings={len(warnings)}, infos={len(infos)})"
    )
    return EXIT_OK
