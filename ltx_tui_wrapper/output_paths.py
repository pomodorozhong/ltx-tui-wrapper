"""Timestamped output paths for batch runs."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_TIMESTAMP_SUFFIX = re.compile(r"^\d{8}_\d{6}$")
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


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


def is_extended_output_video(path: Path) -> bool:
    """Return True when *path* looks like an extend-from output file."""
    return "_extended" in path.stem


def extended_output_exists(input_video: Path) -> Path | None:
    """Return an existing extended output for *input_video*, if any."""
    input_video = input_video.expanduser()
    parent = input_video.parent
    suffix = input_video.suffix
    stem = input_video.stem
    candidates: list[Path] = []

    exact = parent / f"{stem}_extended{suffix}"
    if exact.is_file():
        candidates.append(exact)

    prefix = f"{stem}_extended_"
    if parent.is_dir():
        for candidate in parent.iterdir():
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

    path = Path(input_video).expanduser()
    default = path.with_name(f"{path.stem}_extended{path.suffix}")
    if default.is_file():
        return timestamped_output_path(str(default), when=when)
    return str(default)


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
