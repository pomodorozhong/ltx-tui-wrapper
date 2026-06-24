"""Timestamped output paths for batch runs."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_TIMESTAMP_SUFFIX = re.compile(r"^\d{8}_\d{6}$")


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
