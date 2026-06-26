"""Structured prefill values for the TUI app."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ltx_tui_wrapper.tui.tab_registry import TabId


@dataclass(frozen=True)
class GeneratePrefill:
    prompt: str | None = None
    output: Path | None = None
    image: Path | None = None


@dataclass(frozen=True)
class BatchPrefill:
    count: int | None = None
    retries: int | None = None
    continue_on_error: bool | None = None


@dataclass(frozen=True)
class ExtendPrefill:
    length: str | None = None
    retries: int | None = None
    count: int | None = None
    output: str | None = None
    timestamp: bool | None = None
    keep_segments: bool | None = None
    continue_on_error: bool | None = None
    upscale: bool | None = None
    upscale_model: str | None = None
    upscale_scale: int | None = None
    realesrgan_bin: str | None = None
    models_dir: str | None = None


@dataclass(frozen=True)
class ExtendFromPrefill:
    input_path: str | None = None
    length: str | None = None
    retries: int | None = None
    output: str | None = None
    keep_segments: bool | None = None
    continue_on_error: bool | None = None
    upscale: bool | None = None
    upscale_model: str | None = None
    upscale_scale: int | None = None
    realesrgan_bin: str | None = None
    models_dir: str | None = None
    frames: int | None = None
    regenerate_base: bool | None = None
    random_seed: bool | None = None


@dataclass(frozen=True)
class UpscalePrefill:
    input: str | None = None
    output: str | None = None
    model: str | None = None
    scale: int | None = None
    realesrgan_bin: str | None = None
    models_dir: str | None = None
    keep_frames: bool | None = None


@dataclass(frozen=True)
class AppPrefill:
    initial_tab: TabId = "generate"
    generate: GeneratePrefill = field(default_factory=GeneratePrefill)
    batch: BatchPrefill = field(default_factory=BatchPrefill)
    extend: ExtendPrefill = field(default_factory=ExtendPrefill)
    extend_from: ExtendFromPrefill = field(default_factory=ExtendFromPrefill)
    upscale: UpscalePrefill = field(default_factory=UpscalePrefill)
