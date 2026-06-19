from __future__ import annotations

import random
import shlex
from collections.abc import Callable
from typing import Any

from ltx_pipelines_mlx.utils.args import DEFAULT_IMAGE_CRF, ImageConditioningInput

from ltx_tui_wrapper.options import GenerateOptions


class GenerateParseError(Exception):
    """Invalid generate option values."""


def parse_image_specs(specs: tuple[str, ...] | None) -> list[ImageConditioningInput] | None:
    """Parse ``--image`` values entered as ``PATH`` or ``PATH FRAME_IDX STRENGTH [CRF]``."""
    if not specs:
        return None

    images: list[ImageConditioningInput] = []
    for spec in specs:
        parts = spec.split()
        if len(parts) not in (1, 3, 4):
            raise GenerateParseError(
                f"Image: expected PATH or PATH FRAME_IDX STRENGTH [CRF], got: {spec!r}"
            )
        path = parts[0]
        if len(parts) == 1:
            images.append(ImageConditioningInput(path, 0, 1.0, DEFAULT_IMAGE_CRF))
            continue
        try:
            frame_idx = int(parts[1])
            strength = float(parts[2])
            crf = int(parts[3]) if len(parts) == 4 else DEFAULT_IMAGE_CRF
        except (ValueError, TypeError) as exc:
            raise GenerateParseError(f"Image: could not parse {spec!r}: {exc}") from exc
        images.append(ImageConditioningInput(path, frame_idx, strength, crf))
    return images


def invoke(handler: Callable[[Any], None], **kwargs: Any) -> None:
    """Build an argparse namespace and dispatch to an ltx-2-mlx command handler."""
    import argparse

    image = kwargs.pop("image", None)
    kwargs["images"] = (
        parse_image_specs(tuple(image) if image else None) if image else None
    )

    lora = kwargs.pop("lora", None)
    kwargs["lora"] = [tuple(pair) for pair in lora] if lora else None

    for key in (
        "steps",
        "stage1_steps",
        "stage2_steps",
        "cfg_scale",
        "stg_scale",
        "teacache_thresh",
    ):
        kwargs.setdefault(key, None)

    args = argparse.Namespace(**kwargs)
    if hasattr(args, "seed") and args.seed is not None and args.seed < 0:
        args.seed = random.randint(0, 2**31 - 1)
    handler(args)


def build_command_argv(options: GenerateOptions) -> list[str]:
    """Build a shell-style argv for ``ltx-2-mlx generate`` (for preview)."""
    argv = ["ltx-2-mlx", "generate", "-p", options.prompt, "-o", options.output]

    mode_flags = {
        "two_stage": "--two-stage",
        "two_stages_hq": "--two-stages-hq",
        "distilled": "--distilled",
        "one_stage": "--one-stage",
    }
    argv.append(mode_flags[options.pipeline_mode])

    if options.model != "dgrauet/ltx-2.3-mlx-q8":
        argv.extend(["-m", options.model])
    if options.gemma != "mlx-community/gemma-3-12b-it-4bit":
        argv.extend(["--gemma", options.gemma])
    if options.seed != -1:
        argv.extend(["-s", str(options.seed)])
    if options.quiet:
        argv.append("-q")
    if options.height != 480:
        argv.extend(["-H", str(options.height)])
    if options.width != 704:
        argv.extend(["-W", str(options.width)])
    if options.frames != 97:
        argv.extend(["-f", str(options.frames)])
    argv.extend(["--frame-rate", str(options.frame_rate)])
    if options.tile_frames != 1:
        argv.extend(["--tile-frames", str(options.tile_frames)])
    if options.tile_spatial != 1:
        argv.extend(["--tile-spatial", str(options.tile_spatial)])
    if options.tile_overlap != 2:
        argv.extend(["--tile-overlap", str(options.tile_overlap)])
    if options.low_ram:
        argv.append("--low-ram")
    for spec in options.image_specs:
        argv.extend(["-i", spec])
    for spec in options.lora_specs:
        parts = spec.split()
        if len(parts) == 2:
            argv.extend(["--lora", parts[0], parts[1]])
    if options.steps is not None:
        argv.extend(["--steps", str(options.steps)])
    if options.stage1_steps is not None:
        argv.extend(["--stage1-steps", str(options.stage1_steps)])
    if options.stage2_steps is not None:
        argv.extend(["--stage2-steps", str(options.stage2_steps)])
    if options.cfg_scale is not None:
        argv.extend(["--cfg-scale", str(options.cfg_scale)])
    if options.stg_scale is not None:
        argv.extend(["--stg-scale", str(options.stg_scale)])
    if options.dev_transformer != "transformer-dev.safetensors":
        argv.extend(["--dev-transformer", options.dev_transformer])
    if options.distilled_lora != "ltx-2.3-22b-distilled-lora-384.safetensors":
        argv.extend(["--distilled-lora", options.distilled_lora])
    if options.distilled_lora_strength != 1.0:
        argv.extend(["--distilled-lora-strength", str(options.distilled_lora_strength)])
    if options.enable_teacache:
        argv.append("--enable-teacache")
    if options.teacache_thresh is not None:
        argv.extend(["--teacache-thresh", str(options.teacache_thresh)])
    if options.enhance_prompt:
        argv.append("--enhance-prompt")
    return argv


def format_command(options: GenerateOptions) -> str:
    """Return a copy-pasteable command string."""
    return shlex.join(build_command_argv(options))
