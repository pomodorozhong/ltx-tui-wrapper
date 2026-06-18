from __future__ import annotations

import argparse
import random
from collections.abc import Callable
from typing import Any
from ltx_pipelines_mlx.utils.args import DEFAULT_IMAGE_CRF, ImageConditioningInput


def parse_image_specs(specs: tuple[str, ...] | None) -> list[ImageConditioningInput] | None:
    """Parse ``--image`` values entered as ``PATH`` or ``PATH FRAME_IDX STRENGTH [CRF]``."""
    if not specs:
        return None

    images: list[ImageConditioningInput] = []
    for spec in specs:
        parts = spec.split()
        if len(parts) not in (1, 3, 4):
            raise click.ClickException(
                f"--image: expected PATH or PATH FRAME_IDX STRENGTH [CRF], got: {spec!r}"
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
            raise click.ClickException(f"--image: could not parse {spec!r}: {exc}") from exc
        images.append(ImageConditioningInput(path, frame_idx, strength, crf))
    return images


def _coerce_bool_strings(kwargs: dict[str, Any]) -> None:
    for key, value in list(kwargs.items()):
        if isinstance(value, str) and value.lower() in ("true", "false"):
            kwargs[key] = value.lower() == "true"


def invoke(handler: Callable[[argparse.Namespace], None], **kwargs: Any) -> None:
    """Build an argparse namespace and dispatch to an ltx-2-mlx command handler."""
    _coerce_bool_strings(kwargs)

    images = kwargs.pop("image", None)
    if images is not None:
        kwargs["images"] = parse_image_specs(tuple(images) if images else None)

    lora = kwargs.get("lora")
    if lora is not None:
        kwargs["lora"] = [tuple(pair) for pair in lora]

    video_conditioning = kwargs.get("video_conditioning")
    if video_conditioning is not None:
        kwargs["video_conditioning"] = [tuple(pair) for pair in video_conditioning]

    args = argparse.Namespace(**kwargs)
    if hasattr(args, "seed") and args.seed is not None and args.seed < 0:
        args.seed = random.randint(0, 2**31 - 1)
    handler(args)
