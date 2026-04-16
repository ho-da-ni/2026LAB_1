"""Analyze command."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab.exit_codes import EXIT_OK, EXIT_OUTPUT_WRITE_FAILED
from lab.shared_utils import atomic_write_json
from lab.git.repo_meta import build_scan_index, collect_repo_meta
from lab.runtime.run_context import build_run_context


def run(args: argparse.Namespace) -> int:
    start = datetime.now(timezone.utc)
    output_dir = Path(args.output_dir)
    try:
        run_context = build_run_context(args, start, datetime.now(timezone.utc))
        repo_meta = collect_repo_meta(args.repo)
        atomic_write_json(output_dir / "run_context.json", run_context)
        atomic_write_json(output_dir / "repo_meta.json", repo_meta)
        atomic_write_json(output_dir / "scan_index.json", build_scan_index(output_dir))
    except OSError as exc:
        print(f"[ERROR] failed to write analyze artifacts: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_WRITE_FAILED

    print(f"Generated: {output_dir / 'run_context.json'}")
    print(f"Generated: {output_dir / 'repo_meta.json'}")
    print(f"Generated: {output_dir / 'scan_index.json'}")
    return EXIT_OK
