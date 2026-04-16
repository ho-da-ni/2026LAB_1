"""Detect endpoints command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab.cli_shared import atomic_write_json
from lab.controller_detection import detect_endpoints_from_fixture


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    case_ids = args.case_id or []
    try:
        payload = detect_endpoints_from_fixture(input_path, case_ids=case_ids)
    except OSError as exc:
        print(f"[ERROR] failed to read fixture input: {exc}", file=sys.stderr)
        return 4
    except json.JSONDecodeError as exc:
        print(f"[ERROR] invalid fixture json: {exc}", file=sys.stderr)
        return 4
    except ValueError as exc:
        print(f"[ERROR] invalid fixture format: {exc}", file=sys.stderr)
        return 4

    try:
        atomic_write_json(output_path, payload)
    except OSError as exc:
        print(f"[ERROR] failed to write endpoints.json: {exc}", file=sys.stderr)
        return 5
    print(f"Generated: {output_path}")
    return 0
