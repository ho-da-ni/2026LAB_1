"""Centralized CLI exit codes."""

from __future__ import annotations

EXIT_OK = 0

# Common failures.
EXIT_REF_RESOLUTION_FAILED = 3
EXIT_INPUT_INVALID = 4
EXIT_OUTPUT_WRITE_FAILED = 5
EXIT_INTEGRITY_MISMATCH = 7
EXIT_GIT_UNAVAILABLE = 8
