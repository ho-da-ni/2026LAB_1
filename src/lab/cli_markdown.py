"""Markdown rendering functions for CLI generate commands."""

from __future__ import annotations

from typing import Any

from lab.cli_shared import utc_now_iso


def render_api_markdown(ir_payload: dict[str, Any], features_payload: dict[str, Any] | None = None) -> str:
    schema_version = ir_payload.get("schema_version", "UNKNOWN")
    generated_at = ir_payload.get("generated_at", "UNKNOWN")
    repo = ir_payload.get("repo", {})
    base = repo.get("base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    head = repo.get("head", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    merge_base = repo.get("merge_base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"

    endpoints_raw = ir_payload.get("endpoints", [])
    endpoints: list[dict[str, Any]] = endpoints_raw if isinstance(endpoints_raw, list) else []
    endpoints_sorted = sorted(
        (ep for ep in endpoints if isinstance(ep, dict)),
        key=lambda ep: (
            str(ep.get("path", "UNKNOWN")),
            str(ep.get("method", "UNKNOWN")),
            str(ep.get("endpoint_id", "UNKNOWN")),
        ),
    )

    feature_by_endpoint: dict[str, str] = {}
    if isinstance(features_payload, dict):
        raw_features = features_payload.get("features", [])
        if isinstance(raw_features, list):
            for feature in raw_features:
                if not isinstance(feature, dict):
                    continue
                feature_id = str(feature.get("feature_id", "UNKNOWN"))
                signals = feature.get("signals", {})
                endpoint_ids = signals.get("endpoints", []) if isinstance(signals, dict) else []
                if not isinstance(endpoint_ids, list):
                    continue
                for endpoint_id in endpoint_ids:
                    feature_by_endpoint[str(endpoint_id)] = feature_id

    lines: list[str] = []
    lines.append("# API Overview")
    lines.append(f"- Endpoint Count: `{len(endpoints_sorted)}`")
    lines.append(f"- Generated At: `{generated_at}`")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- schema_version: `{schema_version}`")
    lines.append("- source: `ir_merged.json`")
    lines.append(f"- base/head/merge_base: `{base}` / `{head}` / `{merge_base}`")
    lines.append("")
    lines.append("## Endpoint Index")
    lines.append("| endpoint_id | method | path | handler | auth | feature_id |")
    lines.append("|---|---|---|---|---|---|")
    for ep in endpoints_sorted:
        handler = ep.get("handler", {})
        signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
        endpoint_id = str(ep.get("endpoint_id", "UNKNOWN"))
        feature_id = feature_by_endpoint.get(endpoint_id, "UNKNOWN")
        lines.append(
            f"| {ep.get('endpoint_id', 'UNKNOWN')} | {ep.get('method', 'UNKNOWN')} | {ep.get('path', 'UNKNOWN')} | "
            f"{signature} | UNKNOWN | {feature_id} |"
        )

    lines.append("")
    lines.append("## Endpoints")
    for ep in endpoints_sorted:
        endpoint_id = ep.get("endpoint_id", "UNKNOWN")
        method = ep.get("method", "UNKNOWN")
        path = ep.get("path", "UNKNOWN")
        handler = ep.get("handler", {})
        signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
        feature_id = feature_by_endpoint.get(str(endpoint_id), "UNKNOWN")
        evidence = ep.get("source_evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        needs_review = ep.get("needs_review", [])
        if not isinstance(needs_review, list):
            needs_review = []

        lines.append(f"### {method} {path} (`{endpoint_id}`)")
        lines.append("")
        lines.append("#### Summary")
        lines.append(f"- Handler: `{signature}`")
        lines.append(f"- Feature: `{feature_id}`")
        lines.append("- Status: `unknown`")
        lines.append("")
        lines.append("#### Request")
        lines.append("- Content-Type: `UNKNOWN`")
        lines.append("- Path Params: `UNKNOWN`")
        lines.append("- Query Params: `UNKNOWN`")
        lines.append("- Headers: `UNKNOWN`")
        lines.append("- Body Schema: `UNKNOWN`")
        lines.append("")
        lines.append("#### Response")
        lines.append("- Success: `UNKNOWN`")
        lines.append("- Error: `UNKNOWN`")
        lines.append("- Response Schema: `UNKNOWN`")
        lines.append("")
        lines.append("#### Security")
        lines.append("- Auth Required: `UNKNOWN`")
        lines.append("- Roles/Scopes: `UNKNOWN`")
        lines.append("")
        lines.append("#### Exceptions")
        lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Source Evidence")
        if evidence:
            for ev in evidence:
                if not isinstance(ev, dict):
                    continue
                file_path = ev.get("file", "UNKNOWN")
                symbol = ev.get("symbol", "UNKNOWN")
                line_start = ev.get("line_start", "UNKNOWN")
                line_end = ev.get("line_end", "UNKNOWN")
                annotation = ev.get("annotation", "UNKNOWN")
                lines.append(f"- File: `{file_path}`")
                lines.append(f"- Symbol: `{symbol}`")
                lines.append(f"- Lines: `L{line_start}-L{line_end}`")
                lines.append(f"- Annotation/Signature: `{annotation}`")
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### needs_review")
        if method == "*":
            lines.append("- `needs_review.http_wildcard`")
        if method in {"UNKNOWN", "UNKNOWN_METHOD"}:
            lines.append("- `needs_review.method_unknown`")
        if needs_review:
            for item in needs_review:
                lines.append(f"- `{item}`")
        else:
            lines.append("- 없음")
        lines.append("")

    top_needs_review = ir_payload.get("needs_review", [])
    if not isinstance(top_needs_review, list):
        top_needs_review = []

    lines.append("## needs_review")
    if top_needs_review:
        lines.append("| code | endpoint_id/target | detail |")
        lines.append("|---|---|---|")
        for item in top_needs_review:
            if isinstance(item, dict):
                code = item.get("code", "UNKNOWN")
                target = item.get("path", "UNKNOWN")
                detail = item.get("detail", "UNKNOWN")
                lines.append(f"| {code} | {target} | {detail} |")
            else:
                lines.append(f"| UNKNOWN | UNKNOWN | {item} |")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Appendix: Source Evidence Summary")
    lines.append("- 본 문서는 `ir_merged.json` 기준 자동 생성되었다.")
    return "\n".join(lines) + "\n"


def render_spec_markdown(changed_files_payload: dict[str, Any], features_payload: dict[str, Any], ir_payload: dict[str, Any]) -> str:
    repo = changed_files_payload.get("repo", {})
    base = repo.get("base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    head = repo.get("head", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    merge_base = repo.get("merge_base", "UNKNOWN") if isinstance(repo, dict) else "UNKNOWN"
    files = changed_files_payload.get("files", [])
    file_rows = sorted((item for item in files if isinstance(item, dict)), key=lambda item: str(item.get("path", "UNKNOWN"))) if isinstance(files, list) else []
    features = features_payload.get("features", [])
    features_rows = sorted(
        (item for item in features if isinstance(item, dict)),
        key=lambda item: (str(item.get("category", "UNKNOWN")), str(item.get("name", "UNKNOWN")), str(item.get("feature_id", "UNKNOWN"))),
    ) if isinstance(features, list) else []

    ir_endpoints = ir_payload.get("endpoints", [])
    endpoint_map: dict[str, dict[str, Any]] = {}
    if isinstance(ir_endpoints, list):
        endpoint_map = {str(ep.get("endpoint_id", "")): ep for ep in ir_endpoints if isinstance(ep, dict)}

    lines: list[str] = []
    lines.append("# Change Specification Overview")
    lines.append("- Project: `UNKNOWN`")
    lines.append(f"- Feature Change Count: `{len(features_rows)}`")
    lines.append(f"- Changed Files: `{len(file_rows)}`")
    lines.append(f"- Generated At: `{utc_now_iso()}`")
    lines.append("")
    lines.append("## Metadata")
    lines.append("- schema_version: `1.0.0`")
    lines.append(f"- base/head/merge_base: `{base}` / `{head}` / `{merge_base}`")
    lines.append("- inputs: `changed_files.json`, `features.json`, `ir_merged.json`")
    lines.append("")
    lines.append("## Diff Summary")
    lines.append("| path | change_type | language | feature_id | evidence_ref |")
    lines.append("|---|---|---|---|---|")
    for row in file_rows:
        lines.append(
            f"| {row.get('path', 'UNKNOWN')} | {row.get('status', 'UNKNOWN')} | {row.get('language', 'UNKNOWN')} | UNKNOWN | {row.get('path', 'UNKNOWN')} |"
        )
    lines.append("")
    lines.append("## Feature Changes")
    for feature in features_rows:
        feature_id = str(feature.get("feature_id", "UNKNOWN"))
        name = str(feature.get("name", "UNKNOWN"))
        lines.append(f"### {name} (`{feature_id}`)")
        lines.append("")
        lines.append("#### Change Intent")
        lines.append("- 변경 목적: `UNKNOWN`")
        lines.append("")
        lines.append("#### Affected Files")
        evidence = feature.get("evidence", [])
        evidence_rows = evidence if isinstance(evidence, list) else []
        if evidence_rows:
            for ev in evidence_rows:
                if not isinstance(ev, dict):
                    continue
                source = ev.get("source", {})
                source_file = source.get("file", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                lines.append(f"- `{source_file}` (`UNKNOWN`)")
        else:
            lines.append("- `UNKNOWN` (`UNKNOWN`)")
        lines.append("")
        lines.append("#### Behavior Delta")
        lines.append("- Before: `UNKNOWN`")
        lines.append("- After: `UNKNOWN`")
        lines.append("- Trigger/Condition: `UNKNOWN`")
        lines.append("")
        lines.append("#### Contract Delta")
        lines.append("- Input Contract: `UNKNOWN`")
        lines.append("- Output Contract: `UNKNOWN`")
        lines.append("- Error/Exception Contract: `UNKNOWN`")
        lines.append("")
        lines.append("#### Dependency/Impact")
        lines.append("- Upstream Impact: `UNKNOWN`")
        lines.append("- Downstream Impact: `UNKNOWN`")
        lines.append("")
        lines.append("#### Evidence")
        if evidence_rows:
            for ev in evidence_rows:
                if not isinstance(ev, dict):
                    continue
                source = ev.get("source", {})
                source_file = source.get("file", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                symbol = source.get("symbol", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                line_start = source.get("line_start", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                line_end = source.get("line_end", "UNKNOWN") if isinstance(source, dict) else "UNKNOWN"
                lines.append(f"- File: `{source_file}`")
                lines.append(f"- Symbol: `{symbol}`")
                lines.append(f"- Lines: `L{line_start}-L{line_end}`")
                lines.append("- Diff Hunk: `UNKNOWN`")
        else:
            lines.append("- File: `UNKNOWN`")
            lines.append("- Symbol: `UNKNOWN`")
            lines.append("- Lines: `UNKNOWN`")
            lines.append("- Diff Hunk: `UNKNOWN`")
        lines.append("")
        lines.append("#### needs_review")
        if not evidence_rows:
            lines.append("- `needs_review.evidence_missing`")
        lines.append("- `needs_review.spec_unknown_contract`")
        lines.append("")

    lines.append("## Interface/API Changes (Optional)")
    lines.append("| endpoint_id | method | path | handler | feature_id |")
    lines.append("|---|---|---|---|---|")
    for feature in features_rows:
        feature_id = str(feature.get("feature_id", "UNKNOWN"))
        signals = feature.get("signals", {})
        endpoint_ids = signals.get("endpoints", []) if isinstance(signals, dict) else []
        if not isinstance(endpoint_ids, list):
            continue
        for endpoint_id in sorted(str(item) for item in endpoint_ids):
            endpoint = endpoint_map.get(endpoint_id, {})
            handler = endpoint.get("handler", {})
            signature = handler.get("signature", "UNKNOWN") if isinstance(handler, dict) else "UNKNOWN"
            lines.append(
                f"| {endpoint_id} | {endpoint.get('method', 'UNKNOWN')} | {endpoint.get('path', 'UNKNOWN')} | {signature} | {feature_id} |"
            )
    lines.append("")
    lines.append("## Data/Schema Changes (Optional)")
    lines.append("- `UNKNOWN`")
    lines.append("")
    lines.append("## Risk & Compatibility")
    lines.append("- breaking_change: `unknown`")
    lines.append("- rollout_risk: `unknown`")
    lines.append("- rollback_plan: `UNKNOWN`")
    lines.append("")
    lines.append("## Validation Plan")
    lines.append("- Command: `PYTHONPATH=src pytest -q`")
    lines.append("- Expected: `PASS`")
    lines.append("- Actual: `UNKNOWN`")
    lines.append("")
    lines.append("## needs_review")
    lines.append("| code | target | detail | evidence_ref |")
    lines.append("|---|---|---|---|")
    lines.append("| needs_review.spec_unknown_contract | SPEC | UNKNOWN contract fields included | SPEC.md |")
    lines.append("")
    lines.append("## Appendix: Evidence Index")
    lines.append("| file path | ref_count | symbols |")
    lines.append("|---|---:|---|")
    evidence_index: dict[str, set[str]] = {}
    for feature in features_rows:
        evidence = feature.get("evidence", [])
        if not isinstance(evidence, list):
            continue
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            source = ev.get("source", {})
            if not isinstance(source, dict):
                continue
            file_path = str(source.get("file", "UNKNOWN"))
            symbol = str(source.get("symbol", "UNKNOWN"))
            evidence_index.setdefault(file_path, set()).add(symbol)
    for file_path in sorted(evidence_index):
        symbols = sorted(evidence_index[file_path])
        lines.append(f"| {file_path} | {len(symbols)} | {', '.join(symbols)} |")
    if not evidence_index:
        lines.append("| UNKNOWN | 0 | UNKNOWN |")
    return "\n".join(lines) + "\n"
