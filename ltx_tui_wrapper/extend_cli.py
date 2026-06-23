"""CLI for extending the last generated video by chaining I2V segments."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.extend import parse_target_duration, run_extend_batch
from ltx_tui_wrapper.upscale import AI_SCALES, NCNN_MODELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-extend",
        description=(
            "Extend the last ltx-tui generate output by re-running generation with "
            "each segment's last frame as the next input, until the combined duration "
            "exceeds the target length."
        ),
    )
    parser.add_argument(
        "-l",
        "--length",
        required=True,
        metavar="DURATION",
        help="Target total duration to exceed (seconds, e.g. 60, 90s, or 1.5m)",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=1,
        metavar="N",
        help="Retry each segment generation up to N times on failure (default: 1)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Path for the final concatenated video "
            "(default: <last-output>_extended_<timestamp>.mp4)"
        ),
    )
    parser.add_argument(
        "--timestamp",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Append a timestamp suffix to the output file name "
            "(default: on)"
        ),
    )
    parser.add_argument(
        "--keep-segments",
        action="store_true",
        help="Keep individual segment videos and extracted frames after completion",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        metavar="N",
        help="Number of extended videos to generate (default: 1)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep going after a failed run instead of stopping immediately",
    )
    parser.add_argument(
        "--upscale",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "AI-upscale each segment's last frame before the next generation "
            "(default: off)"
        ),
    )
    parser.add_argument(
        "--upscale-model",
        choices=NCNN_MODELS,
        default="realesrgan-x4plus",
        help=(
            "Real-ESRGAN model for --upscale "
            f"(default: realesrgan-x4plus)"
        ),
    )
    parser.add_argument(
        "--upscale-scale",
        type=int,
        choices=AI_SCALES,
        help="AI upscale factor for --upscale (default: auto from source size)",
    )
    parser.add_argument(
        "--realesrgan-bin",
        help="Path to realesrgan-ncnn-vulkan binary (default: find on PATH)",
    )
    parser.add_argument(
        "--models-dir",
        help="Path to realesrgan-ncnn-vulkan models directory (passed as -m)",
    )
    args = parser.parse_args()

    if args.retries < 1:
        raise SystemExit("retries must be at least 1")
    if args.count < 1:
        raise SystemExit("count must be at least 1")

    try:
        target_duration = parse_target_duration(args.length)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    raise SystemExit(
        run_extend_batch(
            target_duration=target_duration,
            max_retries=args.retries,
            count=args.count,
            final_output=args.output,
            timestamp=args.timestamp,
            keep_segments=args.keep_segments,
            continue_on_error=args.continue_on_error,
            upscale=args.upscale,
            upscale_model=args.upscale_model,
            upscale_scale=args.upscale_scale,
            realesrgan_bin=args.realesrgan_bin,
            models_dir=args.models_dir,
        )
    )


if __name__ == "__main__":
    main()
