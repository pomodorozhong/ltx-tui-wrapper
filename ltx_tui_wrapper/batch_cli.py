"""Run the last ltx-tui generate settings repeatedly with timestamped outputs."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace

from pathlib import Path

from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.output_paths import timestamped_output_path
from ltx_tui_wrapper.parsing import build_command_argv, format_command
from ltx_tui_wrapper.runner import execute_command, prevent_sleep
from ltx_tui_wrapper.video_metadata import write_command_metadata


def format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


def run_batch(*, count: int, continue_on_error: bool = False) -> int:
    """Run the saved generate command *count* times."""
    if count < 1:
        raise SystemExit("count must be at least 1")

    base_options = load_last_run()
    if base_options is None:
        raise SystemExit(
            "No saved generate settings found. Run `ltx-tui` once and press Run first."
        )

    failures = 0
    batch_started = time.perf_counter()
    with prevent_sleep():
        for index in range(1, count + 1):
            run_options = replace(
                base_options,
                output=timestamped_output_path(base_options.output),
            )
            argv = build_command_argv(run_options)
            print(f"[{index}/{count}] {format_command(run_options)}", flush=True)
            run_started = time.perf_counter()
            exit_code = execute_command(argv, echo=False)
            elapsed = time.perf_counter() - run_started
            if exit_code != 0:
                failures += 1
                print(
                    f"Run {index} failed with exit code {exit_code} "
                    f"after {format_elapsed(elapsed)}.",
                    file=sys.stderr,
                )
                if not continue_on_error:
                    return exit_code
            else:
                write_command_metadata(Path(run_options.output), argv)
                print(
                    f"Run {index} finished in {format_elapsed(elapsed)} -> {run_options.output}",
                    flush=True,
                )

    total_elapsed = time.perf_counter() - batch_started
    succeeded = count - failures
    print(
        f"Batch complete: {succeeded}/{count} succeeded in {format_elapsed(total_elapsed)}.",
        flush=True,
    )
    if failures:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-batch",
        description=(
            "Run the last ltx-tui generate command repeatedly. "
            "Each output file gets a timestamp suffix (e.g. out_20250619_143022.mp4)."
        ),
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        required=True,
        metavar="N",
        help="Number of videos to generate",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep going after a failed run instead of stopping immediately",
    )
    args = parser.parse_args()
    raise SystemExit(run_batch(count=args.count, continue_on_error=args.continue_on_error))


if __name__ == "__main__":
    main()
