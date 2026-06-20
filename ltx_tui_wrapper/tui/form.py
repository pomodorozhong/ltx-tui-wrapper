"""Read generate options from TUI widgets."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from textual.widgets import Checkbox, Select

from ltx_tui_wrapper.options import MODEL_IDS, GenerateOptions
from ltx_tui_wrapper.tui.widgets import CopyInput, CopyTextArea


class FormWidgets(Protocol):
    """Minimal widget query surface used by :class:`GenerateForm`."""

    def query_one(self, selector: str, expect_type: type): ...


def _optional_int(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    return int(text)


def _optional_float(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    return float(text)


def _lines(text_area: CopyTextArea) -> tuple[str, ...]:
    return tuple(line.strip() for line in text_area.text.splitlines() if line.strip())


def _format_optional(value: int | float | None) -> str:
    return "" if value is None else str(value)


def _split_primary_image(
    image_specs: tuple[str, ...],
) -> tuple[str, str, str, str, tuple[str, ...]]:
    """Split image specs into primary fields and extra lines."""
    if not image_specs:
        return "", "0", "1.0", "", ()
    parts = image_specs[0].split()
    path = parts[0]
    if len(parts) == 1:
        return path, "0", "1.0", "", image_specs[1:]
    if len(parts) == 3:
        return path, parts[1], parts[2], "", image_specs[1:]
    if len(parts) == 4:
        return path, parts[1], parts[2], parts[3], image_specs[1:]
    return image_specs[0], "0", "1.0", "", image_specs[1:]


def _resolution_preset(height: int, width: int) -> str:
    preset = f"{height}x{width}"
    if preset in ("480x704", "768x512"):
        return preset
    return "custom"


def _frame_rate(select: Select[str], custom: CopyInput) -> float:
    value = select.value
    if value is Select.BLANK:
        return 24.0
    if value == "custom":
        text = custom.value.strip()
        return float(text) if text else 24.0
    return float(value)


def _resolution(
    preset: Select[str],
    height_input: CopyInput,
    width_input: CopyInput,
) -> tuple[int, int]:
    value = preset.value
    if value is Select.BLANK or value == "custom":
        return int(height_input.value.strip() or "480"), int(width_input.value.strip() or "704")
    height_text, width_text = value.split("x", 1)
    return int(height_text), int(width_text)


class GenerateForm:
    """Reads :class:`~ltx_tui_wrapper.options.GenerateOptions` from the TUI."""

    def __init__(self, app: FormWidgets) -> None:
        self._app = app

    def collect(self) -> GenerateOptions:
        image_path = self._app.query_one("#image-path", CopyInput).value.strip()
        image_specs: list[str] = []
        if image_path:
            frame_idx = self._app.query_one("#image-frame-idx", CopyInput).value.strip() or "0"
            strength = self._app.query_one("#image-strength", CopyInput).value.strip() or "1.0"
            crf = self._app.query_one("#image-crf", CopyInput).value.strip()
            if frame_idx == "0" and strength == "1.0" and not crf:
                image_specs.append(image_path)
            elif crf:
                image_specs.append(f"{image_path} {frame_idx} {strength} {crf}")
            else:
                image_specs.append(f"{image_path} {frame_idx} {strength}")
        image_specs.extend(_lines(self._app.query_one("#extra-images", CopyTextArea)))

        height, width = _resolution(
            self._app.query_one("#resolution-preset", Select),
            self._app.query_one("#height", CopyInput),
            self._app.query_one("#width", CopyInput),
        )

        pipeline_mode = self._app.query_one("#pipeline-mode", Select).value
        if pipeline_mode is Select.BLANK:
            pipeline_mode = "two_stage"

        return GenerateOptions(
            prompt=self._app.query_one("#prompt", CopyInput).value.strip(),
            output=self._app.query_one("#output-path", CopyInput).value.strip(),
            frame_rate=_frame_rate(
                self._app.query_one("#frame-rate-preset", Select),
                self._app.query_one("#frame-rate", CopyInput),
            ),
            pipeline_mode=pipeline_mode,
            model=self._app.query_one("#model", Select).value or "dgrauet/ltx-2.3-mlx-q8",
            gemma=self._app.query_one("#gemma", CopyInput).value.strip()
            or "mlx-community/gemma-3-12b-it-4bit",
            seed=int(self._app.query_one("#seed", CopyInput).value.strip() or "-1"),
            quiet=self._app.query_one("#quiet", Checkbox).value,
            height=height,
            width=width,
            frames=int(self._app.query_one("#frames", CopyInput).value.strip() or "97"),
            tile_frames=int(self._app.query_one("#tile-frames", CopyInput).value.strip() or "1"),
            tile_spatial=int(self._app.query_one("#tile-spatial", CopyInput).value.strip() or "1"),
            tile_overlap=int(self._app.query_one("#tile-overlap", CopyInput).value.strip() or "2"),
            low_ram=self._app.query_one("#low-ram", Checkbox).value,
            image_specs=tuple(image_specs),
            lora_specs=_lines(self._app.query_one("#lora-specs", CopyTextArea)),
            steps=_optional_int(self._app.query_one("#steps", CopyInput).value),
            stage1_steps=_optional_int(self._app.query_one("#stage1-steps", CopyInput).value),
            stage2_steps=_optional_int(self._app.query_one("#stage2-steps", CopyInput).value),
            cfg_scale=_optional_float(self._app.query_one("#cfg-scale", CopyInput).value),
            stg_scale=_optional_float(self._app.query_one("#stg-scale", CopyInput).value),
            dev_transformer=self._app.query_one("#dev-transformer", CopyInput).value.strip()
            or "transformer-dev.safetensors",
            distilled_lora=self._app.query_one("#distilled-lora", CopyInput).value.strip()
            or "ltx-2.3-22b-distilled-lora-384.safetensors",
            distilled_lora_strength=float(
                self._app.query_one("#distilled-lora-strength", CopyInput).value.strip() or "1.0"
            ),
            enable_teacache=self._app.query_one("#enable-teacache", Checkbox).value,
            teacache_thresh=_optional_float(self._app.query_one("#teacache-thresh", CopyInput).value),
            enhance_prompt=self._app.query_one("#enhance-prompt", Checkbox).value,
        )

    def browse_start_dir(self, input_id: str) -> Path:
        text = self._app.query_one(input_id, CopyInput).value.strip() or "."
        start = Path(text)
        return start.parent if start.suffix else start

    def browse_save_defaults(self) -> tuple[Path, str]:
        text = self._app.query_one("#output-path", CopyInput).value.strip()
        if text:
            path = Path(text)
            if path.suffix:
                return path.parent, path.name
            return path, "output.mp4"
        return Path.cwd(), "output.mp4"

    def sync_custom_visibility(self, preset_id: str, custom_id: str) -> None:
        preset = self._app.query_one(
            preset_id if preset_id.startswith("#") else f"#{preset_id}",
            Select,
        )
        custom = self._app.query_one(
            custom_id if custom_id.startswith("#") else f"#{custom_id}",
            CopyInput,
        )
        if preset.value == "custom":
            custom.add_class("visible")
        else:
            custom.remove_class("visible")

    def sync_resolution_visibility(self) -> None:
        preset = self._app.query_one("#resolution-preset", Select)
        height = self._app.query_one("#height", CopyInput)
        width = self._app.query_one("#width", CopyInput)
        custom = preset.value == "custom"
        height.disabled = not custom
        width.disabled = not custom
        if not custom and preset.value not in (Select.BLANK, "custom"):
            h, w = _resolution(preset, height, width)
            height.value = str(h)
            width.value = str(w)

    def try_collect_for_preview(self) -> GenerateOptions | None:
        try:
            return self.collect()
        except (ValueError, TypeError):
            return None

    def apply(self, options: GenerateOptions) -> None:
        """Populate the form from a :class:`GenerateOptions` instance."""
        self._app.query_one("#prompt", CopyInput).value = options.prompt
        self._app.query_one("#output-path", CopyInput).value = options.output
        self._app.query_one("#pipeline-mode", Select).value = options.pipeline_mode

        frame_rate_preset = self._app.query_one("#frame-rate-preset", Select)
        frame_rate_input = self._app.query_one("#frame-rate", CopyInput)
        if options.frame_rate == 24.0:
            frame_rate_preset.value = "24"
            frame_rate_input.value = ""
        else:
            frame_rate_preset.value = "custom"
            frame_rate_input.value = str(options.frame_rate)

        resolution_preset = self._app.query_one("#resolution-preset", Select)
        resolution_preset.value = _resolution_preset(options.height, options.width)
        self._app.query_one("#height", CopyInput).value = str(options.height)
        self._app.query_one("#width", CopyInput).value = str(options.width)
        self._app.query_one("#frames", CopyInput).value = str(options.frames)

        image_path, frame_idx, strength, crf, extra_images = _split_primary_image(
            options.image_specs
        )
        self._app.query_one("#image-path", CopyInput).value = image_path
        self._app.query_one("#image-frame-idx", CopyInput).value = frame_idx
        self._app.query_one("#image-strength", CopyInput).value = strength
        self._app.query_one("#image-crf", CopyInput).value = crf
        self._app.query_one("#extra-images", CopyTextArea).text = "\n".join(extra_images)

        self._app.query_one("#steps", CopyInput).value = _format_optional(options.steps)
        self._app.query_one("#stage1-steps", CopyInput).value = _format_optional(options.stage1_steps)
        self._app.query_one("#stage2-steps", CopyInput).value = _format_optional(options.stage2_steps)
        self._app.query_one("#cfg-scale", CopyInput).value = _format_optional(options.cfg_scale)
        self._app.query_one("#stg-scale", CopyInput).value = _format_optional(options.stg_scale)
        self._app.query_one("#enhance-prompt", Checkbox).value = options.enhance_prompt

        self._app.query_one("#dev-transformer", CopyInput).value = options.dev_transformer
        self._app.query_one("#distilled-lora", CopyInput).value = options.distilled_lora
        self._app.query_one("#distilled-lora-strength", CopyInput).value = str(
            options.distilled_lora_strength
        )
        self._app.query_one("#enable-teacache", Checkbox).value = options.enable_teacache
        self._app.query_one("#teacache-thresh", CopyInput).value = _format_optional(
            options.teacache_thresh
        )

        self._app.query_one("#lora-specs", CopyTextArea).text = "\n".join(options.lora_specs)

        model_select = self._app.query_one("#model", Select)
        if options.model in MODEL_IDS:
            model_select.value = options.model
        self._app.query_one("#gemma", CopyInput).value = options.gemma
        self._app.query_one("#seed", CopyInput).value = str(options.seed)
        self._app.query_one("#low-ram", Checkbox).value = options.low_ram
        self._app.query_one("#quiet", Checkbox).value = options.quiet
        self._app.query_one("#tile-frames", CopyInput).value = str(options.tile_frames)
        self._app.query_one("#tile-spatial", CopyInput).value = str(options.tile_spatial)
        self._app.query_one("#tile-overlap", CopyInput).value = str(options.tile_overlap)
