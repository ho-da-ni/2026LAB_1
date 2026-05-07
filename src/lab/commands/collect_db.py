"""Collect live Oracle DB metadata."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from lab.db.oracle_collector import (
    DEFAULT_SYSTEM_OWNERS,
    OracleCollectionError,
    OracleConnectionConfig,
    OracleDependencyError,
    collect_oracle_metadata,
    normalize_owner_list,
)
from lab.exit_codes import EXIT_DB_CONNECTION_FAILED, EXIT_INPUT_INVALID, EXIT_OK, EXIT_OUTPUT_WRITE_FAILED
from lab.shared_utils import atomic_write_json


def _resolve_password_mode(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.password is not None:
        return "cli", args.password
    if args.password_stdin:
        return "stdin", sys.stdin.read().rstrip("\n")
    if args.password_env:
        value = os.getenv(args.password_env)
        if value is None:
            return None, f"[DB_CONN_SECRET_MISSING] Password environment variable '{args.password_env}' is not set. Provide --password-env with a valid variable or use --password-stdin."
        return "env", value
    return None, "one password input mode is required"


def _safe_target(args: argparse.Namespace) -> tuple[str, str]:
    if args.service_name:
        return "service_name", args.service_name
    return "sid", args.sid


def _print_connection_failure(args: argparse.Namespace, message: str) -> None:
    target_mode, target = _safe_target(args)
    print(
        f"[DB_CONN_FAILED] {message} host={args.host} port={args.port} {target_mode}={target} username={args.username}. No secret values were logged.",
        file=sys.stderr,
    )


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

    owners = normalize_owner_list(args.owner)
    if len(owners) == 0:
        print("[ERROR] at least one --owner is required for live Oracle collection", file=sys.stderr)
        return EXIT_INPUT_INVALID

    password_mode, password_value_or_error = _resolve_password_mode(args)
    if password_mode is None:
        print(f"[ERROR] {password_value_or_error}", file=sys.stderr)
        return EXIT_INPUT_INVALID
    if not password_value_or_error:
        print("[ERROR] password input is empty", file=sys.stderr)
        return EXIT_INPUT_INVALID

    config = OracleConnectionConfig(
        host=args.host,
        port=args.port,
        service_name=args.service_name,
        sid=args.sid,
        username=args.username,
        password=password_value_or_error,
        password_mode=password_mode,
        password_env_name=args.password_env if password_mode == "env" else None,
        owners=owners,
        output_dir=str(args.output_dir),
        timeout=args.timeout,
        include_comments=bool(args.include_comments),
        system_owners=DEFAULT_SYSTEM_OWNERS,
    )

    try:
        payload = collect_oracle_metadata(config)
    except OracleDependencyError as exc:
        _print_connection_failure(args, str(exc))
        return EXIT_DB_CONNECTION_FAILED
    except OracleCollectionError as exc:
        _print_connection_failure(args, str(exc))
        return EXIT_DB_CONNECTION_FAILED

    output_dir = Path(args.output_dir)
    output_path = output_dir / "db_collection.json"
    try:
        atomic_write_json(output_path, payload)
    except OSError as exc:
        print(f"[ERROR] failed to write db collection output: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_WRITE_FAILED

    print(f"Generated: {output_path}")
    return EXIT_OK
