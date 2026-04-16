"""W4 artifact composition logic."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from lab.shared_utils import utc_now_iso
from lab.runtime.fingerprint import stable_sha256


def normalize_endpoint_evidence(evidence: Any) -> list[dict[str, Any]]:
    items = evidence if isinstance(evidence, list) else []
    normalized: list[dict[str, Any]] = []
    for ev in items:
        if not isinstance(ev, dict):
            continue
        normalized.append(
            {
                "file": str(ev.get("file", "UNKNOWN")),
                "symbol": str(ev.get("symbol", "UNKNOWN")),
                "line_start": ev.get("line_start", "UNKNOWN"),
                "line_end": ev.get("line_end", "UNKNOWN"),
                "annotation": str(ev.get("annotation", "UNKNOWN")),
            }
        )
    normalized = sorted(
        normalized,
        key=lambda ev: (str(ev["file"]), str(ev["symbol"]), str(ev["line_start"]), str(ev["line_end"])),
    )
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for ev in normalized:
        key = (str(ev["file"]), str(ev["symbol"]), str(ev["line_start"]), str(ev["line_end"]), str(ev["annotation"]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    return unique


def build_ir_merged(endpoints_payload: dict[str, Any], repo_base: str, repo_head: str, repo_merge_base: str) -> dict[str, Any]:
    raw_endpoints = endpoints_payload.get("endpoints", [])
    endpoints = raw_endpoints if isinstance(raw_endpoints, list) else []

    merged_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: dict[tuple[str, str], set[str]] = {}

    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        method = str(ep.get("method", "UNKNOWN")).upper()
        path = str(ep.get("path", "UNKNOWN"))
        framework = str(ep.get("framework", "UNKNOWN"))
        handler_signature = str(ep.get("handler", "UNKNOWN"))
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        needs_review = ep.get("needs_review", [])
        if not isinstance(needs_review, list):
            needs_review = []
        source_evidence = normalize_endpoint_evidence(ep.get("source_evidence", []))
        key = (method, path)

        if key in merged_by_key:
            current = merged_by_key[key]
            current_handler = current["handler"]["signature"]
            if current_handler != handler_signature:
                conflicts.setdefault(key, {current_handler}).add(handler_signature)
                continue
            current["source_evidence"] = normalize_endpoint_evidence(current["source_evidence"] + source_evidence)
            current["needs_review"] = sorted(set(current["needs_review"]) | set(str(item) for item in needs_review))
            continue

        merged_by_key[key] = {
            "endpoint_id": endpoint_id,
            "handler": {"signature": handler_signature, "framework": framework},
            "method": method,
            "path": path,
            "paths": [path],
            "methods": [method],
            "produces": [],
            "consumes": [],
            "source_evidence": source_evidence,
            "needs_review": sorted(set(str(item) for item in needs_review)),
        }

    merged_endpoints = sorted(
        merged_by_key.values(),
        key=lambda item: (str(item["path"]), str(item["method"]), str(item["endpoint_id"])),
    )
    top_needs_review: list[dict[str, Any]] = []
    for (method, path), handlers in sorted(conflicts.items(), key=lambda item: (item[0][1], item[0][0])):
        top_needs_review.append(
            {
                "code": "needs_review.mapping_route_conflict",
                "method": method,
                "path": path,
                "handlers": sorted(handlers),
                "detail": "동일 METHOD+PATH에 handler 충돌",
            }
        )

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "repo": {"base": repo_base, "head": repo_head, "merge_base": repo_merge_base},
        "endpoints": merged_endpoints,
        "needs_review": top_needs_review,
        "metadata": {"generated_at_utc": utc_now_iso()},
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy_version": "1.0.0",
            "exclude": ["metadata.generated_at_utc"],
        },
    }
    fingerprint_payload = copy.deepcopy(payload)
    metadata = fingerprint_payload.get("metadata", {})
    if isinstance(metadata, dict):
        metadata.pop("generated_at_utc", None)
    payload["integrity"]["fingerprint"] = stable_sha256(fingerprint_payload)
    return payload


def build_feature_id(category: str, name: str, endpoint_ids: list[str], tables: list[str], tags: list[str]) -> str:
    normalized_name = name.strip().lower()
    source = json.dumps(
        [category, normalized_name, sorted(set(endpoint_ids)), sorted(set(tables)), sorted(set(tags))],
        ensure_ascii=False,
        sort_keys=True,
    )
    return "feat_" + hashlib.sha1(source.encode("utf-8")).hexdigest()[:16]


def build_features(ir_merged_payload: dict[str, Any]) -> dict[str, Any]:
    endpoints = ir_merged_payload.get("endpoints", [])
    endpoint_list = endpoints if isinstance(endpoints, list) else []
    features: list[dict[str, Any]] = []

    for ep in endpoint_list:
        if not isinstance(ep, dict):
            continue
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        path = str(ep.get("path", "UNKNOWN"))
        method = str(ep.get("method", "UNKNOWN"))
        handler = ep.get("handler", {})
        signature = str(handler.get("signature", "UNKNOWN")) if isinstance(handler, dict) else "UNKNOWN"
        feature_name = path if path != "UNKNOWN" else signature
        category = "api"
        tags = sorted(set([method.lower()])) if method != "UNKNOWN" else []
        evidence: list[dict[str, Any]] = []
        for ev in ep.get("source_evidence", []):
            if not isinstance(ev, dict):
                continue
            evidence.append(
                {
                    "type": "code",
                    "source": {
                        "file": str(ev.get("file", "UNKNOWN")),
                        "symbol": str(ev.get("symbol", "UNKNOWN")),
                        "line_start": ev.get("line_start", "UNKNOWN"),
                        "line_end": ev.get("line_end", "UNKNOWN"),
                    },
                    "snippet_hash": "UNKNOWN",
                    "confidence": "medium",
                    "note": str(ev.get("annotation", "UNKNOWN")),
                }
            )
        evidence = sorted(
            evidence,
            key=lambda item: (
                str(item["type"]),
                str(item["source"]["file"]),
                str(item["source"]["symbol"]),
                str(item["source"]["line_start"]),
                str(item["source"]["line_end"]),
            ),
        )
        feature = {
            "feature_id": build_feature_id(category, feature_name, [endpoint_id], [], tags),
            "name": feature_name if feature_name else "UNKNOWN",
            "category": category,
            "status": "unknown",
            "description": "UNKNOWN",
            "tags": tags,
            "owners": [],
            "signals": {"endpoints": [endpoint_id], "tables": [], "jobs": []},
            "evidence": evidence,
            "needs_review": [],
        }
        if not evidence:
            feature["needs_review"].append("needs_review.evidence_missing")
        if feature["name"] == "UNKNOWN":
            feature["needs_review"].append("needs_review.feature_name_unknown")
        features.append(feature)

    features = sorted(features, key=lambda item: (str(item["category"]), str(item["name"]), str(item["feature_id"])))
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "repo": ir_merged_payload.get("repo", {"base": "UNKNOWN", "head": "UNKNOWN", "merge_base": "UNKNOWN"}),
        "features": features,
        "metadata": {"generated_at_utc": utc_now_iso()},
        "integrity": {
            "fingerprint": "UNKNOWN",
            "fingerprint_policy_version": "1.0.0",
            "exclude": ["metadata.generated_at_utc"],
        },
    }
    fingerprint_payload = copy.deepcopy(payload)
    metadata = fingerprint_payload.get("metadata", {})
    if isinstance(metadata, dict):
        metadata.pop("generated_at_utc", None)
    payload["integrity"]["fingerprint"] = stable_sha256(fingerprint_payload)
    return payload
