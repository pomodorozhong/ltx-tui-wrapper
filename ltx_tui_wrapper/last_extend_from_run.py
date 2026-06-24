"""Persist and restore the last extend-from tab settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LAST_EXTEND_FROM_RUN_PATH = Path.home() / ".config" / "ltx-tui" / "last_extend_from.json"


@dataclass(frozen=True)
class ExtendFromRunSettings:
    input_path: str
    target_duration_text: str
    max_retries: int
    final_output: str | None
    keep_segments: bool
    continue_on_error: bool
    upscale: bool
    upscale_model: str
    upscale_scale: int | None
    realesrgan_bin: str | None
    models_dir: str | None


def save_last_extend_from_run(
    *,
    input_path: str,
    target_duration_text: str,
    max_retries: int,
    final_output: str | None,
    keep_segments: bool,
    continue_on_error: bool,
    upscale: bool,
    upscale_model: str,
    upscale_scale: int | None,
    realesrgan_bin: str | None,
    models_dir: str | None,
) -> None:
    """Write extend-from tab settings to the user's config directory."""
    LAST_EXTEND_FROM_RUN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "input_path": input_path,
        "target_duration_text": target_duration_text,
        "max_retries": max_retries,
        "final_output": final_output,
        "keep_segments": keep_segments,
        "continue_on_error": continue_on_error,
        "upscale": upscale,
        "upscale_model": upscale_model,
        "upscale_scale": upscale_scale,
        "realesrgan_bin": realesrgan_bin,
        "models_dir": models_dir,
    }
    LAST_EXTEND_FROM_RUN_PATH.write_text(json.dumps(data, indent=2) + "\n")


def load_last_extend_from_run() -> ExtendFromRunSettings | None:
    """Load the most recently saved extend-from settings, if any."""
    if not LAST_EXTEND_FROM_RUN_PATH.is_file():
        return None
    try:
        data = json.loads(LAST_EXTEND_FROM_RUN_PATH.read_text())
        return ExtendFromRunSettings(
            input_path=str(data["input_path"]),
            target_duration_text=str(data["target_duration_text"]),
            max_retries=int(data.get("max_retries", 1)),
            final_output=_optional_str(data.get("final_output")),
            keep_segments=bool(data.get("keep_segments", False)),
            continue_on_error=bool(data.get("continue_on_error", False)),
            upscale=bool(data.get("upscale", False)),
            upscale_model=str(data.get("upscale_model", "realesrgan-x4plus")),
            upscale_scale=_optional_int(data.get("upscale_scale")),
            realesrgan_bin=_optional_str(data.get("realesrgan_bin")),
            models_dir=_optional_str(data.get("models_dir")),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
