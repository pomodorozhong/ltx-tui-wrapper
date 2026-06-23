"""CLI for upscaling a video to 1920×1080."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.upscale import AI_SCALES, NCNN_MODELS, upscale_video


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-upscale",
        description=(
            "Upscale a video to strict 1920×1080 with letterbox/pillarbox padding to 16:9. "
            "Uses FFmpeg Lanczos by default, or realesrgan-ncnn-vulkan when --model is set."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Input video path (default: last ltx-tui generate output)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output video path (default: <input-stem>_1080p.mp4)",
    )
    parser.add_argument(
        "--model",
        choices=NCNN_MODELS,
        help=(
            "Run realesrgan-ncnn-vulkan with this model instead of FFmpeg Lanczos "
            f"(choices: {', '.join(NCNN_MODELS)})"
        ),
    )
    parser.add_argument(
        "--scale",
        type=int,
        choices=AI_SCALES,
        help="AI upscale factor for realesrgan-ncnn-vulkan (default: auto from source size)",
    )
    parser.add_argument(
        "--realesrgan-bin",
        help="Path to realesrgan-ncnn-vulkan binary (default: find on PATH)",
    )
    parser.add_argument(
        "--models-dir",
        help="Path to realesrgan-ncnn-vulkan models directory (passed as -m)",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Keep extracted and upscaled frame directories after AI upscaling",
    )
    args = parser.parse_args()

    raise SystemExit(
        upscale_video(
            input_path=args.input,
            output_path=args.output,
            model=args.model,
            scale=args.scale,
            realesrgan_bin=args.realesrgan_bin,
            models_dir=args.models_dir,
            keep_frames=args.keep_frames,
        )
    )


if __name__ == "__main__":
    main()
