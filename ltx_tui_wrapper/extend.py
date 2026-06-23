"""Extend a generated video by chaining I2V runs from each segment's last frame."""

from __future__ import annotations

import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from ltx_tui_wrapper.batch_cli import format_elapsed
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.output_paths import timestamped_output_path
from ltx_tui_wrapper.parsing import build_command_argv, format_command
from ltx_tui_wrapper.progress import print_failure, print_status_band
from ltx_tui_wrapper.runner import execute_command, prevent_sleep
from ltx_tui_wrapper.upscale import upscale_image

_DURATION_RE = re.compile(
    r"^(?:(?P<minutes>\d+(?:\.\d+)?)m)?(?:(?P<seconds>\d+(?:\.\d+)?)s?)?$",
    re.IGNORECASE,
)


def parse_target_duration(value: str) -> float:
    """Parse a duration string such as ``60``, ``90s``, or ``1.5m`` into seconds."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("duration must not be empty")

    if stripped.isdigit() or (
        stripped.count(".") == 1 and stripped.replace(".", "", 1).isdigit()
    ):
        seconds = float(stripped)
    else:
        match = _DURATION_RE.fullmatch(stripped)
        if match is None:
            raise ValueError(
                f"invalid duration {value!r}; use seconds (60), 90s, or 1.5m"
            )
        minutes = float(match.group("minutes") or 0)
        seconds = float(match.group("seconds") or 0)
        seconds = minutes * 60 + seconds

    if seconds <= 0:
        raise ValueError("duration must be positive")
    return seconds


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"{name} is required but was not found on PATH.")
    return path


def probe_video_duration(path: Path) -> float:
    """Return the duration of *path* in seconds via ffprobe."""
    _require_tool("ffprobe")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed for {path}: {result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"could not parse duration for {path}") from exc
    if duration <= 0:
        raise RuntimeError(f"invalid duration for {path}: {duration}")
    return duration


def extract_last_frame(video: Path, frame_path: Path) -> None:
    """Write the last video frame to *frame_path* using ffmpeg."""
    _require_tool("ffmpeg")
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-sseof",
            "-3",
            "-i",
            str(video),
            "-update",
            "1",
            "-q:v",
            "1",
            str(frame_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not frame_path.is_file():
        raise RuntimeError(
            f"ffmpeg failed to extract last frame from {video}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def concat_videos(segments: list[Path], output: Path) -> None:
    """Concatenate *segments* into a single *output* file."""
    _require_tool("ffmpeg")
    if not segments:
        raise ValueError("no segments to concatenate")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
    ) as list_file:
        for segment in segments:
            escaped = str(segment.resolve()).replace("'", r"'\''")
            list_file.write(f"file '{escaped}'\n")
        list_path = Path(list_file.name)

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        list_path.unlink(missing_ok=True)

    if result.returncode != 0 or not output.is_file():
        raise RuntimeError(
            f"ffmpeg concat failed: {result.stderr.strip() or result.stdout.strip()}"
        )


def extended_output_path(base_output: str) -> str:
    """Return the default path for the concatenated extended video."""
    path = Path(base_output)
    return str(path.with_name(f"{path.stem}_extended{path.suffix}"))


def resolve_final_output_path(
    base_output: str,
    final_output: str | None,
    *,
    timestamp: bool,
) -> str:
    """Return the path for the concatenated extended video."""
    path = final_output or extended_output_path(base_output)
    if timestamp:
        path = timestamped_output_path(path)
    return path


def run_with_retries(
    argv: list[str],
    *,
    max_retries: int,
    label: str,
) -> tuple[int, float]:
    """Run *argv*, retrying up to *max_retries* times on non-zero exit."""
    attempts = max(1, max_retries)
    exit_code = 1
    elapsed = 0.0
    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        exit_code = execute_command(argv, echo=False)
        elapsed = time.perf_counter() - started
        if exit_code == 0:
            return 0, elapsed
        if attempt < attempts:
            print_status_band(
                f"{label} failed with exit code {exit_code} "
                f"after {format_elapsed(elapsed)}; "
                f"retrying ({attempt}/{attempts})…",
                success=False,
            )
    return exit_code, elapsed


def extend_video(
    *,
    target_duration: float,
    max_retries: int,
    final_output: str | None = None,
    timestamp: bool = True,
    keep_segments: bool = False,
    upscale: bool = False,
    upscale_model: str = "realesrgan-x4plus",
    upscale_scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
) -> int:
    """Chain last-run generations until total duration exceeds *target_duration*."""
    base_options = load_last_run()
    if base_options is None:
        raise SystemExit(
            "No saved generate settings found. Run `ltx-tui` once and press Run first."
        )

    if base_options.seed == -1:
        base_options = replace(
            base_options,
            seed=random.randint(0, 2**31 - 1),
        )

    _require_tool("ffmpeg")
    _require_tool("ffprobe")

    segments: list[Path] = []
    total_duration = 0.0
    segment_index = 0
    current_options: GenerateOptions = base_options
    work_dir = Path(tempfile.mkdtemp(prefix="ltx-tui-extend-"))
    extend_started = time.perf_counter()

    print(
        f"Extending video to > {target_duration:.1f}s "
        f"(retry up to {max_retries} time(s) per segment, seed {base_options.seed}).",
        flush=True,
    )
    print(f"Working directory: {work_dir}", flush=True)

    try:
        with prevent_sleep():
            while total_duration < target_duration:
                segment_index += 1
                run_options = replace(
                    current_options,
                    output=timestamped_output_path(base_options.output),
                )
                if segment_index > 1:
                    run_options = replace(
                        run_options,
                        image_specs=(str(frame_path),),
                    )

                argv = build_command_argv(run_options)
                label = f"Segment {segment_index}"
                print(f"[{label}] {format_command(run_options)}", flush=True)
                exit_code, elapsed = run_with_retries(
                    argv,
                    max_retries=max_retries,
                    label=label,
                )
                if exit_code != 0:
                    attempts = max(1, max_retries)
                    print_status_band(
                        f"{label} failed with exit code {exit_code} "
                        f"after {format_elapsed(elapsed)} ({attempts} attempt(s)).",
                        success=False,
                    )
                    return exit_code

                segment_path = Path(run_options.output)
                if not segment_path.is_file():
                    print_status_band(
                        f"{label} failed: expected output file missing ({segment_path}).",
                        success=False,
                    )
                    return 1

                segment_duration = probe_video_duration(segment_path)
                segments.append(segment_path)
                total_duration += segment_duration
                print_status_band(
                    f"Segment {segment_index}: {segment_duration:.2f}s "
                    f"(total {total_duration:.2f}s / {target_duration:.1f}s) "
                    f"in {format_elapsed(elapsed)}.",
                    success=True,
                )

                if total_duration >= target_duration:
                    break

                frame_path = work_dir / f"segment_{segment_index:03d}_last.png"
                extract_last_frame(segment_path, frame_path)
                if upscale:
                    upscaled_frame_path = (
                        work_dir / f"segment_{segment_index:03d}_last_upscaled.png"
                    )
                    try:
                        upscale_image(
                            frame_path,
                            upscaled_frame_path,
                            model=upscale_model,
                            scale=upscale_scale,
                            realesrgan_bin=realesrgan_bin,
                            models_dir=models_dir,
                        )
                    except (RuntimeError, ValueError) as exc:
                        print_failure(
                            f"Failed to upscale last frame for segment {segment_index}",
                            details=str(exc),
                        )
                        return 1
                    frame_path = upscaled_frame_path
                current_options = run_options

        if not segments:
            print("No segments were generated.", file=sys.stderr)
            return 1

        out_path = Path(
            resolve_final_output_path(
                base_options.output,
                final_output,
                timestamp=timestamp,
            )
        )
        print(
            f"Concatenating {len(segments)} segment(s) -> {out_path}",
            flush=True,
        )
        concat_videos(segments, out_path)
        final_duration = probe_video_duration(out_path)
        total_elapsed = time.perf_counter() - extend_started
        print(
            f"Extended video ready: {out_path} ({final_duration:.2f}s) "
            f"in {format_elapsed(total_elapsed)}.",
            flush=True,
        )
        return 0
    finally:
        if not keep_segments:
            for segment in segments:
                segment.unlink(missing_ok=True)
            shutil.rmtree(work_dir, ignore_errors=True)


def run_extend_batch(
    *,
    target_duration: float,
    max_retries: int,
    count: int,
    final_output: str | None = None,
    timestamp: bool = True,
    keep_segments: bool = False,
    continue_on_error: bool = False,
    upscale: bool = False,
    upscale_model: str = "realesrgan-x4plus",
    upscale_scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
) -> int:
    """Run :func:`extend_video` *count* times, optionally with timestamped outputs."""
    if count < 1:
        raise SystemExit("count must be at least 1")

    if count == 1:
        return extend_video(
            target_duration=target_duration,
            max_retries=max_retries,
            final_output=final_output,
            timestamp=timestamp,
            keep_segments=keep_segments,
            upscale=upscale,
            upscale_model=upscale_model,
            upscale_scale=upscale_scale,
            realesrgan_bin=realesrgan_bin,
            models_dir=models_dir,
        )

    base_options = load_last_run()
    if base_options is None:
        raise SystemExit(
            "No saved generate settings found. Run `ltx-tui` once and press Run first."
        )

    failures = 0
    batch_started = time.perf_counter()
    with prevent_sleep():
        for index in range(1, count + 1):
            run_output = resolve_final_output_path(
                base_options.output,
                final_output,
                timestamp=timestamp,
            )
            print(
                f"[{index}/{count}] Extending to > {target_duration:.1f}s -> {run_output}",
                flush=True,
            )
            exit_code = extend_video(
                target_duration=target_duration,
                max_retries=max_retries,
                final_output=run_output,
                timestamp=False,
                keep_segments=keep_segments,
                upscale=upscale,
                upscale_model=upscale_model,
                upscale_scale=upscale_scale,
                realesrgan_bin=realesrgan_bin,
                models_dir=models_dir,
            )
            if exit_code != 0:
                failures += 1
                print(
                    f"Extend run {index} failed with exit code {exit_code}.",
                    file=sys.stderr,
                )
                if not continue_on_error:
                    return exit_code

    total_elapsed = time.perf_counter() - batch_started
    succeeded = count - failures
    print(
        f"Batch complete: {succeeded}/{count} succeeded in "
        f"{format_elapsed(total_elapsed)}.",
        flush=True,
    )
    if failures:
        return 1
    return 0
