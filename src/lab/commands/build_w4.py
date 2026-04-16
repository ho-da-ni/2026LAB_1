"""Build W4 artifacts command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.cli_shared import atomic_write_json, load_json_file
from lab.cli_w4 import build_features, build_ir_merged


def run(args: argparse.Namespace) -> int:
    endpoints_payload, error = load_json_file(Path(args.endpoints_input))
    if error or endpoints_payload is None:
        print(f"[ERROR] failed to load endpoints input: {error}", file=sys.stderr)
        return 4

    ir_merged_payload = build_ir_merged(endpoints_payload, args.base, args.head, args.merge_base)
    features_payload = build_features(ir_merged_payload)
    output_dir = Path(args.output_dir)
    try:
        atomic_write_json(output_dir / "ir_merged.json", ir_merged_payload)
        atomic_write_json(output_dir / "features.json", features_payload)
    except OSError as exc:
        print(f"[ERROR] failed to write W4 artifacts: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_dir / 'ir_merged.json'}")
    print(f"Generated: {output_dir / 'features.json'}")
    return 0
