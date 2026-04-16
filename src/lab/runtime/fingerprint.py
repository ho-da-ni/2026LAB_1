"""Fingerprint helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _drop_by_path(target: Any, path: str) -> None:
    parts = [segment for segment in path.split(".") if segment]
    if not parts:
        return

    cursor: Any = target
    for segment in parts[:-1]:
        if isinstance(cursor, dict):
            if segment not in cursor:
                return
            cursor = cursor[segment]
            continue
        if isinstance(cursor, list) and segment.isdigit():
            index = int(segment)
            if index < 0 or index >= len(cursor):
                return
            cursor = cursor[index]
            continue
        return

    leaf = parts[-1]
    if isinstance(cursor, dict):
        cursor.pop(leaf, None)
    elif isinstance(cursor, list) and leaf.isdigit():
        index = int(leaf)
        if 0 <= index < len(cursor):
            cursor.pop(index)


def stable_sha256(
    payload: dict[str, Any], *, exclude_paths: list[str] | None = None, exclude_keys: list[str] | None = None
) -> str:
    """Return deterministic sha256 hash of JSON payload."""
    fingerprint_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    for path in exclude_paths or []:
        _drop_by_path(fingerprint_payload, path)
    for key in exclude_keys or []:
        _drop_by_path(fingerprint_payload, key)
    source = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()
