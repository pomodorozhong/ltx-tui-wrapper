"""Upscale tab for the ltx-tui application."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Label, Select, Static

from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.tui.constants import NCNN_MODEL_PRESETS
from ltx_tui_wrapper.tui.run_actions import UpscaleRun
from ltx_tui_wrapper.tui.tabs.shared import TabMixinBase
from ltx_tui_wrapper.tui.widgets import CopyInput
from ltx_tui_wrapper.upscale import AI_SCALES, upscaled_output_path


class UpscaleTabMixin(TabMixinBase):
    """Compose, events, and run logic for the Upscale tab."""

    def _compose_upscale_tab(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "Upscale a video to strict 1920×1080 with letterbox/pillarbox padding.",
                classes="field-hint",
            )
            yield Label("Input video", classes="field-label")
            with Horizontal(classes="field-row"):
                yield CopyInput(
                    placeholder="default: last generate output",
                    id="upscale-input",
                )
                yield Button("Browse…", id="browse-upscale-input")
            yield Label("Output video", classes="field-label")
            with Horizontal(classes="field-row"):
                yield CopyInput(
                    placeholder="default: <input-stem>_1080p.mp4",
                    id="upscale-output",
                )
                yield Button("Browse…", id="browse-upscale-output")
            yield Label("Upscale method", classes="field-label")
            yield Select(
                NCNN_MODEL_PRESETS,
                id="upscale-model",
                value="__lanczos__",
            )
            yield Label("AI scale (optional)", classes="field-label")
            yield CopyInput(
                placeholder=f"auto or one of {', '.join(map(str, AI_SCALES))}",
                id="upscale-scale",
            )
            yield Label("realesrgan-ncnn-vulkan binary (optional)", classes="field-label")
            yield CopyInput(id="upscale-realesrgan-bin")
            yield Label("Models directory (optional)", classes="field-label")
            yield CopyInput(id="upscale-models-dir")
            yield Checkbox("Keep extracted frames (AI only)", id="upscale-keep-frames")

    def _mount_upscale_tab(self) -> None:
        if self._upscale_input is not None:
            self.query_one("#upscale-input", CopyInput).value = self._upscale_input
        if self._upscale_output is not None:
            self.query_one("#upscale-output", CopyInput).value = self._upscale_output
        if self._upscale_model is not None:
            self.query_one("#upscale-model", Select).value = self._upscale_model
        if self._upscale_scale is not None:
            self.query_one("#upscale-scale", CopyInput).value = str(self._upscale_scale)
        if self._upscale_realesrgan_bin is not None:
            self.query_one("#upscale-realesrgan-bin", CopyInput).value = self._upscale_realesrgan_bin
        if self._upscale_models_dir is not None:
            self.query_one("#upscale-models-dir", CopyInput).value = self._upscale_models_dir
        if self._upscale_keep_frames is not None:
            self.query_one("#upscale-keep-frames", Checkbox).value = self._upscale_keep_frames

    def apply_last_upscale(self, last_run: GenerateOptions) -> None:
        self.query_one("#upscale-input", CopyInput).value = last_run.output
        self.query_one("#upscale-output", CopyInput).value = upscaled_output_path(
            last_run.output
        )
        self._set_status("Applied last run output as upscale input.")

    @on(Button.Pressed, "#browse-upscale-input")
    def browse_upscale_input(self) -> None:
        from ltx_tui_wrapper.file_dialog import VIDEO_EXTENSIONS

        self._browse_into_input(
            "#upscale-input",
            self._browse_start_dir("#upscale-input"),
            extensions=VIDEO_EXTENSIONS,
        )

    @on(Button.Pressed, "#browse-upscale-output")
    def browse_upscale_output(self) -> None:
        start = self._browse_start_dir("#upscale-output")
        default_name = "output_1080p.mp4"
        input_text = self.query_one("#upscale-input", CopyInput).value.strip()
        if input_text:
            default_name = f"{Path(input_text).stem}_1080p.mp4"
        self._browse_into_input(
            "#upscale-output",
            start,
            save=True,
            default_name=default_name,
        )

    def _start_upscale_run(self) -> None:
        self._clear_validation_highlights()

        input_text = self.query_one("#upscale-input", CopyInput).value.strip()
        if input_text:
            input_path = Path(input_text).expanduser()
            if not input_path.is_file():
                self._set_validation_highlights(["#upscale-input"])
                self.query_one("#upscale-input").focus()
                self._set_status(f"Input video not found: {input_path}")
                return
        else:
            last_run = load_last_run()
            if last_run is None:
                self._set_status(
                    "No saved generate output. Use Generate first or set an input video."
                )
                return
            input_path = Path(last_run.output)
            if not input_path.is_file():
                self._set_validation_highlights(["#upscale-input"])
                self._set_status(f"Last generate output not found: {input_path}")
                return

        scale_text = self.query_one("#upscale-scale", CopyInput).value
        try:
            scale = self._parse_optional_scale(scale_text, widget_id="#upscale-scale")
        except ValueError:
            return

        model_value = self.query_one("#upscale-model", Select).value
        model = None if model_value in (None, Select.BLANK, "__lanczos__") else str(model_value)

        output_text = self.query_one("#upscale-output", CopyInput).value.strip()
        realesrgan_bin = self.query_one("#upscale-realesrgan-bin", CopyInput).value.strip()
        models_dir = self.query_one("#upscale-models-dir", CopyInput).value.strip()

        self._pending_run = UpscaleRun(
            input_path=input_text or None,
            output_path=output_text or None,
            model=model,
            scale=scale,
            realesrgan_bin=realesrgan_bin or None,
            models_dir=models_dir or None,
            keep_frames=self.query_one("#upscale-keep-frames", Checkbox).value,
        )
        self.exit()
