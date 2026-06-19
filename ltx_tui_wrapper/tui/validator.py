"""Form validation for the generate TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from textual.widgets import Checkbox, Input, Select

from ltx_tui_wrapper.tui.form import GenerateForm, _frame_rate


@dataclass
class ValidationResult:
    """Outcome of validating the TUI form before a run."""

    error_message: str | None = None
    highlight_widget_ids: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error_message is None


class GenerateFormValidator:
    """Validates form state and maps errors to widget highlights."""

    def __init__(self, form: GenerateForm) -> None:
        self._form = form

    def validate(self) -> ValidationResult:
        app = self._form._app
        highlights: list[str] = []
        errors: list[str] = []

        prompt = app.query_one("#prompt", Input).value.strip()
        if not prompt:
            highlights.append("#prompt")
            errors.append("Prompt is required.")

        output_text = app.query_one("#output-path", Input).value.strip()
        if not output_text:
            highlights.append("#output-path")
            errors.append("Output path is required.")
        elif not output_text.lower().endswith(".mp4"):
            highlights.append("#output-path")
            errors.append("Output should be an .mp4 path.")

        pipeline_mode = app.query_one("#pipeline-mode", Select).value
        if pipeline_mode is Select.BLANK:
            highlights.append("#pipeline-mode")
            errors.append("Pipeline mode is required.")

        frame_rate_select = app.query_one("#frame-rate-preset", Select)
        frame_rate_custom = app.query_one("#frame-rate", Input)
        try:
            frame_rate = _frame_rate(frame_rate_select, frame_rate_custom)
            if frame_rate <= 0:
                raise ValueError("frame rate must be positive")
        except ValueError:
            widget = (
                "#frame-rate"
                if frame_rate_select.value == "custom"
                else "#frame-rate-preset"
            )
            highlights.append(widget)
            errors.append("Invalid frame rate.")

        image_path = app.query_one("#image-path", Input).value.strip()
        if image_path and not Path(image_path).is_file():
            highlights.append("#image-path")
            errors.append(f"Image not found: {image_path}")

        numeric_fields: list[tuple[str, str, str]] = [
            ("#height", "height", "positive integer"),
            ("#width", "width", "positive integer"),
            ("#frames", "frames", "positive integer"),
            ("#seed", "seed", "integer"),
            ("#steps", "steps", "positive integer"),
            ("#stage1-steps", "stage 1 steps", "positive integer"),
            ("#stage2-steps", "stage 2 steps", "positive integer"),
            ("#cfg-scale", "CFG scale", "number"),
            ("#stg-scale", "STG scale", "number"),
            ("#teacache-thresh", "TeaCache threshold", "number"),
            ("#distilled-lora-strength", "distilled LoRA strength", "number"),
            ("#image-frame-idx", "image frame index", "integer"),
            ("#image-strength", "image strength", "number"),
            ("#image-crf", "image CRF", "integer"),
        ]
        for widget_id, label, _ in numeric_fields:
            text = app.query_one(widget_id, Input).value.strip()
            if not text:
                continue
            try:
                value = float(text) if "scale" in label or "strength" in label or "threshold" in label else int(text)
                if "positive" in _ and value <= 0:
                    raise ValueError
            except ValueError:
                highlights.append(widget_id)
                errors.append(f"Invalid {label}.")

        enable_teacache = app.query_one("#enable-teacache", Checkbox).value
        if enable_teacache and pipeline_mode not in ("two_stage", "two_stages_hq"):
            highlights.append("#enable-teacache")
            errors.append("TeaCache requires two-stage or two-stage HQ mode.")

        if not errors:
            return ValidationResult()

        return ValidationResult(
            error_message="; ".join(errors),
            highlight_widget_ids=list(dict.fromkeys(highlights)),
        )
