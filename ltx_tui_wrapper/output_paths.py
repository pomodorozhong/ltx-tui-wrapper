"""Timestamped output paths for batch runs."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

_TIMESTAMP_SUFFIX = re.compile(r"^\d{8}_\d{6}$")
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}
EXTEND_FROM_EXTENDED_DIR = "extended"
EXTEND_FROM_ORIGINAL_DIR = "original"
EXTEND_FROM_SEGMENTS_DIR = "segments"


def timestamp_suffix(when: datetime | None = None) -> str:
    """Return a filesystem-safe timestamp string."""
    return (when or datetime.now()).strftime("%Y%m%d_%H%M%S")


def timestamped_output_path(output: str, when: datetime | None = None) -> str:
    """Insert a timestamp before the file extension."""
    path = Path(output)
    stamped = f"{path.stem}_{timestamp_suffix(when)}{path.suffix}"
    return str(path.with_name(stamped))


def _batch_timestamped_variants(base_output: Path) -> list[Path]:
    """Return batch-style timestamped files derived from *base_output*."""
    parent = base_output.parent
    if not parent.is_dir():
        return []

    prefix = f"{base_output.stem}_"
    variants: list[Path] = []
    for candidate in parent.iterdir():
        if not candidate.is_file() or candidate.suffix != base_output.suffix:
            continue
        if not candidate.stem.startswith(prefix):
            continue
        if _TIMESTAMP_SUFFIX.fullmatch(candidate.stem[len(prefix) :]):
            variants.append(candidate)
    return variants


def extend_from_base_dir(path: Path) -> Path:
    """Return the directory that holds ``extended/`` and ``original/`` subfolders."""
    path = path.expanduser()
    if path.is_dir():
        return path
    return path.parent


def is_extended_output_video(path: Path) -> bool:
    """Return True when *path* looks like an extend-from output file."""
    return "_extended" in path.stem


def extend_from_output_path(input_video: str) -> str:
    """Return the default extend-from output path under ``extended/``."""
    path = Path(input_video).expanduser()
    extended_dir = extend_from_base_dir(path) / EXTEND_FROM_EXTENDED_DIR
    return str(extended_dir / f"{path.stem}_extended{path.suffix}")


def extend_from_segments_dir(input_video: Path) -> Path:
    """Return the persistent work directory for in-progress extend-from segments."""
    input_video = input_video.expanduser()
    return extend_from_base_dir(input_video) / EXTEND_FROM_SEGMENTS_DIR / input_video.stem


def extended_output_exists(input_video: Path) -> Path | None:
    """Return an existing extended output for *input_video*, if any."""
    input_video = input_video.expanduser()
    extended_dir = extend_from_base_dir(input_video) / EXTEND_FROM_EXTENDED_DIR
    suffix = input_video.suffix
    stem = input_video.stem
    candidates: list[Path] = []

    exact = extended_dir / f"{stem}_extended{suffix}"
    if exact.is_file():
        candidates.append(exact)

    prefix = f"{stem}_extended_"
    if extended_dir.is_dir():
        for candidate in extended_dir.iterdir():
            if not candidate.is_file() or candidate.suffix != suffix:
                continue
            if not candidate.stem.startswith(prefix):
                continue
            suffix_part = candidate.stem[len(prefix) :]
            if _TIMESTAMP_SUFFIX.fullmatch(suffix_part):
                candidates.append(candidate)

    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.stat().st_mtime)


def resolve_extend_from_output_path(
    input_video: str,
    final_output: str | None = None,
    *,
    when: datetime | None = None,
) -> str:
    """Return the default extend-from output path, timestamping only on collision."""
    if final_output:
        path = Path(final_output).expanduser()
        if path.is_file():
            return timestamped_output_path(str(path), when=when)
        return str(path)

    default = Path(extend_from_output_path(input_video))
    if default.is_file():
        return timestamped_output_path(str(default), when=when)
    return str(default)


def archive_extend_from_original(input_video: Path) -> Path:
    """Move *input_video* into the extend-from ``original/`` subfolder."""
    input_video = input_video.expanduser().resolve()
    original_dir = extend_from_base_dir(input_video) / EXTEND_FROM_ORIGINAL_DIR
    if input_video.parent == original_dir:
        return input_video

    original_dir.mkdir(parents=True, exist_ok=True)
    dest = original_dir / input_video.name
    if dest.resolve() == input_video:
        return dest
    if dest.is_file():
        return dest

    shutil.move(str(input_video), str(dest))
    return dest


def discover_extend_from_inputs(path: Path) -> list[Path]:
    """Return video files to extend from a file or directory *path*."""
    path = path.expanduser()
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise SystemExit(f"Input path not found: {path}")

    videos: list[Path] = []
    for candidate in sorted(path.iterdir(), key=lambda item: item.name):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in _VIDEO_EXTENSIONS:
            continue
        if is_extended_output_video(candidate):
            continue
        videos.append(candidate)

    if not videos:
        raise SystemExit(f"No candidate videos found in {path}")
    return videos


def latest_output_path(base_output: str) -> str:
    """Return the newest on-disk output derived from a generate output path.

    Batch runs stamp outputs as ``<stem>_YYYYMMDD_HHMMSS<suffix>``. When several
    candidates exist (including the unstamped base file), the newest by mtime wins.
    """
    path = Path(base_output).expanduser()
    candidates = _batch_timestamped_variants(path)
    if path.is_file():
        candidates.append(path)
    if not candidates:
        return str(path)
    return str(max(candidates, key=lambda candidate: candidate.stat().st_mtime))
