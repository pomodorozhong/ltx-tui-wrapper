"""Read generate options from TUI widgets."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from textual.widgets import Checkbox, Input, Select, TextArea

from ltx_tui_wrapper.options import GenerateOptions


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


def _lines(text_area: TextArea) -> tuple[str, ...]:
    return tuple(line.strip() for line in text_area.text.splitlines() if line.strip())


def _frame_rate(select: Select[str], custom: Input) -> float:
    value = select.value
    if value is Select.BLANK:
        return 24.0
    if value == "custom":
        text = custom.value.strip()
        return float(text) if text else 24.0
    return float(value)


def _resolution(
    preset: Select[str],
    height_input: Input,
    width_input: Input,
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
        image_path = self._app.query_one("#image-path", Input).value.strip()
        image_specs: list[str] = []
        if image_path:
            frame_idx = self._app.query_one("#image-frame-idx", Input).value.strip() or "0"
            strength = self._app.query_one("#image-strength", Input).value.strip() or "1.0"
            crf = self._app.query_one("#image-crf", Input).value.strip()
            if frame_idx == "0" and strength == "1.0" and not crf:
                image_specs.append(image_path)
            elif crf:
                image_specs.append(f"{image_path} {frame_idx} {strength} {crf}")
            else:
                image_specs.append(f"{image_path} {frame_idx} {strength}")
        image_specs.extend(_lines(self._app.query_one("#extra-images", TextArea)))

        height, width = _resolution(
            self._app.query_one("#resolution-preset", Select),
            self._app.query_one("#height", Input),
            self._app.query_one("#width", Input),
        )

        pipeline_mode = self._app.query_one("#pipeline-mode", Select).value
        if pipeline_mode is Select.BLANK:
            pipeline_mode = "two_stage"

        return GenerateOptions(
            prompt=self._app.query_one("#prompt", Input).value.strip(),
            output=self._app.query_one("#output-path", Input).value.strip(),
            frame_rate=_frame_rate(
                self._app.query_one("#frame-rate-preset", Select),
                self._app.query_one("#frame-rate", Input),
            ),
            pipeline_mode=pipeline_mode,
            model=self._app.query_one("#model", Select).value or "dgrauet/ltx-2.3-mlx-q8",
            gemma=self._app.query_one("#gemma", Input).value.strip()
            or "mlx-community/gemma-3-12b-it-4bit",
            seed=int(self._app.query_one("#seed", Input).value.strip() or "-1"),
            quiet=self._app.query_one("#quiet", Checkbox).value,
            height=height,
            width=width,
            frames=int(self._app.query_one("#frames", Input).value.strip() or "97"),
            tile_frames=int(self._app.query_one("#tile-frames", Input).value.strip() or "1"),
            tile_spatial=int(self._app.query_one("#tile-spatial", Input).value.strip() or "1"),
            tile_overlap=int(self._app.query_one("#tile-overlap", Input).value.strip() or "2"),
            low_ram=self._app.query_one("#low-ram", Checkbox).value,
            image_specs=tuple(image_specs),
            lora_specs=_lines(self._app.query_one("#lora-specs", TextArea)),
            steps=_optional_int(self._app.query_one("#steps", Input).value),
            stage1_steps=_optional_int(self._app.query_one("#stage1-steps", Input).value),
            stage2_steps=_optional_int(self._app.query_one("#stage2-steps", Input).value),
            cfg_scale=_optional_float(self._app.query_one("#cfg-scale", Input).value),
            stg_scale=_optional_float(self._app.query_one("#stg-scale", Input).value),
            dev_transformer=self._app.query_one("#dev-transformer", Input).value.strip()
            or "transformer-dev.safetensors",
            distilled_lora=self._app.query_one("#distilled-lora", Input).value.strip()
            or "ltx-2.3-22b-distilled-lora-384.safetensors",
            distilled_lora_strength=float(
                self._app.query_one("#distilled-lora-strength", Input).value.strip() or "1.0"
            ),
            enable_teacache=self._app.query_one("#enable-teacache", Checkbox).value,
            teacache_thresh=_optional_float(self._app.query_one("#teacache-thresh", Input).value),
            enhance_prompt=self._app.query_one("#enhance-prompt", Checkbox).value,
        )

    def browse_start_dir(self, input_id: str) -> Path:
        text = self._app.query_one(input_id, Input).value.strip() or "."
        start = Path(text)
        return start.parent if start.suffix else start

    def browse_save_defaults(self) -> tuple[Path, str]:
        text = self._app.query_one("#output-path", Input).value.strip()
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
            Input,
        )
        if preset.value == "custom":
            custom.add_class("visible")
        else:
            custom.remove_class("visible")

    def sync_resolution_visibility(self) -> None:
        preset = self._app.query_one("#resolution-preset", Select)
        height = self._app.query_one("#height", Input)
        width = self._app.query_one("#width", Input)
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
