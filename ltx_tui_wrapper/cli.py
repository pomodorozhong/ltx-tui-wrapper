"""CLI entry point for ltx-tui."""

from __future__ import annotations

import argparse

from pathlib import Path

from ltx_tui_wrapper.tui.app import run_ltx_tui
from ltx_tui_wrapper.tui.prefill import AppPrefill, GeneratePrefill


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui",
        description="Textual TUI for building and running ltx-2-mlx generate commands.",
    )
    parser.add_argument(
        "--prompt",
        "-p",
        help="Pre-fill the prompt field",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Pre-fill the output path",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=Path,
        help="Pre-fill the reference image path",
    )
    args = parser.parse_args()
    prefill = AppPrefill(
        generate=GeneratePrefill(
            prompt=args.prompt,
            output=args.output,
            image=args.image,
        )
    )
    raise SystemExit(
        run_ltx_tui(prefill=prefill)
    )


if __name__ == "__main__":
    main()
