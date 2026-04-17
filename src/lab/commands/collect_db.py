"""Collect DB metadata command (W6 contract placeholder)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from lab.exit_codes import EXIT_INPUT_INVALID, EXIT_OK, EXIT_OUTPUT_WRITE_FAILED
from lab.shared_utils import atomic_write_json, utc_now_iso


def _resolve_password_mode(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.password is not None:
        return "cli", args.password
    if args.password_stdin:
        return "stdin", sys.stdin.read().rstrip("\n")
    if args.password_env:
        value = os.getenv(args.password_env)
        if value is None:
            return None, f"environment variable not found: {args.password_env}"
        return "env", value
    return None, "one password input mode is required"


def run(args: argparse.Namespace) -> int:
    if args.port < 1 or args.port > 65535:
        print("[ERROR] --port must be in range 1..65535", file=sys.stderr)
        return EXIT_INPUT_INVALID
    if args.timeout < 1:
        print("[ERROR] --timeout must be >= 1", file=sys.stderr)
        return EXIT_INPUT_INVALID
    if args.db_collect_format != "json":
        print("[ERROR] --format currently supports only 'json'", file=sys.stderr)
        return EXIT_INPUT_INVALID
    if any(owner.strip() == "" for owner in args.owner):
        print("[ERROR] --owner must not be empty", file=sys.stderr)
        return EXIT_INPUT_INVALID

    password_mode, password_value_or_error = _resolve_password_mode(args)
    if password_mode is None:
        print(f"[ERROR] {password_value_or_error}", file=sys.stderr)
        return EXIT_INPUT_INVALID
    if not password_value_or_error:
        print("[ERROR] password input is empty", file=sys.stderr)
        return EXIT_INPUT_INVALID

    connect_target = args.service_name if args.service_name else args.sid
    connect_mode = "service_name" if args.service_name else "sid"

    payload = {
        "metadata": {
            "source_type": "oracle_live_collection",
            "source_path": f"oracle://{args.host}:{args.port}/{connect_target}",
            "snapshot_id": "UNKNOWN",
            "collected_at_utc": utc_now_iso(),
            "collection_mode": "placeholder_no_live_query",
            "connection": {
                "host": args.host,
                "port": args.port,
                "target_mode": connect_mode,
                "target": connect_target,
                "username": args.username,
                "owner_filters": sorted(args.owner),
                "timeout_seconds": args.timeout,
                "include_comments": bool(args.include_comments),
                "password_mode": password_mode,
            },
        },
        "tables": [],
        "needs_review": ["needs_review.db_collection.query_integration_pending"],
    }

    output_dir = Path(args.output_dir)
    output_path = output_dir / "db_collection.json"
    try:
        atomic_write_json(output_path, payload)
    except OSError as exc:
        print(f"[ERROR] failed to write db collection output: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_WRITE_FAILED

    print(f"Generated: {output_path}")
    return EXIT_OK
