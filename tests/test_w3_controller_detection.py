from __future__ import annotations

import json
from pathlib import Path

from lab.cli import main
from lab.controller_detection import build_endpoint_id, detect_endpoints_from_fixture


def test_w3_endpoint_id_is_deterministic() -> None:
    endpoint_id, canonical = build_endpoint_id(
        "GET",
        "/api/users",
        "com.example.UserController#getUsers()",
        "-",
    )
    assert canonical == "v1|GET|/api/users|com.example.UserController#getUsers()|-"
    assert endpoint_id == "ep_64253e4d477784b3"


def test_w3_detect_endpoints_from_fixture_minimum_input() -> None:
    fixture_path = Path("fixtures/controller_detection/endpoints.fixture.json")
    payload = detect_endpoints_from_fixture(fixture_path, case_ids=["C001"])
    assert payload["summary"]["total_endpoints"] == 1
    endpoint = payload["endpoints"][0]
    assert endpoint["method"] == "GET"
    assert endpoint["path"] == "/api/users"
    assert endpoint["endpoint_id"] == "ep_64253e4d477784b3"
    assert isinstance(endpoint["source_evidence"], list)
    assert endpoint["source_evidence"][0]["file"] == "fixtures/controller_detection/endpoints.fixture.json"


def test_w3_detect_endpoints_cli_generates_endpoints_json(tmp_path: Path) -> None:
    output = tmp_path / "endpoints.json"
    rc = main(
        [
            "detect-endpoints",
            "--input",
            "fixtures/controller_detection/endpoints.fixture.json",
            "--case-id",
            "C001",
            "--output",
            str(output),
        ]
    )
    assert rc == 0
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["total_endpoints"] == 1

