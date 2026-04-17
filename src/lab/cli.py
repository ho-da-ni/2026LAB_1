"""LAB CLI entrypoint: argparse + dispatch only."""

from __future__ import annotations

import argparse
from typing import Sequence

from lab.commands import (
    analyze,
    build_w4,
    collect_db,
    detect_endpoints,
    diff,
    generate_api,
    generate_db_schema,
    generate_spec,
    validate,
)
from lab.exit_codes import EXIT_OK
from lab.git.changed_files import build_changed_files
from lab.w4_artifacts import build_feature_id

# Backward-compatible re-exports used by tests and external callers.
_build_changed_files = build_changed_files
_build_feature_id = build_feature_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="LAB CLI")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository and build run context")
    analyze_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    analyze_parser.add_argument("--output-dir", required=True, help="Output directory for analysis artifacts")

    collect_parser = subparsers.add_parser("collect", help="Collect source metadata artifacts")
    collect_subparsers = collect_parser.add_subparsers(dest="collect_command", metavar="TARGET")
    collect_db_parser = collect_subparsers.add_parser("db", help="Collect DB metadata JSON")
    collect_db_parser.add_argument("--host", required=True, help="DB host or IP")
    collect_db_parser.add_argument("--port", type=int, default=1521, help="DB listener port (default: 1521)")
    collect_target_group = collect_db_parser.add_mutually_exclusive_group(required=True)
    collect_target_group.add_argument("--service-name", help="Oracle service name (mutually exclusive with --sid)")
    collect_target_group.add_argument("--sid", help="Oracle SID (mutually exclusive with --service-name)")
    collect_db_parser.add_argument("--username", required=True, help="DB login username")
    collect_password_group = collect_db_parser.add_mutually_exclusive_group(required=True)
    collect_password_group.add_argument("--password", help="DB password (plain text, discouraged)")
    collect_password_group.add_argument("--password-stdin", action="store_true", help="Read DB password from stdin")
    collect_password_group.add_argument("--password-env", help="Read DB password from environment variable name")
    collect_db_parser.add_argument("--owner", action="append", default=[], help="Schema owner filter (repeatable)")
    collect_db_parser.add_argument("--output-dir", required=True, help="Output directory for db collection artifact")
    collect_db_parser.add_argument("--timeout", type=int, default=30, help="DB query timeout in seconds (default: 30)")
    collect_db_parser.add_argument("--include-comments", action="store_true", help="Include comments metadata")
    collect_db_parser.add_argument("--format", dest="db_collect_format", default="json", help="Output format (json only)")

    generate_parser = subparsers.add_parser("generate", help="Generate markdown artifacts")
    generate_subparsers = generate_parser.add_subparsers(dest="generate_command", metavar="TARGET")
    generate_api_parser = generate_subparsers.add_parser("api", help="Generate API.md")
    generate_api_parser.add_argument("--input", required=True, help="Input ir_merged.json path")
    generate_api_parser.add_argument("--output", required=True, help="Output API.md path")
    generate_api_parser.add_argument("--features", help="Optional features.json path for endpoint-feature mapping")
    generate_spec_parser = generate_subparsers.add_parser("spec", help="Generate SPEC.md")
    generate_spec_parser.add_argument("--changed-files", required=True, help="Input changed_files.json path")
    generate_spec_parser.add_argument("--features", required=True, help="Input features.json path")
    generate_spec_parser.add_argument("--ir", required=True, help="Input ir_merged.json path")
    generate_spec_parser.add_argument("--output", required=True, help="Output SPEC.md path")
    generate_db_parser = generate_subparsers.add_parser("db-schema", help="Render DB_SCHEMA.md from collected db metadata")
    generate_db_parser.add_argument("--input", dest="db_schema_input", required=True, help="DB collection JSON input path")
    generate_db_parser.add_argument(
        "--json-output",
        dest="db_schema_json_output",
        default="db_schema.json",
        help="Output db_schema.json path",
    )
    generate_db_parser.add_argument(
        "--output",
        dest="db_schema_output",
        default="DB_SCHEMA.md",
        help="Output DB_SCHEMA.md path",
    )

    diff_parser = subparsers.add_parser("diff", help="Collect changed files between refs")
    diff_parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    diff_parser.add_argument("--base", required=True, help="Base git ref")
    diff_parser.add_argument("--head", required=True, help="Head git ref")
    diff_parser.add_argument("--output", required=True, help="Path to write changed_files.json")
    diff_parser.add_argument("--include", action="append", help="Include path/glob pattern")
    diff_parser.add_argument("--exclude", action="append", help="Exclude path/glob pattern")
    diff_parser.add_argument("--test-hook-force-integrity-mismatch", action="store_true", help=argparse.SUPPRESS)

    validate_parser = subparsers.add_parser("validate", help="Validate generated artifacts")
    validate_parser.add_argument("--run-dir", required=True, help="Directory containing generated artifacts")
    validate_parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    detect_parser = subparsers.add_parser("detect-endpoints", help="Detect endpoints from controller fixtures")
    detect_parser.add_argument("--input", required=True, help="Input fixture json path")
    detect_parser.add_argument("--output", required=True, help="Output endpoints.json path")
    detect_parser.add_argument("--case-id", action="append", help="Fixture case id filter (repeatable)")

    w4_parser = subparsers.add_parser("build-w4", help="Build W4 artifacts (ir_merged.json, features.json)")
    w4_parser.add_argument("--endpoints-input", required=True, help="Input endpoints.json path")
    w4_parser.add_argument("--output-dir", required=True, help="Output directory")
    w4_parser.add_argument("--base", default="UNKNOWN", help="Repo base ref")
    w4_parser.add_argument("--head", default="UNKNOWN", help="Repo head ref")
    w4_parser.add_argument("--merge-base", default="UNKNOWN", help="Repo merge-base ref")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return EXIT_OK

    if args.command == "collect" and args.collect_command is None:
        parser.parse_args(["collect", "--help"])
        return EXIT_OK

    if args.command == "generate" and args.generate_command is None:
        parser.parse_args(["generate", "--help"])
        return EXIT_OK

    if args.command == "analyze":
        return analyze.run(args)
    if args.command == "collect" and args.collect_command == "db":
        return collect_db.run(args)
    if args.command == "diff":
        return diff.run(args)
    if args.command == "validate":
        return validate.run(args)
    if args.command == "detect-endpoints":
        return detect_endpoints.run(args)
    if args.command == "build-w4":
        return build_w4.run(args)
    if args.command == "generate" and args.generate_command == "api":
        return generate_api.run(args)
    if args.command == "generate" and args.generate_command == "spec":
        return generate_spec.run(args)
    if args.command == "generate" and args.generate_command == "db-schema":
        return generate_db_schema.run(args)

    print(f"[TODO] '{args.command}' command is not implemented yet.")
    return EXIT_OK
