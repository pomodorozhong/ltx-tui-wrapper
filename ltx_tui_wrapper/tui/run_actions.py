"""Run payloads produced when the user presses Run in the TUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ltx_tui_wrapper.batch_cli import run_batch
from ltx_tui_wrapper.extend import run_extend_batch
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.upscale import upscale_video

TabId = Literal["generate", "batch", "extend", "upscale"]


@dataclass(frozen=True)
class GenerateRun:
    command: list[str]
    options: GenerateOptions


@dataclass(frozen=True)
class BatchRun:
    count: int
    continue_on_error: bool


@dataclass(frozen=True)
class ExtendRun:
    target_duration: float
    max_retries: int
    count: int
    final_output: str | None
    timestamp: bool
    keep_segments: bool
    continue_on_error: bool
    upscale: bool
    upscale_model: str
    upscale_scale: int | None
    realesrgan_bin: str | None
    models_dir: str | None


@dataclass(frozen=True)
class UpscaleRun:
    input_path: str | None
    output_path: str | None
    model: str | None
    scale: int | None
    realesrgan_bin: str | None
    models_dir: str | None
    keep_frames: bool


RunAction = GenerateRun | BatchRun | ExtendRun | UpscaleRun


def execute_run_action(action: RunAction) -> int:
    from ltx_tui_wrapper.runner import execute_command
    from ltx_tui_wrapper.video_metadata import write_command_metadata

    if isinstance(action, GenerateRun):
        exit_code = execute_command(action.command)
        if exit_code == 0:
            write_command_metadata(Path(action.options.output), action.command)
        return exit_code

    if isinstance(action, BatchRun):
        return run_batch(count=action.count, continue_on_error=action.continue_on_error)

    if isinstance(action, ExtendRun):
        return run_extend_batch(
            target_duration=action.target_duration,
            max_retries=action.max_retries,
            count=action.count,
            final_output=action.final_output,
            timestamp=action.timestamp,
            keep_segments=action.keep_segments,
            continue_on_error=action.continue_on_error,
            upscale=action.upscale,
            upscale_model=action.upscale_model,
            upscale_scale=action.upscale_scale,
            realesrgan_bin=action.realesrgan_bin,
            models_dir=action.models_dir,
        )

    return upscale_video(
        input_path=action.input_path,
        output_path=action.output_path,
        model=action.model,
        scale=action.scale,
        realesrgan_bin=action.realesrgan_bin,
        models_dir=action.models_dir,
        keep_frames=action.keep_frames,
    )
