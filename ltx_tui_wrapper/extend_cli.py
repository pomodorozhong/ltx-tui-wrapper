"""CLI for extending the last generated video by chaining I2V segments."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.tui.app import run_ltx_tui
from ltx_tui_wrapper.upscale import AI_SCALES, NCNN_MODELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-extend",
        description=(
            "Extend tab in ltx-tui: chain I2V segments from the last generate output "
            "until the combined duration exceeds the target length."
        ),
    )
    parser.add_argument(
        "-l",
        "--length",
        metavar="DURATION",
        help="Pre-fill target total duration (seconds, e.g. 60, 90s, or 1.5m)",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        metavar="N",
        help="Pre-fill retries per segment (default: 1)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Pre-fill path for the final concatenated video",
    )
    parser.add_argument(
        "--timestamp",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Pre-fill whether to append a timestamp suffix to the output name",
    )
    parser.add_argument(
        "--keep-segments",
        action="store_true",
        help="Pre-fill keep segment files",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        metavar="N",
        help="Pre-fill number of extended videos to generate",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Pre-fill continue on error",
    )
    parser.add_argument(
        "--upscale",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Pre-fill AI-upscale last frame between segments",
    )
    parser.add_argument(
        "--upscale-model",
        choices=NCNN_MODELS,
        help="Pre-fill Real-ESRGAN model for --upscale",
    )
    parser.add_argument(
        "--upscale-scale",
        type=int,
        choices=AI_SCALES,
        help="Pre-fill AI upscale factor for --upscale",
    )
    parser.add_argument(
        "--realesrgan-bin",
        help="Pre-fill path to realesrgan-ncnn-vulkan binary",
    )
    parser.add_argument(
        "--models-dir",
        help="Pre-fill path to realesrgan-ncnn-vulkan models directory",
    )
    args = parser.parse_args()

    raise SystemExit(
        run_ltx_tui(
            initial_tab="extend",
            extend_length=args.length,
            extend_retries=args.retries,
            extend_count=args.count,
            extend_output=args.output,
            extend_timestamp=args.timestamp,
            extend_keep_segments=args.keep_segments,
            extend_continue_on_error=args.continue_on_error,
            extend_upscale=args.upscale,
            extend_upscale_model=args.upscale_model,
            extend_upscale_scale=args.upscale_scale,
            extend_realesrgan_bin=args.realesrgan_bin,
            extend_models_dir=args.models_dir,
        )
    )


if __name__ == "__main__":
    main()
