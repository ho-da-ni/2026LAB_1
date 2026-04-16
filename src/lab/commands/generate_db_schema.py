"""Generate DB schema json/markdown command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.db.collector import collect
from lab.db.normalizer import normalize
from lab.db.renderer import render
from lab.exit_codes import EXIT_INPUT_INVALID, EXIT_OK, EXIT_OUTPUT_WRITE_FAILED
from lab.shared_utils import atomic_write_json


def run(args: argparse.Namespace) -> int:
    try:
        raw = collect(args.db_schema_input)
    except (OSError, ValueError) as exc:
        print(f"[ERROR] failed to load db metadata input: {exc}", file=sys.stderr)
        return EXIT_INPUT_INVALID

    payload = normalize(raw)
    markdown = render(payload)

    json_output_path = Path(args.db_schema_json_output)
    markdown_output_path = Path(args.db_schema_output)
    try:
        atomic_write_json(json_output_path, payload)
        markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write db schema outputs: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_WRITE_FAILED

    print(f"Generated: {json_output_path}")
    print(f"Generated: {markdown_output_path}")
    return EXIT_OK
