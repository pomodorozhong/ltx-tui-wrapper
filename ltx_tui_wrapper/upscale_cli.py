"""CLI for upscaling a video to 1920×1080."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.tui.app import run_ltx_tui
from ltx_tui_wrapper.tui.prefill import AppPrefill, UpscalePrefill
from ltx_tui_wrapper.upscale import AI_SCALES, NCNN_MODELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-upscale",
        description=(
            "Upscale tab in ltx-tui: scale a video to strict 1920×1080 with "
            "letterbox/pillarbox padding."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Pre-fill input video path (default: last generate output)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Pre-fill output video path",
    )
    parser.add_argument(
        "--model",
        choices=NCNN_MODELS,
        help="Pre-fill realesrgan-ncnn-vulkan model (omit for FFmpeg Lanczos)",
    )
    parser.add_argument(
        "--scale",
        type=int,
        choices=AI_SCALES,
        help="Pre-fill AI upscale factor",
    )
    parser.add_argument(
        "--realesrgan-bin",
        help="Pre-fill path to realesrgan-ncnn-vulkan binary",
    )
    parser.add_argument(
        "--models-dir",
        help="Pre-fill path to realesrgan-ncnn-vulkan models directory",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Pre-fill keep extracted frames after AI upscaling",
    )
    args = parser.parse_args()
    prefill = AppPrefill(
        initial_tab="upscale",
        upscale=UpscalePrefill(
            input=args.input,
            output=args.output,
            model=args.model,
            scale=args.scale,
            realesrgan_bin=args.realesrgan_bin,
            models_dir=args.models_dir,
            keep_frames=args.keep_frames,
        ),
    )

    raise SystemExit(
        run_ltx_tui(prefill=prefill)
    )


if __name__ == "__main__":
    main()
