"""Fingerprint helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_sha256(payload: dict[str, Any], *, exclude_keys: list[str] | None = None) -> str:
    """Return deterministic sha256 hash of JSON payload."""
    fingerprint_payload = dict(payload)
    for key in exclude_keys or []:
        fingerprint_payload.pop(key, None)
    source = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()
