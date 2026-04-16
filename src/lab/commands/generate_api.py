"""Generate API markdown command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from lab.markdown_renderer import render_api_markdown
from lab.shared_utils import load_json_file


def run(args: argparse.Namespace) -> int:
    payload, error = load_json_file(Path(args.input))
    if error or payload is None:
        print(f"[ERROR] failed to load input: {error}", file=sys.stderr)
        return 4

    features_payload: dict[str, Any] | None = None
    if getattr(args, "features", None):
        feature_payload, feature_error = load_json_file(Path(args.features))
        if feature_error or feature_payload is None:
            print(f"[ERROR] failed to load features input: {feature_error}", file=sys.stderr)
            return 4
        features_payload = feature_payload

    markdown = render_api_markdown(payload, features_payload=features_payload)
    output_path = Path(args.output)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] failed to write api markdown: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {output_path}")
    return 0
