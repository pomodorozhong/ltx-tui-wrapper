"""Click CLI with Trogon TUI for ltx-2-mlx."""

from __future__ import annotations

import sys

import click
from ltx_pipelines_mlx.cli import (
    DEFAULT_GEMMA,
    _cmd_a2v,
    _cmd_enhance,
    _cmd_extend,
    _cmd_generate,
    _cmd_hdr_ic_lora,
    _cmd_ic_lora,
    _cmd_info,
    _cmd_keyframe,
    _cmd_lipdub,
    _cmd_preprocess,
    _cmd_retake,
    _cmd_slice,
    _cmd_train,
)
from trogon import tui

from ltx_tui_wrapper.options import (
    BOOL_FLAGS,
    IMAGE_OPTION,
    LORA_OPTION,
    MODEL_OPTION,
    VIDEO_CONDITIONING_OPTION,
    tui_bool_option,
    with_base_options,
    with_generation_options,
)
from ltx_tui_wrapper.parsing import invoke


@tui(command="tui", help="Open interactive TUI for ltx-2-mlx")
@click.group(
    name="ltx-tui",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def cli() -> None:
    """LTX-2.3 video generation on Apple Silicon (MLX)."""


@cli.command(help="Generate video from text (T2V) or image (I2V)")
@with_generation_options
@IMAGE_OPTION
@click.option("--steps", type=int, default=None, help="Denoising steps for one-stage (default: 8)")
@tui_bool_option("--two-stage", help="Two-stage pipeline (dev + CFG, upscale, distilled refine)")
@tui_bool_option("--two-stages-hq", help="HQ two-stage pipeline (res_2s sampler)")
@tui_bool_option("--distilled", help="Distilled two-stage pipeline (fastest)")
@tui_bool_option("--one-stage", help="Dev model + CFG one-stage at full resolution")
@click.option("--stage1-steps", type=int, default=None, help="Stage 1 steps")
@click.option("--stage2-steps", type=int, default=None, help="Stage 2 steps (default: 3)")
@click.option("--cfg-scale", type=float, default=None, help="CFG guidance scale (default: 3.0)")
@click.option("--stg-scale", type=float, default=None, help="STG guidance scale")
@click.option("--dev-transformer", default="transformer-dev.safetensors", show_default=True)
@click.option("--distilled-lora", default="ltx-2.3-22b-distilled-lora-384.safetensors", show_default=True)
@click.option("--distilled-lora-strength", default=1.0, show_default=True, type=float)
@tui_bool_option("--enable-teacache", help="Enable TeaCache stage-1 acceleration (two-stage only)")
@click.option("--teacache-thresh", type=float, default=None, help="TeaCache rel_l1_thresh override")
@tui_bool_option("--enhance-prompt", help="Enhance prompt using Gemma before generation")
@LORA_OPTION
def generate(**kwargs) -> None:
    invoke(_cmd_generate, **kwargs)


@cli.command(help="[beta] Generate video from audio + text prompt")
@with_generation_options
@click.option("--audio", "-a", required=True, type=click.Path(), help="Input audio file")
@click.option("--audio-start", default=0.0, show_default=True, type=float, help="Audio start time in seconds")
@click.option("--stage1-steps", type=int, default=None, help="Stage 1 steps (default: 30)")
@click.option("--stage2-steps", type=int, default=None, help="Stage 2 steps (default: 3)")
@click.option("--cfg-scale", type=float, default=None, help="CFG guidance scale (default: 3.0)")
@click.option("--stg-scale", type=float, default=None, help="STG guidance scale (default: 1.0)")
@IMAGE_OPTION
def a2v(**kwargs) -> None:
    invoke(_cmd_a2v, **kwargs)


@cli.command(help="[beta] Regenerate a time segment of an existing video")
@with_base_options
@click.option("--video", "-v", required=True, type=click.Path(), help="Source video file")
@click.option("--start", required=True, type=int, help="Start latent frame index (inclusive)")
@click.option("--end", required=True, type=int, help="End latent frame index (exclusive)")
@click.option("--steps", type=int, default=None, help="Denoising steps (default: 30)")
@click.option("--cfg-scale", type=float, default=None, help="CFG guidance scale (default: 3.0)")
@click.option("--stg-scale", type=float, default=None, help="STG guidance scale (default: 1.0)")
@tui_bool_option("--no-regen-audio", help="Preserve original audio")
def retake(**kwargs) -> None:
    invoke(_cmd_retake, **kwargs)


@cli.command(help="[beta] Add frames before or after an existing video")
@with_base_options
@click.option("--video", "-v", required=True, type=click.Path(), help="Source video file")
@click.option("--extend-frames", required=True, type=int, help="Number of latent frames to add")
@click.option(
    "--direction",
    type=click.Choice(["before", "after"]),
    default="after",
    show_default=True,
    help="Direction to extend",
)
@click.option("--steps", type=int, default=None, help="Denoising steps (default: 30)")
@click.option("--cfg-scale", type=float, default=None, help="CFG guidance scale (default: 3.0)")
@click.option("--stg-scale", type=float, default=None, help="STG guidance scale (default: 1.0)")
def extend(**kwargs) -> None:
    invoke(_cmd_extend, **kwargs)


@cli.command(help="Interpolate between keyframe images")
@with_generation_options
@click.option("--start", required=True, type=click.Path(), help="Start keyframe image path")
@click.option("--end", required=True, type=click.Path(), help="End keyframe image path")
@click.option("--start-strength", default=1.0, show_default=True, type=float)
@click.option("--end-strength", default=1.0, show_default=True, type=float)
@click.option("--stage1-steps", type=int, default=None, help="Stage 1 denoising steps")
@click.option("--stage2-steps", type=int, default=None, help="Stage 2 denoising steps")
@click.option("--cfg-scale", type=float, default=None, help="CFG scale (default: 3.0 video, 7.0 audio)")
@click.option("--stg-scale", type=float, default=None, help="STG scale (default: 1.0)")
@click.option("--dev-transformer", default=None, help="Dev transformer filename for stage 1")
@click.option("--distilled-lora", default=None, help="Distilled LoRA filename for stage 2")
@click.option("--lora-strength", default=1.0, show_default=True, type=float, help="Distilled LoRA strength")
def keyframe(**kwargs) -> None:
    invoke(_cmd_keyframe, **kwargs)


@cli.command("ic-lora", help="Generate video with IC-LoRA control conditioning")
@with_generation_options
@click.option(
    "--lora",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    required=True,
    help="IC-LoRA weights and strength (repeatable)",
)
@click.option(
    "--video-conditioning",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    required=True,
    help="Reference control video and strength (repeatable)",
)
@IMAGE_OPTION
@click.option("--stage1-steps", type=int, default=None, help="Stage 1 denoising steps")
@click.option("--stage2-steps", type=int, default=None, help="Stage 2 denoising steps")
@click.option("--conditioning-strength", default=1.0, show_default=True, type=float)
@tui_bool_option("--skip-stage-2", help="Skip stage 2 upsampling")
def ic_lora(**kwargs) -> None:
    invoke(_cmd_ic_lora, **kwargs)


@cli.command(help="[experimental] Lip-dub a reference video")
@with_base_options
@click.option("--height", "-H", default=480, show_default=True, type=int)
@click.option("--width", "-W", default=704, show_default=True, type=int)
@tui_bool_option("--low-ram", help="Stream transformer blocks")
@click.option("--reference-video", required=True, type=click.Path(), help="Reference video")
@click.option("--reference-strength", default=1.0, show_default=True, type=float)
@click.option(
    "--lora",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    required=True,
    help="Lip-dub IC-LoRA (exactly one required)",
)
@click.option("--stage1-steps", type=int, default=None)
@click.option("--stage2-steps", type=int, default=None)
def lipdub(**kwargs) -> None:
    invoke(_cmd_lipdub, **kwargs)


@cli.command("hdr-ic-lora", help="Generate HDR video via IC-LoRA with LogC3 inverse")
@with_generation_options
@click.option(
    "--lora",
    multiple=True,
    nargs=2,
    metavar="PATH STRENGTH",
    required=True,
    help="HDR IC-LoRA weights and strength (repeatable)",
)
@VIDEO_CONDITIONING_OPTION
@IMAGE_OPTION
@click.option("--stage1-steps", type=int, default=None)
@click.option("--stage2-steps", type=int, default=None)
@click.option("--conditioning-strength", default=1.0, show_default=True, type=float)
@tui_bool_option("--skip-stage-2")
def hdr_ic_lora(**kwargs) -> None:
    invoke(_cmd_hdr_ic_lora, **kwargs)


@cli.command(help="Enhance a prompt using Gemma (no video generation)")
@click.option("--prompt", "-p", required=True, help="Prompt to enhance")
@click.option("--mode", type=click.Choice(["t2v", "i2v"]), default="t2v", show_default=True)
@click.option("--gemma", default=DEFAULT_GEMMA, show_default=True)
@click.option("--seed", "-s", default=10, show_default=True, type=int)
def enhance(**kwargs) -> None:
    invoke(_cmd_enhance, **kwargs)


@cli.command(help="Show model info and memory estimate")
@MODEL_OPTION
def info(**kwargs) -> None:
    invoke(_cmd_info, **kwargs)


@cli.command(help="Train a LoRA or full model (requires ltx-trainer-mlx)")
@click.option("--config", "-c", required=True, type=click.Path(), help="Training config YAML")
@tui_bool_option("--low-ram", help="Enable gradient checkpointing")
def train(**kwargs) -> None:
    invoke(_cmd_train, **kwargs)


@cli.command(help="Preprocess videos into latents + conditions for training")
@click.option("--videos", "-v", required=True, type=click.Path(), help="Directory of video files")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output directory")
@MODEL_OPTION
@click.option("--gemma", default=DEFAULT_GEMMA, show_default=True)
@click.option("--height", "-H", default=None, type=int, help="Resize height")
@click.option("--width", "-W", default=None, type=int, help="Resize width")
@click.option("--max-frames", default=97, show_default=True, type=int)
@click.option("--captions", default=None, type=click.Path(), help="Caption files directory")
@click.option("--caption-ext", default=".txt", show_default=True)
@tui_bool_option("--with-audio", help="Also encode audio latents")
@click.option("--frame-rate", default=None, type=float, help="Override fps per clip")
def preprocess(**kwargs) -> None:
    invoke(_cmd_preprocess, **kwargs)


@cli.command(help="Slice long videos into normalized training clips")
@click.argument("sources", nargs=-1, required=True)
@click.option("--output", "-o", required=True, type=click.Path(), help="Root output directory")
@click.option("--interval", default=4.0, show_default=True, type=float, help="Clip length in seconds")
@click.option("--timecodes", default=None, type=click.Path(), help="Start,end timecode list file")
@click.option("--res", default="384x384", show_default=True, help="Target resolution WxH")
@click.option("--fps", default=24.0, show_default=True, type=float, help="Output frame rate")
@click.option("--fit", type=click.Choice(["crop", "pad"]), default="crop", show_default=True)
@click.option("--min-length", default=2.0, show_default=True, type=float)
@click.option("--max-clips", default=None, type=int)
@click.option("--sample", type=click.Choice(["even", "sequential"]), default="even", show_default=True)
@click.option("--skip-start", default=0.0, show_default=True, type=float)
@click.option("--skip-end", default=0.0, show_default=True, type=float)
@click.option("--caption-template", default=None, help="Caption text written next to each clip")
@click.option("--crf", default=18, show_default=True, type=int, help="x264 quality (lower = better)")
def slice(sources: tuple[str, ...], **kwargs) -> None:
    invoke(_cmd_slice, sources=list(sources), **kwargs)


def _normalize_bool_flags(argv: list[str]) -> list[str]:
    """Allow bare flags like ``--distilled`` as shorthand for ``--distilled true``."""
    normalized: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in BOOL_FLAGS:
            normalized.append(arg)
            if i + 1 < len(argv) and argv[i + 1].lower() in ("true", "false"):
                i += 1
                normalized.append(argv[i])
            else:
                normalized.append("true")
        else:
            normalized.append(arg)
        i += 1
    return normalized


def main() -> None:
    sys.argv = _normalize_bool_flags(sys.argv)
    cli()


if __name__ == "__main__":
    main()
