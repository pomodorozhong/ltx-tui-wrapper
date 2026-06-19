"""Timestamped output paths for batch runs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def timestamp_suffix(when: datetime | None = None) -> str:
    """Return a filesystem-safe timestamp string."""
    return (when or datetime.now()).strftime("%Y%m%d_%H%M%S")


def timestamped_output_path(output: str, when: datetime | None = None) -> str:
    """Insert a timestamp before the file extension."""
    path = Path(output)
    stamped = f"{path.stem}_{timestamp_suffix(when)}{path.suffix}"
    return str(path.with_name(stamped))
