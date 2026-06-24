"""Embed invocation metadata in generated video files."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from pathlib import Path


METADATA_KEY = "ltx_tui_command"
GENERATE_COMMANDS_METADATA_KEY = "ltx_tui_generate_commands"


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
