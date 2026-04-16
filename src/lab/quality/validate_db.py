"""DB schema validation placeholder rules."""

from __future__ import annotations

from pathlib import Path


Finding = dict[str, str]


def validate_db_markdown(run_dir: Path) -> list[Finding]:
    markdown_path = run_dir / "DB_SCHEMA.md"
    if not markdown_path.exists():
        return [{"level": "INFO", "code": "QR-COMMON-003", "target": str(markdown_path), "detail": "optional file not found"}]
    return []
