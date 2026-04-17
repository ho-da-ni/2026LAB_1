"""Database metadata loader for `lab generate db-schema`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def collect(input_path: str) -> dict[str, Any]:
    path = Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    raise ValueError("db metadata json root must be object")
