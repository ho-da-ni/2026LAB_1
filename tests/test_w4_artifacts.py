from __future__ import annotations

import copy
import json
from pathlib import Path

from lab.cli import _build_feature_id, main
from lab.runtime.fingerprint import stable_sha256


def test_w4_build_artifacts_generates_ir_merged_and_features(tmp_path: Path) -> None:
    endpoints_payload = {
        "schema_version": "1.0.0",
        "endpoints": [
            {
                "endpoint_id": "ep_1111111111111111",
                "framework": "spring_boot",
                "method": "GET",
                "path": "/users",
                "handler": "com.example.UserController#getUsers()",
                "source_evidence": [
                    {
                        "file": "src/main/java/com/example/UserController.java",
                        "symbol": "UserController#getUsers",
                        "line_start": 10,
                        "line_end": 20,
                        "annotation": "@GetMapping(\"/users\")",
                    }
                ],
                "needs_review": [],
            }
        ],
    }
    endpoints_path = tmp_path / "endpoints.json"
    endpoints_path.write_text(json.dumps(endpoints_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_dir = tmp_path / "out"

    rc = main(
        [
            "build-w4",
            "--endpoints-input",
            str(endpoints_path),
            "--output-dir",
            str(output_dir),
            "--base",
            "main",
            "--head",
            "work",
            "--merge-base",
            "abc123",
        ]
    )
    assert rc == 0

    ir_path = output_dir / "ir_merged.json"
    feat_path = output_dir / "features.json"
    assert ir_path.exists()
    assert feat_path.exists()

    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    assert ir["repo"]["base"] == "main"
    assert ir["endpoints"][0]["method"] == "GET"
    assert ir["endpoints"][0]["path"] == "/users"
    assert ir["endpoints"][0]["handler"]["signature"] == "com.example.UserController#getUsers()"
    assert "metadata" in ir
    assert isinstance(ir["integrity"]["fingerprint"], str)
    canonical_ir = copy.deepcopy(ir)
    canonical_ir["metadata"].pop("generated_at_utc", None)
    canonical_ir["integrity"]["fingerprint"] = "UNKNOWN"
    assert ir["integrity"]["fingerprint"] == stable_sha256(canonical_ir)

    features = json.loads(feat_path.read_text(encoding="utf-8"))
    assert len(features["features"]) == 1
    first = features["features"][0]
    assert first["signals"]["endpoints"] == ["ep_1111111111111111"]
    assert len(first["evidence"]) == 1
    assert first["feature_id"].startswith("feat_")
    assert "metadata" in features
    canonical_features = copy.deepcopy(features)
    canonical_features["metadata"].pop("generated_at_utc", None)
    canonical_features["integrity"]["fingerprint"] = "UNKNOWN"
    assert features["integrity"]["fingerprint"] == stable_sha256(canonical_features)


def test_w4_feature_id_is_deterministic() -> None:
    first = _build_feature_id("api", "/users", ["ep_a"], [], ["get"])
    second = _build_feature_id("api", "/users", ["ep_a"], [], ["get"])
    assert first == second
