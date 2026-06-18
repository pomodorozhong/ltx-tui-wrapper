from __future__ import annotations

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

import click
from ltx_pipelines_mlx.cli import DEFAULT_GEMMA, DEFAULT_MODEL

P = ParamSpec("P")
R = TypeVar("R")

BOOL_CHOICE = click.Choice(["true", "false"], case_sensitive=False)

# Bare flags like `--distilled` are expanded to `--distilled true` before Click parses argv.
BOOL_FLAGS = frozenset(
    {
        "--quiet",
        "-q",
        "--low-ram",
        "--two-stage",
        "--two-stages-hq",
        "--distilled",
        "--one-stage",
        "--enable-teacache",
        "--enhance-prompt",
        "--no-regen-audio",
        "--skip-stage-2",
        "--with-audio",
    }
)


def tui_bool_option(*param_decls: str, **kwargs: object) -> Callable[[Callable], Callable]:
    """Boolean option rendered as a true/false select in Trogon (not a bare is_flag)."""
    kwargs.setdefault("type", BOOL_CHOICE)
    kwargs.setdefault("default", "false")
    kwargs.setdefault("show_default", True)
    return click.option(*param_decls, **kwargs)


def _apply_options(fn: Callable[P, R], options: list[Callable[[Callable], Callable]]) -> Callable[P, R]:
    for option in reversed(options):
        fn = option(fn)
    return fn


BASE_OPTIONS = [
    click.option("--prompt", "-p", required=True, help="Text prompt"),
    click.option("--output", "-o", required=True, type=click.Path(), help="Output video path (.mp4)"),
    click.option("--model", "-m", default=DEFAULT_MODEL, show_default=True, help="Model weights (HF repo or path)"),
    click.option("--gemma", default=DEFAULT_GEMMA, show_default=True, help="Gemma model for text encoding"),
    click.option("--seed", "-s", default=-1, show_default=True, type=int, help="Random seed (-1 = random)"),
    tui_bool_option("--quiet", "-q", help="Suppress progress output"),
]

GENERATION_OPTIONS = [
    *BASE_OPTIONS,
    click.option("--height", "-H", default=480, show_default=True, type=int, help="Video height"),
    click.option("--width", "-W", default=704, show_default=True, type=int, help="Video width"),
    click.option("--frames", "-f", default=97, show_default=True, type=int, help="Number of frames"),
    click.option(
        "--frame-rate",
        required=True,
        type=float,
        help="Output frame rate (LTX-2.3 was trained at 24 fps)",
    ),
    click.option("--tile-frames", default=1, show_default=True, type=int, help="Temporal tiles (1 = no tiling)"),
    click.option("--tile-spatial", default=1, show_default=True, type=int, help="Spatial tiles per axis"),
    click.option("--tile-overlap", default=2, show_default=True, type=int, help="Token-grid overlap between tiles"),
    tui_bool_option("--low-ram", help="Stream transformer blocks to reduce peak memory"),
]

IMAGE_OPTION = click.option(
    "--image",
    "-i",
    multiple=True,
    help="Reference image: PATH or PATH FRAME_IDX STRENGTH [CRF] (repeatable)",
)

LORA_OPTION = click.option(
    "--lora",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    help="LoRA weights and strength (repeatable)",
)

VIDEO_CONDITIONING_OPTION = click.option(
    "--video-conditioning",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    help="Reference control video and strength (repeatable)",
)


def with_base_options(fn: Callable[P, R]) -> Callable[P, R]:
    return _apply_options(fn, BASE_OPTIONS)


def with_generation_options(fn: Callable[P, R]) -> Callable[P, R]:
    return functools.wraps(fn)(_apply_options(fn, GENERATION_OPTIONS))
