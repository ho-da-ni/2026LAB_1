"""Database markdown renderer."""

from __future__ import annotations

from typing import Any


def render(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    meta = metadata if isinstance(metadata, dict) else {}
    generated_at = str(meta.get("generated_at_utc", "UNKNOWN"))
    source_type = str(meta.get("source_type", "UNKNOWN"))
    source_path = str(meta.get("source_path", "UNKNOWN"))
    snapshot_id = str(meta.get("snapshot_id", "UNKNOWN"))
    collected_at = str(meta.get("collected_at_utc", "UNKNOWN"))

    integrity = payload.get("integrity", {})
    integrity_obj = integrity if isinstance(integrity, dict) else {}
    fingerprint = str(integrity_obj.get("fingerprint", "UNKNOWN"))
    policy = integrity_obj.get("fingerprint_policy", {})
    policy_obj = policy if isinstance(policy, dict) else {}
    excludes = policy_obj.get("exclude", [])
    excludes_list = [str(item) for item in excludes] if isinstance(excludes, list) else []

    tables_raw = payload.get("tables", [])
    tables = (item for item in tables_raw if isinstance(item, dict)) if isinstance(tables_raw, list) else []
    table_rows = sorted(tables, key=lambda t: (str(t.get("schema_name", "UNKNOWN")), str(t.get("table_name", "UNKNOWN"))))
    needs_review_raw = payload.get("needs_review", [])
    needs_review = sorted(str(code) for code in needs_review_raw) if isinstance(needs_review_raw, list) else []

    lines: list[str] = []
    lines.append("# DB Schema Overview")
    lines.append(f"- Table Count: `{len(table_rows)}`")
    lines.append(f"- Generated At: `{generated_at}`")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- schema_version: `{payload.get('schema_version', 'UNKNOWN')}`")
    lines.append(f"- source_type: `{source_type}`")
    lines.append(f"- source_path: `{source_path}`")
    lines.append(f"- snapshot_id: `{snapshot_id}`")
    lines.append(f"- collected_at_utc: `{collected_at}`")
    lines.append("")
    lines.append("## Integrity")
    lines.append(f"- fingerprint: `{fingerprint}`")
    lines.append(f"- fingerprint_policy.algorithm: `{policy_obj.get('algorithm', 'UNKNOWN')}`")
    lines.append(f"- fingerprint_policy.normalization: `{policy_obj.get('normalization', 'UNKNOWN')}`")
    if excludes_list:
        lines.append("- fingerprint_policy.exclude:")
        for item in excludes_list:
            lines.append(f"  - `{item}`")
    else:
        lines.append("- fingerprint_policy.exclude: `UNKNOWN`")
    lines.append("")
    lines.append("## Table Index")
    lines.append("| schema | table_name | column_count | primary_key | foreign_key_count |")
    lines.append("|---|---|---:|---|---:|")
    for table in table_rows:
        pk = table.get("primary_key", {})
        pk_columns = pk.get("columns", []) if isinstance(pk, dict) else []
        fks = table.get("foreign_keys", [])
        fk_count = len(fks) if isinstance(fks, list) else 0
        columns = table.get("columns", [])
        column_count = len(columns) if isinstance(columns, list) else 0
        pk_text = ", ".join(str(col) for col in pk_columns) if isinstance(pk_columns, list) and pk_columns else "UNKNOWN"
        lines.append(
            f"| {table.get('schema_name', 'UNKNOWN')} | {table.get('table_name', 'UNKNOWN')} | {column_count} | {pk_text} | {fk_count} |"
        )

    lines.append("")
    lines.append("## Tables")
    for table in table_rows:
        schema_name = table.get("schema_name", "UNKNOWN")
        table_name = table.get("table_name", "UNKNOWN")
        columns = table.get("columns", [])
        foreign_keys = table.get("foreign_keys", [])
        indexes = table.get("indexes", [])
        source_evidence = table.get("source_evidence", [])
        table_needs_review = table.get("needs_review", [])

        lines.append(f"### {schema_name}.{table_name}")
        lines.append("")
        lines.append("#### Columns")
        if isinstance(columns, list) and columns:
            lines.append("| name | data_type | nullable | default | is_pk | is_fk | references |")
            lines.append("|---|---|---|---|---|---|---|")
            for col in sorted((item for item in columns if isinstance(item, dict)), key=lambda c: str(c.get("name", "UNKNOWN"))):
                refs = col.get("references", {})
                refs_obj = refs if isinstance(refs, dict) else {}
                ref_text = f"{refs_obj.get('table', 'UNKNOWN')}.{refs_obj.get('column', 'UNKNOWN')}"
                lines.append(
                    f"| {col.get('name', 'UNKNOWN')} | {col.get('data_type', 'UNKNOWN')} | {col.get('nullable', 'UNKNOWN')} | "
                    f"{col.get('default', 'UNKNOWN')} | {col.get('is_primary_key', False)} | {col.get('is_foreign_key', False)} | {ref_text} |"
                )
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Primary Key")
        pk = table.get("primary_key", {})
        pk_columns = pk.get("columns", []) if isinstance(pk, dict) else []
        if isinstance(pk_columns, list) and pk_columns:
            for col in pk_columns:
                lines.append(f"- `{col}`")
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Foreign Keys")
        if isinstance(foreign_keys, list) and foreign_keys:
            for fk in foreign_keys:
                if not isinstance(fk, dict):
                    continue
                lines.append(
                    f"- `{fk.get('name', 'UNKNOWN')}`: `{fk.get('column', 'UNKNOWN')}` -> "
                    f"`{fk.get('references_table', 'UNKNOWN')}.{fk.get('references_column', 'UNKNOWN')}`"
                )
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Indexes")
        if isinstance(indexes, list) and indexes:
            for index in indexes:
                if not isinstance(index, dict):
                    continue
                cols = index.get("columns", [])
                col_text = ", ".join(str(c) for c in cols) if isinstance(cols, list) and cols else "UNKNOWN"
                lines.append(f"- `{index.get('name', 'UNKNOWN')}` ({index.get('unique', 'UNKNOWN')}): `{col_text}`")
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### Source Evidence")
        if isinstance(source_evidence, list) and source_evidence:
            for ev in source_evidence:
                if not isinstance(ev, dict):
                    continue
                lines.append(
                    f"- `{ev.get('file', 'UNKNOWN')}` `{ev.get('symbol', 'UNKNOWN')}` "
                    f"`L{ev.get('line_start', 'UNKNOWN')}-L{ev.get('line_end', 'UNKNOWN')}`"
                )
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")
        lines.append("#### needs_review")
        if isinstance(table_needs_review, list) and table_needs_review:
            for code in table_needs_review:
                lines.append(f"- `{code}`")
        else:
            lines.append("- 없음")
        lines.append("")

    lines.append("## needs_review")
    if needs_review:
        for code in needs_review:
            lines.append(f"- `{code}`")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Appendix: Source Evidence Summary")
    lines.append("- 본 문서는 `db_schema.json` 기준 자동 생성되었다.")
    return "\n".join(lines) + "\n"
