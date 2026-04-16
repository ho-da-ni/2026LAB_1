"""Diff command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab.shared_utils import GitUnavailableError, atomic_write_json, normalize_match_pattern
from lab.git.changed_files import build_changed_files


def run(args: argparse.Namespace) -> int:
    includes = [normalize_match_pattern(pattern) for pattern in (args.include or [])]
    excludes = [normalize_match_pattern(pattern) for pattern in (args.exclude or [])]

    try:
        payload = build_changed_files(args.repo, args.base, args.head, includes, excludes)
    except GitUnavailableError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 8
    except RuntimeError as exc:
        print(f"[ERROR] diff ref resolution failed: {exc}", file=sys.stderr)
        return 3

    if args.test_hook_force_integrity_mismatch:
        payload["summary"]["total_files"] += 1

    if payload["summary"]["total_files"] != len(payload["files"]):
        print("[ERROR] changed_files integrity mismatch", file=sys.stderr)
        return 7

    try:
        atomic_write_json(Path(args.output), payload)
    except OSError as exc:
        print(f"[ERROR] failed to write changed_files.json: {exc}", file=sys.stderr)
        return 5

    print(f"Generated: {args.output}")
    return 0
