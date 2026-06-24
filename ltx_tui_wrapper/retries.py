"""Retry helpers for long-running CLI workflows."""

from __future__ import annotations

import time

from ltx_tui_wrapper.progress import print_status_band
from ltx_tui_wrapper.runner import execute_command


def run_with_retries(
    argv: list[str],
    *,
    max_retries: int,
    label: str,
) -> tuple[int, float]:
    """Run *argv*, retrying up to *max_retries* times on non-zero exit."""
    from ltx_tui_wrapper.batch_cli import format_elapsed

    attempts = max(1, max_retries)
    exit_code = 1
    elapsed = 0.0
    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        exit_code = execute_command(argv, echo=False)
        elapsed = time.perf_counter() - started
        if exit_code == 0:
            return 0, elapsed
        if attempt < attempts:
            print_status_band(
                f"{label} failed with exit code {exit_code} "
                f"after {format_elapsed(elapsed)}; "
                f"retrying ({attempt}/{attempts})…",
                success=False,
            )
    return exit_code, elapsed
