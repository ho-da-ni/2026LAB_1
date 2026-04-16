"""Database metadata collector placeholder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def collect(input_path: str | None = None) -> dict[str, Any]:
    if input_path:
        path = Path(input_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        raise ValueError("db metadata json root must be object")
    return {
        "source_type": "UNKNOWN",
        "source_path": "UNKNOWN",
        "snapshot_id": "UNKNOWN",
        "collected_at_utc": "UNKNOWN",
        "tables": [],
    }
