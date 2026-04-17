"""Database markdown renderer."""

from __future__ import annotations


def render(payload: dict[str, object]) -> str:
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    database = payload.get("database") if isinstance(payload.get("database"), dict) else {}
    owners = payload.get("owners") if isinstance(payload.get("owners"), list) else []
    tables_raw = payload.get("tables") if isinstance(payload.get("tables"), list) else []
    tables = [table for table in tables_raw if isinstance(table, dict)]
    tables = sorted(tables, key=lambda t: str(t.get("table_id", "UNKNOWN")))
    notes = payload.get("notes") if isinstance(payload.get("notes"), list) else []

    lines: list[str] = []
    lines.append("# DB Schema Overview")
    lines.append(f"- schema_version: `{payload.get('schema_version', 'UNKNOWN')}`")
    lines.append(f"- table_count: `{len(tables)}`")
    lines.append(f"- needs_review: `{bool(payload.get('needs_review', False))}`")
    lines.append("")

    lines.append("## Source")
    lines.append(f"- collector: `{source.get('collector', 'UNKNOWN')}`")
    lines.append(f"- collected_at: `{source.get('collected_at', 'UNKNOWN')}`")
    dictionary_views = source.get("dictionary_views") if isinstance(source.get("dictionary_views"), list) else []
    lines.append("- dictionary_views:")
    if dictionary_views:
        for view_name in dictionary_views:
            lines.append(f"  - `{view_name}`")
    else:
        lines.append("  - `UNKNOWN`")
    lines.append("")

    lines.append("## Database")
    lines.append(f"- vendor: `{database.get('vendor', 'UNKNOWN')}`")
    lines.append(f"- host: `{database.get('host', 'UNKNOWN')}`")
    lines.append(f"- port: `{database.get('port', 'UNKNOWN')}`")
    lines.append(f"- service_name: `{database.get('service_name', 'UNKNOWN')}`")
    lines.append(f"- sid: `{database.get('sid', 'UNKNOWN')}`")
    lines.append("")

    lines.append("## Owners")
    if owners:
        for owner in owners:
            lines.append(f"- `{owner}`")
    else:
        lines.append("- `UNKNOWN`")
    lines.append("")

    lines.append("## Table Index")
    lines.append("| table_id | owner | table_name | column_count | pk | fk_count | unknown | needs_review |")
    lines.append("|---|---|---|---:|---|---:|---|---|")
    for table in tables:
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        pk = table.get("primary_key") if isinstance(table.get("primary_key"), dict) else None
        pk_columns = pk.get("columns") if isinstance(pk, dict) and isinstance(pk.get("columns"), list) else []
        foreign_keys = table.get("foreign_keys") if isinstance(table.get("foreign_keys"), list) else []
        lines.append(
            f"| {table.get('table_id', 'UNKNOWN')} | {table.get('owner', 'UNKNOWN')} | {table.get('table_name', 'UNKNOWN')} | "
            f"{len(columns)} | {', '.join(str(c) for c in pk_columns) if pk_columns else 'NONE'} | {len(foreign_keys)} | "
            f"{table.get('unknown', True)} | {table.get('needs_review', True)} |"
        )

    lines.append("")
    lines.append("## Tables")
    for table in tables:
        lines.append(f"### {table.get('table_id', 'UNKNOWN')}")
        lines.append(f"- table_comment: `{table.get('table_comment')}`")
        lines.append(f"- unknown: `{table.get('unknown', True)}`")
        lines.append(f"- needs_review: `{table.get('needs_review', True)}`")
        lines.append("")

        lines.append("#### Columns")
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        if columns:
            lines.append("| ordinal | name | data_type | nullable | unknown | needs_review |")
            lines.append("|---:|---|---|---|---|---|")
            for col in columns:
                if not isinstance(col, dict):
                    continue
                lines.append(
                    f"| {col.get('ordinal_position', 'UNKNOWN')} | {col.get('name', 'UNKNOWN')} | {col.get('data_type', 'UNKNOWN')} | "
                    f"{col.get('nullable', 'UNKNOWN')} | {col.get('unknown', True)} | {col.get('needs_review', True)} |"
                )
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")

        lines.append("#### Primary Key")
        pk = table.get("primary_key")
        if isinstance(pk, dict):
            lines.append(f"- constraint_name: `{pk.get('constraint_name', 'UNKNOWN')}`")
            pk_columns = pk.get("columns") if isinstance(pk.get("columns"), list) else []
            lines.append(f"- columns: `{', '.join(str(c) for c in pk_columns) if pk_columns else 'NONE'}`")
            lines.append(f"- unknown: `{pk.get('unknown', True)}`")
            lines.append(f"- needs_review: `{pk.get('needs_review', True)}`")
        else:
            lines.append("- `NONE`")
        lines.append("")

        lines.append("#### Foreign Keys")
        foreign_keys = table.get("foreign_keys") if isinstance(table.get("foreign_keys"), list) else []
        if foreign_keys:
            for fk in foreign_keys:
                if not isinstance(fk, dict):
                    continue
                lines.append(
                    f"- `{fk.get('fk_id', 'UNKNOWN')}` -> `{fk.get('referenced_owner', 'UNKNOWN')}.{fk.get('referenced_table', 'UNKNOWN')}` "
                    f"(unknown={fk.get('unknown', True)}, needs_review={fk.get('needs_review', True)})"
                )
        else:
            lines.append("- `NONE`")
        lines.append("")

        lines.append("#### Evidence")
        evidence = table.get("evidence") if isinstance(table.get("evidence"), list) else []
        if evidence:
            for ev in evidence:
                if not isinstance(ev, dict):
                    continue
                lines.append(
                    f"- `{ev.get('source_view', 'UNKNOWN')}` owner=`{ev.get('owner', 'UNKNOWN')}` object=`{ev.get('object_name', 'UNKNOWN')}`"
                )
        else:
            lines.append("- `UNKNOWN`")
        lines.append("")

    lines.append("## Notes")
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Appendix: Source Evidence Summary")
    lines.append("- 본 문서는 `db_schema.json` 기준 자동 생성되었다.")
    return "\n".join(lines) + "\n"
