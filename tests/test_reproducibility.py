from __future__ import annotations

import json
from pathlib import Path

from lab.markdown_renderer import render_api_markdown, render_spec_markdown
from lab.w4_artifacts import build_features, build_ir_merged


def _load_fixture_endpoints() -> dict:
    fixture_path = Path("fixtures/controller_detection/endpoints.fixture.json")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    cases = fixture.get("cases", [])

    endpoints: list[dict] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        framework = str(case.get("framework", "UNKNOWN"))
        for expected in case.get("expected_endpoints", []):
            if not isinstance(expected, dict):
                continue
            method = str(expected.get("method", "UNKNOWN"))
            path = str(expected.get("path", "UNKNOWN"))
            handler = str(expected.get("handler", "UNKNOWN"))
            endpoints.append(
                {
                    "endpoint_id": f"ep_{method}_{path}_{handler}".replace("/", "_").replace("#", "_"),
                    "framework": framework,
                    "method": method,
                    "path": path,
                    "handler": handler,
                    "source_evidence": [
                        {
                            "file": "fixtures/controller_detection/endpoints.fixture.json",
                            "symbol": handler,
                            "line_start": "UNKNOWN",
                            "line_end": "UNKNOWN",
                            "annotation": "fixture_expected_endpoint",
                        }
                    ],
                    "needs_review": [],
                }
            )

    return {"schema_version": "1.0.0", "endpoints": endpoints}


def test_repro_build_ir_merged_fingerprint_is_stable_for_same_fixture_and_ref() -> None:
    endpoints_payload = _load_fixture_endpoints()

    first = build_ir_merged(endpoints_payload, "main", "feature/repro", "abc123")
    second = build_ir_merged(endpoints_payload, "main", "feature/repro", "abc123")

    assert first["integrity"]["fingerprint"] == second["integrity"]["fingerprint"]


def test_repro_build_features_fingerprint_is_stable_for_same_input() -> None:
    endpoints_payload = _load_fixture_endpoints()
    ir_payload = build_ir_merged(endpoints_payload, "main", "feature/repro", "abc123")

    first = build_features(ir_payload)
    second = build_features(ir_payload)

    assert first["integrity"]["fingerprint"] == second["integrity"]["fingerprint"]


def test_repro_markdown_outputs_are_identical_for_same_input_json(tmp_path: Path) -> None:
    endpoints_payload = _load_fixture_endpoints()
    ir_payload = build_ir_merged(endpoints_payload, "main", "feature/repro", "abc123")
    features_payload = build_features(ir_payload)
    changed_files_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-04-01T00:00:00Z",
        "repo": {"base": "main", "head": "feature/repro", "merge_base": "abc123"},
        "summary": {"total_files": 1, "added": 0, "modified": 1, "deleted": 0, "renamed": 0},
        "files": [{"path": "src/main/java/com/example/DemoController.java", "status": "M", "language": "java"}],
        "filters": {"include_paths": [], "exclude_paths": []},
    }

    api_1 = render_api_markdown(ir_payload, features_payload)
    api_2 = render_api_markdown(ir_payload, features_payload)
    spec_1 = render_spec_markdown(changed_files_payload, features_payload, ir_payload)
    spec_2 = render_spec_markdown(changed_files_payload, features_payload, ir_payload)

    api_1_path = tmp_path / "API_1.md"
    api_2_path = tmp_path / "API_2.md"
    spec_1_path = tmp_path / "SPEC_1.md"
    spec_2_path = tmp_path / "SPEC_2.md"

    api_1_path.write_text(api_1, encoding="utf-8")
    api_2_path.write_text(api_2, encoding="utf-8")
    spec_1_path.write_text(spec_1, encoding="utf-8")
    spec_2_path.write_text(spec_2, encoding="utf-8")

    assert api_1_path.read_text(encoding="utf-8") == api_2_path.read_text(encoding="utf-8")
    assert spec_1_path.read_text(encoding="utf-8") == spec_2_path.read_text(encoding="utf-8")
