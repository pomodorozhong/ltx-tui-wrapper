"""CLI for extending the last generated video by chaining I2V segments."""

from __future__ import annotations

import argparse

from ltx_tui_wrapper.extend import extend_video, parse_target_duration


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
        help="Path for the final concatenated video (default: <last-output>_extended.mp4)",
    )
    parser.add_argument(
        "--keep-segments",
        action="store_true",
        help="Keep individual segment videos and extracted frames after completion",
    )
    args = parser.parse_args()

    if args.retries < 1:
        raise SystemExit("retries must be at least 1")

    try:
        target_duration = parse_target_duration(args.length)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    raise SystemExit(
        extend_video(
            target_duration=target_duration,
            max_retries=args.retries,
            final_output=args.output,
            keep_segments=args.keep_segments,
        )
    )


if __name__ == "__main__":
    main()
