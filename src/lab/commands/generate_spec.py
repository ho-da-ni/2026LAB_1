"""Generate spec markdown command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.cli_markdown import render_spec_markdown
from lab.cli_shared import load_json_file


def run(args: argparse.Namespace) -> int:
    changed_payload, changed_error = load_json_file(Path(args.changed_files))
    if changed_error or changed_payload is None:
        print(f"[ERROR] failed to load changed_files input: {changed_error}", file=sys.stderr)
        return 4
    features_payload, features_error = load_json_file(Path(args.features))
    if features_error or features_payload is None:
        print(f"[ERROR] failed to load features input: {features_error}", file=sys.stderr)
        return 4
    ir_payload, ir_error = load_json_file(Path(args.ir))
    if ir_error or ir_payload is None:
        print(f"[ERROR] failed to load ir input: {ir_error}", file=sys.stderr)
        return 4

    markdown = render_spec_markdown(changed_payload, features_payload, ir_payload)
    output_path = Path(args.output)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write spec markdown: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_path}")
    return 0
