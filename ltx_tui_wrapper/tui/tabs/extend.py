"""Extend tab for the ltx-tui application."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Collapsible, Label, Select, Static

from ltx_tui_wrapper.extend import extended_output_path, parse_target_duration
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.tui.command_preview import extend_first_segment_command_preview
from ltx_tui_wrapper.tui.constants import EXTEND_UPSCALE_MODEL_PRESETS
from ltx_tui_wrapper.tui.run_actions import ExtendRun
from ltx_tui_wrapper.tui.tabs.shared import TabMixinBase
from ltx_tui_wrapper.tui.widgets import CopyInput
from ltx_tui_wrapper.upscale import AI_SCALES


class ExtendTabMixin(TabMixinBase):
    """Compose, events, and run logic for the Extend tab."""

    def _compose_extend_tab(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "Chain I2V segments from the last Generate output until the combined "
                "duration exceeds the target length.",
                classes="field-hint",
            )
            yield Label("Target duration", classes="field-label")
            yield CopyInput(placeholder="60, 90s, or 1.5m", id="extend-length")
            yield Static(
                "Seconds (60), suffixed seconds (90s), or minutes (1.5m).",
                classes="field-hint",
            )
            yield Label("Retries per segment", classes="field-label")
            yield CopyInput(value="1", id="extend-retries")
            yield Label("Number of extended videos", classes="field-label")
            yield CopyInput(value="1", id="extend-count")
            yield Label("Final output path (optional)", classes="field-label")
            yield CopyInput(
                placeholder="default: <last-output>_extended_<timestamp>.mp4",
                id="extend-output",
            )
            yield Checkbox("Append timestamp to output name", id="extend-timestamp", value=True)
            yield Checkbox("Keep segment files", id="extend-keep-segments")
            yield Checkbox("Continue on error", id="extend-continue-on-error")
            with Collapsible(title="Upscale last frame between segments", collapsed=True):
                yield Checkbox("AI-upscale last frame before next segment", id="extend-upscale")
                yield Label("Upscale model", classes="field-label")
                yield Select(
                    EXTEND_UPSCALE_MODEL_PRESETS,
                    id="extend-upscale-model",
                    value="realesrgan-x4plus",
                )
                yield Label("Upscale scale (optional)", classes="field-label")
                yield CopyInput(
                    placeholder=f"auto or one of {', '.join(map(str, AI_SCALES))}",
                    id="extend-upscale-scale",
                )
                yield Label("realesrgan-ncnn-vulkan binary (optional)", classes="field-label")
                yield CopyInput(id="extend-realesrgan-bin")
                yield Label("Models directory (optional)", classes="field-label")
                yield CopyInput(id="extend-models-dir")
            yield Label("First ltx-2-mlx generate command", classes="field-label")
            yield Static("", id="extend-command-preview", classes="command-preview")

    def _mount_extend_tab(self) -> None:
        if self._extend_length is not None:
            self.query_one("#extend-length", CopyInput).value = self._extend_length
        if self._extend_retries is not None:
            self.query_one("#extend-retries", CopyInput).value = str(self._extend_retries)
        if self._extend_count is not None:
            self.query_one("#extend-count", CopyInput).value = str(self._extend_count)
        if self._extend_output is not None:
            self.query_one("#extend-output", CopyInput).value = self._extend_output
        if self._extend_timestamp is not None:
            self.query_one("#extend-timestamp", Checkbox).value = self._extend_timestamp
        if self._extend_keep_segments is not None:
            self.query_one("#extend-keep-segments", Checkbox).value = self._extend_keep_segments
        if self._extend_continue_on_error is not None:
            self.query_one("#extend-continue-on-error", Checkbox).value = (
                self._extend_continue_on_error
            )
        if self._extend_upscale is not None:
            self.query_one("#extend-upscale", Checkbox).value = self._extend_upscale
        if self._extend_upscale_model is not None:
            self.query_one("#extend-upscale-model", Select).value = self._extend_upscale_model
        if self._extend_upscale_scale is not None:
            self.query_one("#extend-upscale-scale", CopyInput).value = str(
                self._extend_upscale_scale
            )
        if self._extend_realesrgan_bin is not None:
            self.query_one("#extend-realesrgan-bin", CopyInput).value = self._extend_realesrgan_bin
        if self._extend_models_dir is not None:
            self.query_one("#extend-models-dir", CopyInput).value = self._extend_models_dir
        self._refresh_extend_preview()

    def _refresh_extend_preview(self) -> None:
        self.query_one("#extend-command-preview", Static).update(
            extend_first_segment_command_preview()
        )

    def apply_last_extend(self, last_run: GenerateOptions) -> None:
        self.query_one("#extend-output", CopyInput).value = extended_output_path(
            last_run.output
        )
        self._refresh_extend_preview()
        self._set_status("Applied last run to extend preview and default output.")

    def _start_extend_run(self) -> None:
        self._clear_validation_highlights()
        if load_last_run() is None:
            self._set_status(
                "No saved generate settings. Use the Generate tab and press Run once first."
            )
            return

        length_text = self.query_one("#extend-length", CopyInput).value.strip()
        if not length_text:
            self._set_validation_highlights(["#extend-length"])
            self.query_one("#extend-length").focus()
            self._set_status("Target duration is required.")
            return
        try:
            target_duration = parse_target_duration(length_text)
        except ValueError as exc:
            self._set_validation_highlights(["#extend-length"])
            self.query_one("#extend-length").focus()
            self._set_status(str(exc))
            return

        retries = self._parse_positive_int(
            self.query_one("#extend-retries", CopyInput).value,
            field="Retries per segment",
            widget_id="#extend-retries",
        )
        if retries is None:
            return

        count = self._parse_positive_int(
            self.query_one("#extend-count", CopyInput).value,
            field="Number of extended videos",
            widget_id="#extend-count",
        )
        if count is None:
            return

        upscale_scale_text = self.query_one("#extend-upscale-scale", CopyInput).value
        try:
            upscale_scale = self._parse_optional_scale(
                upscale_scale_text,
                widget_id="#extend-upscale-scale",
            )
        except ValueError:
            return

        output_text = self.query_one("#extend-output", CopyInput).value.strip()
        realesrgan_bin = self.query_one("#extend-realesrgan-bin", CopyInput).value.strip()
        models_dir = self.query_one("#extend-models-dir", CopyInput).value.strip()

        self._pending_run = ExtendRun(
            target_duration=target_duration,
            max_retries=retries,
            count=count,
            final_output=output_text or None,
            timestamp=self.query_one("#extend-timestamp", Checkbox).value,
            keep_segments=self.query_one("#extend-keep-segments", Checkbox).value,
            continue_on_error=self.query_one("#extend-continue-on-error", Checkbox).value,
            upscale=self.query_one("#extend-upscale", Checkbox).value,
            upscale_model=str(self.query_one("#extend-upscale-model", Select).value),
            upscale_scale=upscale_scale,
            realesrgan_bin=realesrgan_bin or None,
            models_dir=models_dir or None,
        )
        self.exit()
