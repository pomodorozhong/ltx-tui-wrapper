"""Run the last ltx-tui generate settings repeatedly with timestamped outputs."""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import replace
from pathlib import Path

from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.output_paths import timestamped_output_path
from ltx_tui_wrapper.parsing import build_command_argv, format_command
from ltx_tui_wrapper.progress import abort_if_missing_output_directory
from ltx_tui_wrapper.retries import run_with_retries
from ltx_tui_wrapper.runner import prevent_sleep
from ltx_tui_wrapper.video_metadata import write_command_metadata


def format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


def run_batch(
    *,
    count: int,
    max_retries: int = 1,
    continue_on_error: bool = False,
) -> int:
    """Run the saved generate command *count* times."""
    if count < 1:
        raise SystemExit("count must be at least 1")

    base_options = load_last_run()
    if base_options is None:
        raise SystemExit(
            "No saved generate settings found. Run `ltx-tui` once and press Run first."
        )

    if abort_if_missing_output_directory(base_options.output):
        return 1

    failures = 0
    batch_started = time.perf_counter()
    with prevent_sleep():
        for index in range(1, count + 1):
            seed = (
                random.randint(0, 2**31 - 1)
                if base_options.seed == -1
                else base_options.seed
            )
            run_options = replace(
                base_options,
                output=timestamped_output_path(base_options.output),
                seed=seed,
            )
            argv = build_command_argv(run_options)
            print(f"[{index}/{count}] {format_command(run_options)}", flush=True)
            exit_code, elapsed = run_with_retries(
                argv,
                max_retries=max_retries,
                label=f"Run {index}",
            )
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
    from ltx_tui_wrapper.tui.app import run_ltx_tui
    from ltx_tui_wrapper.tui.prefill import AppPrefill, BatchPrefill

    parser = argparse.ArgumentParser(
        prog="ltx-tui-batch",
        description=(
            "Batch tab in ltx-tui: run the last generate command repeatedly. "
            "Each output file gets a timestamp suffix."
        ),
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        metavar="N",
        help="Pre-fill the number of videos to generate",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        metavar="N",
        help="Pre-fill retries per run (default: 1)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Pre-fill continue on error",
    )
    args = parser.parse_args()
    prefill = AppPrefill(
        initial_tab="batch",
        batch=BatchPrefill(
            count=args.count,
            retries=args.retries,
            continue_on_error=args.continue_on_error,
        ),
    )
    raise SystemExit(
        run_ltx_tui(prefill=prefill)
    )


if __name__ == "__main__":
    main()
