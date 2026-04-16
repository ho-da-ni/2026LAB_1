"""Shared helpers for CLI modules."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import posixpath
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDES = [".git/", "build/", "target/"]


class GitUnavailableError(RuntimeError):
    """Raised when git executable is not available."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_git(repo: str, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise GitUnavailableError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or exc.stdout.strip() or "git command failed") from exc
    return result.stdout.strip()


def git_value(repo: str, *args: str) -> str:
    try:
        output = run_git(repo, list(args))
    except (RuntimeError, GitUnavailableError):
        return "UNKNOWN"
    return output or "UNKNOWN"


def atomic_write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(output_path)


def normalize_path(path: str) -> str:
    return str(Path(path).as_posix()).lstrip("./")


def normalize_match_pattern(pattern: str) -> str:
    normalized = posixpath.normpath(pattern.replace("\\", "/"))
    return normalized.lstrip("./")


def match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def is_default_excluded(path: str) -> bool:
    for prefix in DEFAULT_EXCLUDES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    return False


def is_excluded(path: str, excludes: list[str]) -> bool:
    if is_default_excluded(path):
        return True
    return match_any(path, excludes)


def is_included(path: str, includes: list[str]) -> bool:
    if not includes:
        return True
    return match_any(path, includes)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except OSError as exc:
        return None, f"failed to read {path}: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid json in {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"invalid json root type in {path}: expected object"
    return payload, None
