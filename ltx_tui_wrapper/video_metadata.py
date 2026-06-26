"""Embed invocation metadata in generated video files."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from pathlib import Path


METADATA_KEY = "ltx_tui_command"
GENERATE_COMMANDS_METADATA_KEY = "ltx_tui_generate_commands"
EXTEND_PROGRAMS = frozenset({"ltx-tui-extend", "ltx-tui-extend-from"})
DEFAULT_UPSCALE_MODEL = "realesrgan-x4plus"


def current_invocation() -> list[str]:
    """Return the current process argv with a short program name."""
    program = Path(sys.argv[0]).name if sys.argv else "unknown"
    return [program, *sys.argv[1:]]


def invocation_with_output(invocation: list[str], output_path: Path) -> list[str]:
    """Return *invocation* with its output flag set to *output_path*."""
    result = list(invocation)
    for flag in ("-o", "--output"):
        if flag in result:
            idx = result.index(flag)
            result[idx + 1] = str(output_path)
            return result
    result.extend(["-o", str(output_path)])
    return result


def format_generate_commands(commands: list[list[str]]) -> str:
    """Return newline-separated shell commands for segment generate runs."""
    return "\n".join(shlex.join(command) for command in commands)


def write_command_metadata(path: Path, command: list[str]) -> None:
    """Store *command* in *path* container metadata (in-place via temp file)."""
    write_metadata(path, {METADATA_KEY: shlex.join(command)})


def _use_metadata_tags(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".m4v", ".mov"}


def write_metadata(path: Path, tags: dict[str, str]) -> None:
    """Store *tags* in *path* container metadata (in-place via temp file)."""
    if not path.is_file() or not tags:
        return

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print(
            "ffmpeg not found; could not embed command metadata "
            f"in {path}.",
            file=sys.stderr,
        )
        return

    temp_path = path.with_suffix(f".meta{path.suffix}")
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(path),
        "-c",
        "copy",
    ]
    if _use_metadata_tags(temp_path):
        command.extend(["-movflags", "use_metadata_tags"])
    for key, value in tags.items():
        command.extend(["-metadata", f"{key}={value}"])
    command.append(str(temp_path))

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not temp_path.is_file():
            detail = result.stderr.strip() or result.stdout.strip()
            print(
                f"Could not embed command metadata in {path}"
                + (f": {detail}" if detail else "."),
                file=sys.stderr,
            )
            return
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def read_metadata(path: Path) -> dict[str, str]:
    """Return ffprobe format tags for *path*."""
    if not path.is_file():
        return {}
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return {}
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format_tags",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    try:
        import json

        payload = json.loads(result.stdout or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    tags = payload.get("format", {}).get("tags", {})
    if not isinstance(tags, dict):
        return {}
    return {str(key): str(value) for key, value in tags.items()}


def read_command_metadata(path: Path) -> str | None:
    """Read the stored command metadata value from *path*, if present."""
    tags = read_metadata(path)
    value = tags.get(METADATA_KEY)
    if not value:
        return None
    return value


def format_duration_for_invocation(seconds: float) -> str:
    """Format a duration in seconds for ``-l`` metadata."""
    if seconds == int(seconds):
        return str(int(seconds))
    return f"{seconds:g}s"


def _argv_flag_value(argv: list[str], *flags: str) -> str | None:
    for flag in flags:
        if flag in argv:
            index = argv.index(flag)
            if index + 1 < len(argv):
                return argv[index + 1]
    return None


def upscale_enabled_in_argv(argv: list[str]) -> bool:
    """Return whether *argv* enables AI upscale between extend segments."""
    if "--no-upscale" in argv:
        return False
    return "--upscale" in argv


def parse_upscale_from_argv(argv: list[str]) -> dict[str, object]:
    """Return upscale settings encoded in an extend / extend-from argv."""
    return {
        "enabled": upscale_enabled_in_argv(argv),
        "model": _argv_flag_value(argv, "--upscale-model") or DEFAULT_UPSCALE_MODEL,
        "scale": _optional_int(_argv_flag_value(argv, "--upscale-scale")),
    }


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def format_upscale_summary(argv: list[str]) -> str | None:
    """Return a readable AI-upscale summary for extend / extend-from commands."""
    if not argv or argv[0] not in EXTEND_PROGRAMS:
        return None

    settings = parse_upscale_from_argv(argv)
    if not settings["enabled"]:
        return "AI upscale between segments: no"

    lines = ["AI upscale between segments: yes", f"model: {settings['model']}"]
    if settings["scale"] is not None:
        lines.append(f"scale: {settings['scale']}")
    return "\n".join(lines)


def _append_upscale_invocation_args(
    argv: list[str],
    *,
    upscale: bool,
    upscale_model: str,
    upscale_scale: int | None,
    realesrgan_bin: str | None,
    models_dir: str | None,
) -> None:
    if upscale:
        argv.append("--upscale")
    if upscale_model != DEFAULT_UPSCALE_MODEL:
        argv.extend(["--upscale-model", upscale_model])
    if upscale_scale is not None:
        argv.extend(["--upscale-scale", str(upscale_scale)])
    if realesrgan_bin:
        argv.extend(["--realesrgan-bin", realesrgan_bin])
    if models_dir:
        argv.extend(["--models-dir", models_dir])


def build_extend_invocation_argv(
    *,
    target_duration: float,
    output_path: Path,
    max_retries: int = 1,
    timestamp: bool = True,
    keep_segments: bool = False,
    upscale: bool = False,
    upscale_model: str = DEFAULT_UPSCALE_MODEL,
    upscale_scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
) -> list[str]:
    """Build the ``ltx-tui-extend`` argv stored in extended video metadata."""
    argv = ["ltx-tui-extend", "-l", format_duration_for_invocation(target_duration)]
    if max_retries != 1:
        argv.extend(["-r", str(max_retries)])
    if not timestamp:
        argv.append("--no-timestamp")
    if keep_segments:
        argv.append("--keep-segments")
    _append_upscale_invocation_args(
        argv,
        upscale=upscale,
        upscale_model=upscale_model,
        upscale_scale=upscale_scale,
        realesrgan_bin=realesrgan_bin,
        models_dir=models_dir,
    )
    argv.extend(["-o", str(output_path)])
    return argv


def build_extend_from_invocation_argv(
    *,
    input_video: Path,
    target_duration: float,
    output_path: Path,
    max_retries: int = 1,
    keep_segments: bool = False,
    upscale: bool = False,
    upscale_model: str = DEFAULT_UPSCALE_MODEL,
    upscale_scale: int | None = None,
    realesrgan_bin: str | None = None,
    models_dir: str | None = None,
    frames: int | None = None,
    regenerate_base: bool = False,
    random_seed: bool = False,
) -> list[str]:
    """Build the ``ltx-tui-extend-from`` argv stored in extended video metadata."""
    argv = [
        "ltx-tui-extend-from",
        "-i",
        str(input_video),
        "-l",
        format_duration_for_invocation(target_duration),
    ]
    if max_retries != 1:
        argv.extend(["-r", str(max_retries)])
    if keep_segments:
        argv.append("--keep-segments")
    if frames is not None:
        argv.extend(["--frames", str(frames)])
    if regenerate_base:
        argv.append("--regenerate-base")
    if random_seed:
        argv.append("--random-seed")
    _append_upscale_invocation_args(
        argv,
        upscale=upscale,
        upscale_model=upscale_model,
        upscale_scale=upscale_scale,
        realesrgan_bin=realesrgan_bin,
        models_dir=models_dir,
    )
    argv.extend(["-o", str(output_path)])
    return argv


def format_argv_readable(argv: list[str]) -> str:
    """Format an argv as one ``argument: value`` pair per line."""
    if not argv:
        return ""

    lines: list[str] = []
    index = 0

    lines.append(f"program: {argv[index]}")
    index += 1

    if index < len(argv) and not argv[index].startswith("-"):
        lines.append(f"command: {argv[index]}")
        index += 1

    while index < len(argv):
        argument = argv[index]
        if argument.startswith("-"):
            index += 1
            values: list[str] = []
            while index < len(argv) and not argv[index].startswith("-"):
                values.append(argv[index])
                index += 1
            if values:
                lines.append(f"{argument}: {' '.join(values)}")
            else:
                lines.append(argument)
            continue

        lines.append(f"arg: {argument}")
        index += 1

    return "\n".join(lines)


def format_command_string_readable(command: str) -> str:
    """Format a shell-quoted command string for display."""
    try:
        argv = shlex.split(command)
    except ValueError:
        return command
    if not argv:
        return command
    return format_argv_readable(argv)


def format_stored_commands(path: Path) -> str:
    """Return a human-readable summary of ltx-tui commands stored in *path* metadata."""
    if not path.is_file():
        return f"File not found: {path}"

    tags = read_metadata(path)
    if not tags:
        return (
            "No metadata tags found in this file "
            "(or ffprobe is unavailable)."
        )

    command = tags.get(METADATA_KEY)
    if not command:
        return "No ltx-tui command metadata found in this file."

    lines: list[str] = []
    try:
        argv = shlex.split(command)
    except ValueError:
        argv = []

    upscale_summary = format_upscale_summary(argv) if argv else None
    if upscale_summary:
        lines.extend((upscale_summary, ""))

    lines.append(format_command_string_readable(command))
    segments = tags.get(GENERATE_COMMANDS_METADATA_KEY)
    if segments:
        lines.append("")
        lines.append("Segment generate commands:")
        for index, segment_command in enumerate(segments.splitlines(), start=1):
            segment_command = segment_command.strip()
            if not segment_command:
                continue
            lines.extend(
                (
                    "",
                    f"--- Segment {index} ---",
                    format_command_string_readable(segment_command),
                )
            )
    return "\n".join(lines)
