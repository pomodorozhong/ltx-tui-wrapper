"""CLI for extending from an existing generated video."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.tui.app import run_ltx_tui
from ltx_tui_wrapper.tui.prefill import AppPrefill, ExtendFromPrefill
from ltx_tui_wrapper.upscale import AI_SCALES, NCNN_MODELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-extend-from",
        description=(
            "Extend From tab in ltx-tui: continue from an existing generated video or "
            "folder of videos by reading embedded metadata and chaining new segments. "
            "Re-running a folder skips videos that already have extended outputs. "
            "Interrupted segment generation resumes from segments/<stem>/."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Pre-fill input video or folder path (must include ltx-tui metadata)",
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
        help="Pre-fill path for the final concatenated video (single input only)",
    )
    parser.add_argument(
        "--keep-segments",
        action="store_true",
        help="Pre-fill keep segment files",
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
    parser.add_argument(
        "-f",
        "--frames",
        type=int,
        metavar="N",
        help="Pre-fill frame count override for new segments",
    )
    parser.add_argument(
        "--regenerate-base",
        action="store_true",
        help="Pre-fill regenerate base segment from input last frame",
    )
    parser.add_argument(
        "--random-seed",
        action="store_true",
        help="Pre-fill use one random seed for all new segments",
    )
    args = parser.parse_args()
    prefill = AppPrefill(
        initial_tab="extend_from",
        extend_from=ExtendFromPrefill(
            input_path=args.input,
            length=args.length,
            retries=args.retries,
            output=args.output,
            keep_segments=args.keep_segments,
            continue_on_error=args.continue_on_error,
            upscale=args.upscale,
            upscale_model=args.upscale_model,
            upscale_scale=args.upscale_scale,
            realesrgan_bin=args.realesrgan_bin,
            models_dir=args.models_dir,
            frames=args.frames,
            regenerate_base=args.regenerate_base,
            random_seed=args.random_seed,
        ),
    )
    raise SystemExit(run_ltx_tui(prefill=prefill))


if __name__ == "__main__":
    main()
