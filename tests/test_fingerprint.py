from __future__ import annotations

from lab.runtime.fingerprint import stable_sha256


def test_stable_sha256_supports_nested_exclude_paths() -> None:
    payload = {
        "metadata": {"generated_at_utc": "2026-04-01T00:00:00Z", "workspace": {"root_path": "/tmp/out", "os": "Linux"}},
        "execution": {"duration_ms": 1234, "exit_code": 0},
        "integrity": {"fingerprint": "UNKNOWN"},
    }

    fingerprint = stable_sha256(
        payload,
        exclude_paths=[
            "metadata.generated_at_utc",
            "metadata.workspace.root_path",
            "execution.duration_ms",
            "integrity.fingerprint",
        ],
    )
    changed_payload = {
        "metadata": {"generated_at_utc": "2099-01-01T00:00:00Z", "workspace": {"root_path": "/another/path", "os": "Linux"}},
        "execution": {"duration_ms": 9999, "exit_code": 0},
        "integrity": {"fingerprint": "DIFFERENT"},
    }
    changed_fingerprint = stable_sha256(
        changed_payload,
        exclude_paths=[
            "metadata.generated_at_utc",
            "metadata.workspace.root_path",
            "execution.duration_ms",
            "integrity.fingerprint",
        ],
    )
    assert fingerprint == changed_fingerprint


def test_stable_sha256_does_not_mutate_payload_when_excluding_nested_path() -> None:
    payload = {"metadata": {"workspace": {"root_path": "/tmp/out"}}}
    stable_sha256(payload, exclude_paths=["metadata.workspace.root_path"])
    assert payload["metadata"]["workspace"]["root_path"] == "/tmp/out"
