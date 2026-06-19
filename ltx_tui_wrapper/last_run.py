"""Persist and restore the last generate run options."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ltx_tui_wrapper.options import GenerateOptions

LAST_RUN_PATH = Path.home() / ".config" / "ltx-tui" / "last_generate.json"


def save_last_run(options: GenerateOptions) -> None:
    """Write *options* to the user's config directory."""
    LAST_RUN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(options)
    data["image_specs"] = list(options.image_specs)
    data["lora_specs"] = list(options.lora_specs)
    LAST_RUN_PATH.write_text(json.dumps(data, indent=2) + "\n")


def load_last_run() -> GenerateOptions | None:
    """Load the most recently saved generate options, if any."""
    if not LAST_RUN_PATH.is_file():
        return None
    try:
        data = json.loads(LAST_RUN_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return GenerateOptions(
            prompt=data["prompt"],
            output=data["output"],
            frame_rate=float(data["frame_rate"]),
            pipeline_mode=data["pipeline_mode"],
            model=data.get("model", "dgrauet/ltx-2.3-mlx-q8"),
            gemma=data.get("gemma", "mlx-community/gemma-3-12b-it-4bit"),
            seed=int(data.get("seed", -1)),
            quiet=bool(data.get("quiet", False)),
            height=int(data.get("height", 480)),
            width=int(data.get("width", 704)),
            frames=int(data.get("frames", 97)),
            tile_frames=int(data.get("tile_frames", 1)),
            tile_spatial=int(data.get("tile_spatial", 1)),
            tile_overlap=int(data.get("tile_overlap", 2)),
            low_ram=bool(data.get("low_ram", False)),
            image_specs=tuple(data.get("image_specs", ())),
            lora_specs=tuple(data.get("lora_specs", ())),
            steps=_optional_int(data.get("steps")),
            stage1_steps=_optional_int(data.get("stage1_steps")),
            stage2_steps=_optional_int(data.get("stage2_steps")),
            cfg_scale=_optional_float(data.get("cfg_scale")),
            stg_scale=_optional_float(data.get("stg_scale")),
            dev_transformer=data.get("dev_transformer", "transformer-dev.safetensors"),
            distilled_lora=data.get(
                "distilled_lora", "ltx-2.3-22b-distilled-lora-384.safetensors"
            ),
            distilled_lora_strength=float(data.get("distilled_lora_strength", 1.0)),
            enable_teacache=bool(data.get("enable_teacache", False)),
            teacache_thresh=_optional_float(data.get("teacache_thresh")),
            enhance_prompt=bool(data.get("enhance_prompt", False)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
