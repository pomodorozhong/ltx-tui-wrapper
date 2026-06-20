"""CLI for upscaling a video to 1920×1080 with FFmpeg Lanczos."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.upscale import upscale_video


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ltx-tui-upscale",
        description=(
            "Upscale a video to strict 1920×1080 using FFmpeg Lanczos scaling "
            "with letterbox/pillarbox padding to 16:9."
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
    args = parser.parse_args()

    raise SystemExit(
        upscale_video(
            input_path=args.input,
            output_path=args.output,
        )
    )


if __name__ == "__main__":
    main()
