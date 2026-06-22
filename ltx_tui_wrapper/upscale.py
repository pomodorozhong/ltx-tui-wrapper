"""Upscale a video to 1920×1080 using FFmpeg or realesrgan-ncnn-vulkan."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from ltx_tui_wrapper.batch_cli import format_elapsed
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.progress import print_failure, print_status_band
from ltx_tui_wrapper.runner import prevent_sleep

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

NCNN_MODELS = (
    "realesrgan-x4plus",
    "realesr-animevideov3",
    "realesrgan-x4plus-anime",
    "realesrnet-x4plus",
)

AI_SCALES = (2, 3, 4)


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    has_audio: bool
    duration: float


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"{name} is required but was not found on PATH.")
    return path


def _parse_fps(value: str) -> float:
    stripped = value.strip()
    if not stripped or stripped == "0/0":
        raise ValueError(f"invalid frame rate {value!r}")
    return float(Fraction(stripped))


def probe_video_info(path: Path) -> VideoInfo:
    """Return video stream metadata for *path* via ffprobe."""
    _require_tool("ffprobe")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1",
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

    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value

    try:
        width = int(fields["width"])
        height = int(fields["height"])
        fps = _parse_fps(fields["r_frame_rate"])
        duration = float(fields["duration"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"could not parse video info for {path}") from exc

    if width <= 0 or height <= 0 or duration <= 0:
        raise RuntimeError(f"invalid video info for {path}")

    audio_result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    has_audio = audio_result.returncode == 0 and bool(audio_result.stdout.strip())

    return VideoInfo(
        width=width,
        height=height,
        fps=fps,
        has_audio=has_audio,
        duration=duration,
    )


def build_scale_filter(target_width: int, target_height: int) -> str:
    """Return an FFmpeg filter chain that fits content into *target_width*×*target_height*."""
    return (
        f"scale={target_width}:{target_height}:"
        "force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black"
    )


def build_1080p_filter() -> str:
    """Return the FFmpeg filter chain for strict 1920×1080 output."""
    return build_scale_filter(TARGET_WIDTH, TARGET_HEIGHT)


def probe_image_size(path: Path) -> tuple[int, int]:
    """Return ``(width, height)`` for an image file via ffprobe."""
    _require_tool("ffprobe")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "default=noprint_wrappers=1",
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

    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value

    try:
        width = int(fields["width"])
        height = int(fields["height"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"could not parse image size for {path}") from exc

    if width <= 0 or height <= 0:
        raise RuntimeError(f"invalid image size for {path}: {width}×{height}")
    return width, height


def compute_ai_scale(
    width: int,
    height: int,
    *,
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT,
) -> int:
    """Return the smallest ncnn scale factor that exceeds the 1080p target box."""
    for scale in AI_SCALES:
        if width * scale >= target_width and height * scale >= target_height:
            return scale
    return AI_SCALES[-1]


def upscaled_output_path(base_output: str) -> str:
    """Return the default path for the upscaled 1080p video."""
    path = Path(base_output)
    return str(path.with_name(f"{path.stem}_1080p{path.suffix}"))


def _run_ffmpeg_upscale(input_path: Path, output_path: Path, *, has_audio: bool) -> None:
    _require_tool("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        build_1080p_filter(),
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
    ]
    if has_audio:
        command.extend(["-c:a", "copy"])
    else:
        command.append("-an")
    command.append(str(output_path))

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not output_path.is_file():
        raise RuntimeError(
            f"ffmpeg upscale failed: {result.stderr.strip() or result.stdout.strip()}"
        )


def _extract_frames(input_path: Path, frames_dir: Path, *, fps: float) -> None:
    _require_tool("ffmpeg")
    frames_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            f"fps={fps}",
            str(frames_dir / "frame_%08d.png"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg frame extraction failed: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    if not any(frames_dir.glob("frame_*.png")):
        raise RuntimeError(f"ffmpeg extracted no frames from {input_path}")


def _realesrgan_model_stem(model: str, scale: int) -> str:
    if model == "realesr-animevideov3":
        return f"{model}-x{scale}"
    return model


def _resolve_realesrgan_binary(realesrgan_bin: str | None) -> Path:
    path = (
        Path(realesrgan_bin)
        if realesrgan_bin
        else Path(_require_tool("realesrgan-ncnn-vulkan"))
    )
    return path.resolve()


def _resolve_realesrgan_models_dir(
    bin_path: Path,
    *,
    models_dir: str | None,
) -> Path:
    if models_dir is not None:
        return Path(models_dir).expanduser().resolve()
    sibling = (bin_path.parent / "models").resolve()
    if sibling.is_dir():
        return sibling
    cwd_models = (Path.cwd() / "models").resolve()
    if cwd_models.is_dir():
        return cwd_models
    return sibling


def _validate_realesrgan_model(models_dir: Path, *, model: str, scale: int) -> None:
    stem = _realesrgan_model_stem(model, scale)
    param_path = models_dir / f"{stem}.param"
    bin_path = models_dir / f"{stem}.bin"
    missing = [path for path in (param_path, bin_path) if not path.is_file()]
    if not missing:
        return
    missing_list = "\n".join(f"  - {path}" for path in missing)
    raise RuntimeError(
        f"realesrgan-ncnn-vulkan model files not found for {model!r} (scale={scale}x).\n"
        f"Missing:\n{missing_list}\n"
        f"Expected models directory: {models_dir}\n\n"
        "Download the release zip that includes models/ from:\n"
        "  https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0\n"
        "Place the models/ folder next to the realesrgan-ncnn-vulkan binary, "
        "or pass --models-dir."
    )


def _prepare_realesrgan(
    *,
    model: str,
    scale: int,
    realesrgan_bin: str | None,
    models_dir: str | None,
) -> tuple[Path, Path]:
    bin_path = _resolve_realesrgan_binary(realesrgan_bin)
    models_path = _resolve_realesrgan_models_dir(bin_path, models_dir=models_dir)
    _validate_realesrgan_model(models_path, model=model, scale=scale)
    return bin_path, models_path


def _format_subprocess_failure(
    tool: str,
    result: subprocess.CompletedProcess[str],
    *,
    command: list[str] | None = None,
) -> str:
    lines = [f"{tool} exited with code {result.returncode}"]
    if command is not None:
        lines.append(f"command: {' '.join(command)}")
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    if stderr:
        lines.append(f"stderr:\n{stderr}")
    if stdout:
        lines.append(f"stdout:\n{stdout}")
    if not stderr and not stdout:
        lines.append("(no output captured)")
    return "\n".join(lines)


def _run_realesrgan(
    input_path: Path,
    output_path: Path,
    *,
    model: str,
    scale: int,
    realesrgan_bin: Path,
    models_dir: Path,
) -> None:
    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(realesrgan_bin),
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "-n",
        model,
        "-s",
        str(scale),
        "-f",
        "png",
        "-m",
        str(models_dir),
    ]

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            _format_subprocess_failure(
                "realesrgan-ncnn-vulkan",
                result,
                command=command,
            )
        )
    if output_path.is_dir():
        if not any(output_path.glob("*.png")):
            raise RuntimeError("realesrgan-ncnn-vulkan produced no output frames")
    elif not output_path.is_file():
        raise RuntimeError("realesrgan-ncnn-vulkan produced no output image")


def _encode_upscaled_frames(
    upscaled_dir: Path,
    input_path: Path,
    output_path: Path,
    *,
    fps: float,
    has_audio: bool,
) -> None:
    _require_tool("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(upscaled_dir / "frame_%08d.png"),
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-vf",
        build_1080p_filter(),
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
    ]
    if has_audio:
        command.extend(["-map", "1:a:0", "-c:a", "copy"])
    else:
        command.append("-an")
    command.extend(["-shortest", str(output_path)])

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not output_path.is_file():
        raise RuntimeError(
            f"ffmpeg encode failed: {result.stderr.strip() or result.stdout.strip()}"
        )


def upscale_image(
    input_path: Path,
    output_path: Path,
    *,
    model: str = "realesrgan-x4plus",
    scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
) -> None:
    """AI-upscale a single image via realesrgan-ncnn-vulkan."""
    if model not in NCNN_MODELS:
        raise ValueError(
            f"unknown model {model!r}; choose from: {', '.join(NCNN_MODELS)}"
        )
    if scale is not None and scale not in AI_SCALES:
        raise ValueError(f"scale must be one of {', '.join(map(str, AI_SCALES))}")

    if not input_path.is_file():
        raise RuntimeError(f"input image not found: {input_path}")

    width, height = probe_image_size(input_path)
    ai_scale = scale if scale is not None else AI_SCALES[-1]
    bin_path, models_path = _prepare_realesrgan(
        model=model,
        scale=ai_scale,
        realesrgan_bin=realesrgan_bin,
        models_dir=models_dir,
    )

    work_dir = Path(tempfile.mkdtemp(prefix="ltx-tui-upscale-image-"))
    upscaled_path = work_dir / "upscaled.png"

    print(
        f"AI upscale frame: {input_path.name} "
        f"({width}×{height}, model={model}, scale={ai_scale}x)",
        flush=True,
    )

    try:
        _run_realesrgan(
            input_path,
            upscaled_path,
            model=model,
            scale=ai_scale,
            realesrgan_bin=bin_path,
            models_dir=models_path,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(upscaled_path, output_path)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _run_ai_upscale(
    input_path: Path,
    output_path: Path,
    *,
    info: VideoInfo,
    model: str,
    scale: int | None,
    realesrgan_bin: str | None,
    models_dir: str | None,
    keep_frames: bool,
) -> None:
    ai_scale = scale if scale is not None else compute_ai_scale(info.width, info.height)
    bin_path, models_path = _prepare_realesrgan(
        model=model,
        scale=ai_scale,
        realesrgan_bin=realesrgan_bin,
        models_dir=models_dir,
    )

    work_dir = Path(tempfile.mkdtemp(prefix="ltx-tui-upscale-"))
    frames_dir = work_dir / "frames"
    upscaled_dir = work_dir / "upscaled"

    print(
        f"AI upscale: model={model}, scale={ai_scale}x, binary={bin_path}",
        flush=True,
    )

    try:
        print("Extracting frames…", flush=True)
        _extract_frames(input_path, frames_dir, fps=info.fps)

        print("Running realesrgan-ncnn-vulkan…", flush=True)
        _run_realesrgan(
            frames_dir,
            upscaled_dir,
            model=model,
            scale=ai_scale,
            realesrgan_bin=bin_path,
            models_dir=models_path,
        )

        print("Encoding 1080p output…", flush=True)
        _encode_upscaled_frames(
            upscaled_dir,
            input_path,
            output_path,
            fps=info.fps,
            has_audio=info.has_audio,
        )
    finally:
        if not keep_frames:
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(f"Kept frame directories in {work_dir}", flush=True)


def upscale_video(
    *,
    input_path: str | None = None,
    output_path: str | None = None,
    model: str | None = None,
    scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
    keep_frames: bool = False,
) -> int:
    """Upscale *input_path* to strict 1920×1080, preserving aspect ratio with padding."""
    if input_path is None:
        last_run = load_last_run()
        if last_run is None:
            raise SystemExit(
                "No saved generate settings found. Run `ltx-tui` once and press Run first, "
                "or pass `-i`."
            )
        input_path = last_run.output

    if scale is not None and scale not in AI_SCALES:
        raise SystemExit(f"scale must be one of {', '.join(map(str, AI_SCALES))}")

    if model is not None and model not in NCNN_MODELS:
        raise SystemExit(
            f"unknown model {model!r}; choose from: {', '.join(NCNN_MODELS)}"
        )

    in_path = Path(input_path)
    if not in_path.is_file():
        raise SystemExit(f"Input video not found: {in_path}")

    out_path = Path(output_path or upscaled_output_path(str(in_path)))
    if out_path.resolve() == in_path.resolve():
        raise SystemExit("Output path must differ from input path.")

    _require_tool("ffmpeg")
    _require_tool("ffprobe")

    method = f"Real-ESRGAN ({model})" if model is not None else "Lanczos"
    started = time.perf_counter()
    print(
        f"Upscaling {in_path} -> {out_path} ({TARGET_WIDTH}×{TARGET_HEIGHT}, {method}).",
        flush=True,
    )

    try:
        info = probe_video_info(in_path)
    except RuntimeError as exc:
        print_failure("Video probe failed", details=str(exc))
        return 1

    print(
        f"Source: {info.width}×{info.height} @ {info.fps:.3f} fps, "
        f"{info.duration:.2f}s, audio={'yes' if info.has_audio else 'no'}.",
        flush=True,
    )

    try:
        with prevent_sleep():
            if model is None:
                _run_ffmpeg_upscale(in_path, out_path, has_audio=info.has_audio)
            else:
                _run_ai_upscale(
                    in_path,
                    out_path,
                    info=info,
                    model=model,
                    scale=scale,
                    realesrgan_bin=realesrgan_bin,
                    models_dir=models_dir,
                    keep_frames=keep_frames,
                )
    except (RuntimeError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            raise
        print_failure("Upscale failed", details=str(exc))
        return 1

    elapsed = time.perf_counter() - started
    try:
        output_info = probe_video_info(out_path)
    except RuntimeError:
        output_info = None

    if output_info is not None:
        print(
            f"Upscaled video ready: {out_path} "
            f"({output_info.width}×{output_info.height}, {output_info.duration:.2f}s) "
            f"in {format_elapsed(elapsed)}.",
            flush=True,
        )
    else:
        print(
            f"Upscaled video ready: {out_path} in {format_elapsed(elapsed)}.",
            flush=True,
        )

    print_status_band(
        f"Upscaled to {TARGET_WIDTH}×{TARGET_HEIGHT} in {format_elapsed(elapsed)}.",
        success=True,
    )
    return 0
