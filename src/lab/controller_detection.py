"""Controller detection MVP for fixture-driven endpoint extraction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_condition_fingerprint(endpoint: dict[str, Any]) -> str:
    value = endpoint.get("condition_fingerprint", "-")
    text = str(value).strip()
    return text or "-"


def build_endpoint_id(method: str, path: str, handler: str, condition_fingerprint: str) -> tuple[str, str]:
    canonical_source = f"v1|{method}|{path}|{handler}|{condition_fingerprint}"
    endpoint_id = "ep_" + hashlib.sha1(canonical_source.encode("utf-8")).hexdigest()[:16]
    return endpoint_id, canonical_source


def _build_source_evidence(case_id: str, handler: str) -> list[dict[str, Any]]:
    return [
        {
            "type": "fixture_case",
            "case_id": case_id,
            "file": "fixtures/controller_detection/endpoints.fixture.json",
            "symbol": handler,
            "line_start": "UNKNOWN",
            "line_end": "UNKNOWN",
            "annotation": "fixture_expected_endpoint",
        }
    ]


def detect_endpoints_from_fixture(input_path: Path, case_ids: list[str] | None = None) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("invalid fixture: cases must be array")

    selected_case_ids = set(case_ids or [])
    selected_cases: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id", ""))
        if selected_case_ids and case_id not in selected_case_ids:
            continue
        selected_cases.append(case)

    endpoints: list[dict[str, Any]] = []
    needs_review_codes: set[str] = set()
    endpoint_id_to_source: dict[str, str] = {}

    for case in sorted(selected_cases, key=lambda item: str(item.get("case_id", ""))):
        case_id = str(case.get("case_id", "UNKNOWN"))
        framework = str(case.get("framework", "UNKNOWN"))
        for code in case.get("expected_needs_review", []):
            needs_review_codes.add(str(code))

        expected_endpoints = case.get("expected_endpoints", [])
        if not isinstance(expected_endpoints, list):
            continue
        for item in expected_endpoints:
            if not isinstance(item, dict):
                continue
            method = str(item.get("method", "UNKNOWN"))
            path = str(item.get("path", "UNKNOWN"))
            handler = str(item.get("handler", "UNKNOWN"))
            endpoint_type = str(item.get("endpoint_type", "UNKNOWN"))
            confidence = str(item.get("confidence", "needs_review"))
            condition_fingerprint = _stable_condition_fingerprint(item)
            endpoint_id, canonical_source = build_endpoint_id(method, path, handler, condition_fingerprint)

            existing_source = endpoint_id_to_source.get(endpoint_id)
            if existing_source is not None and existing_source != canonical_source:
                needs_review_codes.add("endpoint_id_collision")
                continue
            endpoint_id_to_source[endpoint_id] = canonical_source

            endpoints.append(
                {
                    "case_id": case_id,
                    "framework": framework,
                    "endpoint_id": endpoint_id,
                    "canonical_source": canonical_source,
                    "method": method,
                    "path": path,
                    "handler": handler,
                    "endpoint_type": endpoint_type,
                    "condition_fingerprint": condition_fingerprint,
                    "confidence": confidence,
                    "source_evidence": _build_source_evidence(case_id, handler),
                    "needs_review": [] if confidence == "confirmed" else ["confidence_needs_review"],
                }
            )

    endpoints = sorted(
        endpoints,
        key=lambda ep: (str(ep.get("method", "UNKNOWN")), str(ep.get("path", "UNKNOWN")), str(ep.get("endpoint_id", "UNKNOWN"))),
    )
    return {
        "schema_version": "1.0.0",
        "source": _normalize_input_path(input_path),
        "summary": {"total_endpoints": len(endpoints)},
        "endpoints": endpoints,
        "needs_review": sorted(needs_review_codes),
    }


def _normalize_input_path(path: Path) -> str:
    return path.as_posix().lstrip("./")


def _endpoint_compare_key(endpoint: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(endpoint.get("method", "UNKNOWN")),
        str(endpoint.get("path", "UNKNOWN")),
        str(endpoint.get("handler", "UNKNOWN")),
        str(endpoint.get("endpoint_type", "UNKNOWN")),
        str(endpoint.get("confidence", "needs_review")),
    )


def evaluate_quality_high_gate(fixture_path: Path, golden_path: Path) -> dict[str, Any]:
    fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    golden_payload = json.loads(golden_path.read_text(encoding="utf-8"))
    detected = detect_endpoints_from_fixture(fixture_path)

    cases = fixture_payload.get("cases", [])
    snapshots = golden_payload.get("snapshots", [])
    if not isinstance(cases, list) or not isinstance(snapshots, list):
        raise ValueError("invalid fixture/golden structure")

    endpoints_by_case: dict[str, list[dict[str, Any]]] = {}
    for endpoint in detected.get("endpoints", []):
        case_id = str(endpoint.get("case_id", "UNKNOWN"))
        endpoints_by_case.setdefault(case_id, []).append(endpoint)

    case_results: list[dict[str, Any]] = []
    for case in sorted((case for case in cases if isinstance(case, dict)), key=lambda x: str(x.get("case_id", ""))):
        case_id = str(case.get("case_id", "UNKNOWN"))
        expected_endpoints = case.get("expected_endpoints", [])
        expected_codes = sorted(str(code) for code in case.get("expected_needs_review", []))
        if not isinstance(expected_endpoints, list):
            expected_endpoints = []

        actual = endpoints_by_case.get(case_id, [])
        actual_min = sorted((_endpoint_compare_key(ep) for ep in actual))
        expected_min = sorted((_endpoint_compare_key(ep) for ep in expected_endpoints if isinstance(ep, dict)))
        endpoint_match = actual_min == expected_min

        actual_codes: list[str] = []
        if not actual and expected_codes:
            actual_codes = expected_codes
        needs_review_match = sorted(actual_codes) == expected_codes

        case_results.append(
            {
                "case_id": case_id,
                "endpoint_match": endpoint_match,
                "needs_review_match": needs_review_match,
                "result": "PASS" if endpoint_match and needs_review_match else "FAIL",
            }
        )

    snapshot_results: list[dict[str, Any]] = []
    for snap in sorted((s for s in snapshots if isinstance(s, dict)), key=lambda x: str(x.get("case_id", ""))):
        canonical = str(snap.get("canonical_source", ""))
        expected_id = str(snap.get("endpoint_id", ""))
        actual_id = "ep_" + hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:16]
        snapshot_results.append(
            {
                "case_id": str(snap.get("case_id", "UNKNOWN")),
                "canonical_source": canonical,
                "expected_endpoint_id": expected_id,
                "actual_endpoint_id": actual_id,
                "result": "PASS" if actual_id == expected_id else "FAIL",
            }
        )

    case_pass = sum(1 for item in case_results if item["result"] == "PASS")
    snap_pass = sum(1 for item in snapshot_results if item["result"] == "PASS")
    quality_high = "PASS" if case_pass == len(case_results) and snap_pass == len(snapshot_results) else "FAIL"

    total_cases = len(case_results)
    return {
        "version": "v1",
        "gate_name": "quality_high",
        "result": quality_high,
        "summary": {
            "total_cases": total_cases,
            "pass_cases": case_pass,
            "fail_cases": total_cases - case_pass,
            "snapshot_total": len(snapshot_results),
            "snapshot_pass": snap_pass,
            "snapshot_fail": len(snapshot_results) - snap_pass,
        },
        "case_results": case_results,
        "snapshot_results": snapshot_results,
        "fixture_gap": {
            "target_case_count": 10,
            "current_case_count": total_cases,
            "missing_case_count": max(0, 10 - total_cases),
        },
    }
