from __future__ import annotations

from dataclasses import dataclass, field

from ltx_pipelines_mlx.cli import DEFAULT_GEMMA, DEFAULT_MODEL

MODEL_IDS = (
    "dgrauet/ltx-2.3-mlx-q4",
    "dgrauet/ltx-2.3-mlx-q8",
    "dgrauet/ltx-2.3-mlx",
)

PIPELINE_MODES = (
    ("Two-stage (recommended)", "two_stage"),
    ("Two-stage HQ", "two_stages_hq"),
    ("Distilled (fastest)", "distilled"),
    ("One-stage (full res)", "one_stage"),
)


@dataclass
class GenerateOptions:
    """Options for ``ltx-2-mlx generate`` collected from the TUI."""

    prompt: str
    output: str
    frame_rate: float
    pipeline_mode: str

    model: str = DEFAULT_MODEL
    gemma: str = DEFAULT_GEMMA
    seed: int = -1
    quiet: bool = False

    height: int = 480
    width: int = 704
    frames: int = 97
    tile_frames: int = 1
    tile_spatial: int = 1
    tile_overlap: int = 2
    low_ram: bool = False

    image_specs: tuple[str, ...] = ()
    lora_specs: tuple[str, ...] = ()

    steps: int | None = None
    stage1_steps: int | None = None
    stage2_steps: int | None = None
    cfg_scale: float | None = None
    stg_scale: float | None = None
    dev_transformer: str = "transformer-dev.safetensors"
    distilled_lora: str = "ltx-2.3-22b-distilled-lora-384.safetensors"
    distilled_lora_strength: float = 1.0
    enable_teacache: bool = False
    teacache_thresh: float | None = None
    enhance_prompt: bool = False

    def to_kwargs(self) -> dict:
        """Keyword arguments for :func:`ltx_tui_wrapper.parsing.invoke`."""
        kwargs: dict = {
            "prompt": self.prompt,
            "output": self.output,
            "frame_rate": self.frame_rate,
            "model": self.model,
            "gemma": self.gemma,
            "seed": self.seed,
            "quiet": self.quiet,
            "height": self.height,
            "width": self.width,
            "frames": self.frames,
            "tile_frames": self.tile_frames,
            "tile_spatial": self.tile_spatial,
            "tile_overlap": self.tile_overlap,
            "low_ram": self.low_ram,
            "dev_transformer": self.dev_transformer,
            "distilled_lora": self.distilled_lora,
            "distilled_lora_strength": self.distilled_lora_strength,
            "enhance_prompt": self.enhance_prompt,
            "two_stage": self.pipeline_mode == "two_stage",
            "two_stages_hq": self.pipeline_mode == "two_stages_hq",
            "distilled": self.pipeline_mode == "distilled",
            "one_stage": self.pipeline_mode == "one_stage",
            "enable_teacache": self.enable_teacache,
        }
        if self.image_specs:
            kwargs["image"] = self.image_specs
        if self.lora_specs:
            kwargs["lora"] = tuple(spec.split() for spec in self.lora_specs if spec.strip())
        for key in (
            "steps",
            "stage1_steps",
            "stage2_steps",
            "cfg_scale",
            "stg_scale",
            "teacache_thresh",
        ):
            value = getattr(self, key)
            if value is not None:
                kwargs[key] = value
        return kwargs
