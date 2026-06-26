"""Run payloads produced when the user presses Run in the TUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

from ltx_tui_wrapper.batch_cli import run_batch
from ltx_tui_wrapper.extend import run_extend_batch
from ltx_tui_wrapper.extend_from import run_extend_from_inputs
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.progress import abort_if_missing_output_directory
from ltx_tui_wrapper.upscale import upscale_video


@dataclass(frozen=True)
class GenerateRun:
    command: list[str]
    options: GenerateOptions


@dataclass(frozen=True)
class BatchRun:
    count: int
    max_retries: int
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


@dataclass(frozen=True)
class ExtendFromRun:
    input_path: str
    target_duration: float
    max_retries: int
    final_output: str | None
    keep_segments: bool
    continue_on_error: bool
    upscale: bool
    upscale_model: str
    upscale_scale: int | None
    realesrgan_bin: str | None
    models_dir: str | None


RunAction = GenerateRun | BatchRun | ExtendRun | UpscaleRun | ExtendFromRun

RunExecutor = Callable[[RunAction], int]
_EXECUTORS: dict[type[RunAction], RunExecutor] = {}

ActionT = TypeVar("ActionT", bound=RunAction)


def register_run_executor(
    action_type: type[ActionT],
) -> Callable[[Callable[[ActionT], int]], Callable[[ActionT], int]]:
    """Register a run executor for a specific action payload type."""

    def decorator(func: Callable[[ActionT], int]) -> Callable[[ActionT], int]:
        _EXECUTORS[action_type] = func  # type: ignore[assignment]
        return func

    return decorator


@register_run_executor(GenerateRun)
def _execute_generate(action: GenerateRun) -> int:
    from ltx_tui_wrapper.runner import execute_command
    from ltx_tui_wrapper.video_metadata import write_command_metadata

    if abort_if_missing_output_directory(action.options.output):
        return 1

    exit_code = execute_command(action.command)
    if exit_code == 0:
        write_command_metadata(Path(action.options.output), action.command)
    return exit_code


@register_run_executor(BatchRun)
def _execute_batch(action: BatchRun) -> int:
    return run_batch(
        count=action.count,
        max_retries=action.max_retries,
        continue_on_error=action.continue_on_error,
    )


@register_run_executor(ExtendRun)
def _execute_extend(action: ExtendRun) -> int:
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


@register_run_executor(ExtendFromRun)
def _execute_extend_from(action: ExtendFromRun) -> int:
    return run_extend_from_inputs(
        input_path=Path(action.input_path),
        target_duration=action.target_duration,
        max_retries=action.max_retries,
        final_output=action.final_output,
        keep_segments=action.keep_segments,
        continue_on_error=action.continue_on_error,
        upscale=action.upscale,
        upscale_model=action.upscale_model,
        upscale_scale=action.upscale_scale,
        realesrgan_bin=action.realesrgan_bin,
        models_dir=action.models_dir,
    )


@register_run_executor(UpscaleRun)
def _execute_upscale(action: UpscaleRun) -> int:
    return upscale_video(
        input_path=action.input_path,
        output_path=action.output_path,
        model=action.model,
        scale=action.scale,
        realesrgan_bin=action.realesrgan_bin,
        models_dir=action.models_dir,
        keep_frames=action.keep_frames,
    )


def execute_run_action(action: RunAction) -> int:
    executor = _EXECUTORS.get(type(action))
    if executor is None:
        raise TypeError(f"No run executor registered for {type(action).__name__}")
    return executor(action)
