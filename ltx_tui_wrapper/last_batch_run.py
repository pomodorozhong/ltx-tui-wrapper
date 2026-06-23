"""Persist and restore the last batch tab settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LAST_BATCH_RUN_PATH = Path.home() / ".config" / "ltx-tui" / "last_batch.json"


@dataclass(frozen=True)
class BatchRunSettings:
    count: int
    continue_on_error: bool


def save_last_batch_run(*, count: int, continue_on_error: bool) -> None:
    """Write batch tab settings to the user's config directory."""
    LAST_BATCH_RUN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"count": count, "continue_on_error": continue_on_error}
    LAST_BATCH_RUN_PATH.write_text(json.dumps(data, indent=2) + "\n")


def load_last_batch_run() -> BatchRunSettings | None:
    """Load the most recently saved batch settings, if any."""
    if not LAST_BATCH_RUN_PATH.is_file():
        return None
    try:
        data = json.loads(LAST_BATCH_RUN_PATH.read_text())
        return BatchRunSettings(
            count=int(data["count"]),
            continue_on_error=bool(data["continue_on_error"]),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
