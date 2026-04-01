from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.controller_detection import detect_endpoints_from_fixture, evaluate_quality_high_gate


def _stable_hash(payload: dict) -> str:
    source = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def test_w3_fixture_and_golden_quality_high_gate_passes() -> None:
    fixture = Path("fixtures/controller_detection/endpoints.fixture.json")
    golden = Path("fixtures/controller_detection/golden_snapshots.json")

    report = evaluate_quality_high_gate(fixture, golden)
    assert report["result"] == "PASS"
    assert report["summary"]["fail_cases"] == 0
    assert report["summary"]["snapshot_fail"] == 0


def test_w3_detection_is_deterministic_for_same_input() -> None:
    fixture = Path("fixtures/controller_detection/endpoints.fixture.json")
    first = detect_endpoints_from_fixture(fixture)
    second = detect_endpoints_from_fixture(fixture)
    assert _stable_hash(first) == _stable_hash(second)


def test_w3_fixture_gap_is_reported_for_less_than_10_cases() -> None:
    fixture = Path("fixtures/controller_detection/endpoints.fixture.json")
    golden = Path("fixtures/controller_detection/golden_snapshots.json")
    report = evaluate_quality_high_gate(fixture, golden)
    assert report["fixture_gap"]["target_case_count"] == 10
    assert report["fixture_gap"]["current_case_count"] == 10
    assert report["fixture_gap"]["missing_case_count"] == 0


def test_w3_new_fixture_cases_are_included_in_quality_gate() -> None:
    fixture = Path("fixtures/controller_detection/endpoints.fixture.json")
    golden = Path("fixtures/controller_detection/golden_snapshots.json")
    report = evaluate_quality_high_gate(fixture, golden)
    case_ids = {item["case_id"] for item in report["case_results"]}
    assert {"M001", "M002", "C003", "C004"}.issubset(case_ids)
