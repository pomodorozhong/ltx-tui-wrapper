"""Generate tab for the ltx-tui application."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Collapsible, Label, Select, Static

from ltx_tui_wrapper.last_run import load_last_run, save_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.parsing import build_command_argv, format_command
from ltx_tui_wrapper.tui.constants import (
    FRAME_RATE_PRESETS,
    INVALID_CLASS,
    MODEL_PRESETS,
    PIPELINE_MODE_PRESETS,
    RESOLUTION_PRESETS,
)
from ltx_tui_wrapper.tui.run_actions import GenerateRun
from ltx_tui_wrapper.tui.tabs.shared import TabMixinBase
from ltx_tui_wrapper.tui.widgets import CopyInput, CopyTextArea


class GenerateTabMixin(TabMixinBase):
    """Compose, events, and run logic for the Generate tab."""

    def _compose_generate_tab(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Prompt", classes="field-label")
            yield CopyInput(
                placeholder="a sunset over the ocean",
                id="prompt",
            )

            yield Label("Output video", classes="field-label")
            with Horizontal(classes="field-row"):
                yield CopyInput(
                    placeholder="output.mp4",
                    id="output-path",
                )
                yield Button("Browse…", id="browse-output")

            yield Label("Pipeline mode", classes="field-label")
            yield Select(
                PIPELINE_MODE_PRESETS,
                id="pipeline-mode",
                value="two_stage",
            )

            yield Label("Frame rate", classes="field-label")
            yield Static(
                "LTX-2.3 was trained at 24 fps; other values may drift out of distribution.",
                classes="field-hint",
            )
            yield Select(FRAME_RATE_PRESETS, id="frame-rate-preset", value="24")
            yield CopyInput(
                placeholder="e.g. 24",
                id="frame-rate",
                classes="hidden-custom",
            )

            with Collapsible(title="Video size & length", collapsed=False):
                yield Label("Resolution", classes="field-label")
                yield Select(RESOLUTION_PRESETS, id="resolution-preset", value="480x704")
                with Horizontal(classes="resolution-row"):
                    yield CopyInput(value="480", id="height", disabled=True)
                    yield Static("×", classes="field-label")
                    yield CopyInput(value="704", id="width", disabled=True)
                yield Label("Frames", classes="field-label")
                yield CopyInput(value="97", id="frames")

            with Collapsible(title="Image-to-video (optional)", collapsed=True):
                yield Label("Reference image", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield CopyInput(
                        placeholder="photo.jpg",
                        id="image-path",
                    )
                    yield Button("Browse…", id="browse-image")
                yield Label("Frame index / strength / CRF (optional)", classes="field-label")
                yield Static(
                    "Leave defaults for legacy single-image I2V (frame 0, strength 1.0).",
                    classes="field-hint",
                )
                with Horizontal(classes="field-row"):
                    yield CopyInput(value="0", id="image-frame-idx", placeholder="frame idx")
                    yield CopyInput(value="1.0", id="image-strength", placeholder="strength")
                    yield CopyInput(id="image-crf", placeholder="CRF")
                yield Label("Additional image specs (one per line)", classes="field-label")
                yield Static(
                    "Format: PATH or PATH FRAME_IDX STRENGTH [CRF]",
                    classes="field-hint",
                )
                yield CopyTextArea(id="extra-images")

            with Collapsible(title="Sampler & guidance", collapsed=True):
                yield Label("One-stage steps (--steps)", classes="field-label")
                yield CopyInput(placeholder="default: 8", id="steps")
                yield Label("Stage 1 / stage 2 steps", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield CopyInput(placeholder="stage 1", id="stage1-steps")
                    yield CopyInput(placeholder="stage 2 (default 3)", id="stage2-steps")
                yield Label("CFG / STG scale", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield CopyInput(placeholder="CFG (default 3.0)", id="cfg-scale")
                    yield CopyInput(placeholder="STG", id="stg-scale")
                yield Checkbox("Enhance prompt with Gemma", id="enhance-prompt")

            with Collapsible(title="Two-stage options", collapsed=True):
                yield Label("Dev transformer", classes="field-label")
                yield CopyInput(
                    value="transformer-dev.safetensors",
                    id="dev-transformer",
                )
                yield Label("Distilled LoRA", classes="field-label")
                yield CopyInput(
                    value="ltx-2.3-22b-distilled-lora-384.safetensors",
                    id="distilled-lora",
                )
                yield Label("Distilled LoRA strength", classes="field-label")
                yield CopyInput(value="1.0", id="distilled-lora-strength")
                yield Checkbox("Enable TeaCache (two-stage only)", id="enable-teacache")
                yield Label("TeaCache threshold", classes="field-label")
                yield CopyInput(placeholder="default: 0.5", id="teacache-thresh")

            with Collapsible(title="LoRA weights (optional)", collapsed=True):
                yield Static(
                    "One LoRA per line: PATH STRENGTH",
                    classes="field-hint",
                )
                yield CopyTextArea(id="lora-specs")

            with Collapsible(title="Model & memory", collapsed=True):
                yield Label("Model", classes="field-label")
                yield Select(MODEL_PRESETS, id="model", value="dgrauet/ltx-2.3-mlx-q8")
                yield Label("Gemma encoder", classes="field-label")
                yield CopyInput(
                    value="mlx-community/gemma-3-12b-it-4bit",
                    id="gemma",
                )
                yield Label("Seed (-1 = random)", classes="field-label")
                yield CopyInput(value="-1", id="seed")
                yield Checkbox("Low RAM streaming (--low-ram)", id="low-ram")
                yield Checkbox("Quiet (--quiet)", id="quiet")
                yield Label("Tiling", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield CopyInput(value="1", id="tile-frames", placeholder="tile frames")
                    yield CopyInput(value="1", id="tile-spatial", placeholder="tile spatial")
                    yield CopyInput(value="2", id="tile-overlap", placeholder="overlap")

        yield Static("", id="command-preview")

    def _mount_generate_tab(self) -> None:
        if self._initial_prompt:
            self.query_one("#prompt", CopyInput).value = self._initial_prompt
        if self._initial_output is not None:
            self.query_one("#output-path", CopyInput).value = str(self._initial_output)
        if self._initial_image is not None:
            self.query_one("#image-path", CopyInput).value = str(self._initial_image)

        self._form.sync_custom_visibility("#frame-rate-preset", "#frame-rate")
        self._form.sync_resolution_visibility()
        self._last_run_options = load_last_run()
        self._set_last_run_available(self._last_run_options is not None)
        self._refresh_generate_preview()

    def _remember_last_run(self, options: GenerateOptions) -> None:
        self._last_run_options = options
        save_last_run(options)
        self._set_last_run_available(True)
        self._refresh_batch_preview()
        self._refresh_extend_preview()

    def _refresh_generate_preview(self) -> None:
        options = self._form.try_collect_for_preview()
        if options is None or not options.prompt or not options.output:
            self.query_one("#command-preview", Static).update("")
            return
        self.query_one("#command-preview", Static).update(format_command(options))

    def apply_last_generate(self, last_run: GenerateOptions) -> None:
        self._form.apply(last_run)
        self._form.sync_custom_visibility("#frame-rate-preset", "#frame-rate")
        self._form.sync_resolution_visibility()
        self._refresh_generate_preview()
        self._set_status("Applied settings from last run.")

    @on(CopyInput.Changed)
    def input_changed(self, event: CopyInput.Changed) -> None:
        event.input.remove_class(INVALID_CLASS)
        if self._active_tab() == "generate":
            self._refresh_generate_preview()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        event.select.remove_class(INVALID_CLASS)
        if self._active_tab() == "generate":
            self._refresh_generate_preview()

    @on(Checkbox.Changed)
    @on(CopyTextArea.Changed)
    def form_changed(self) -> None:
        if self._active_tab() == "generate":
            self._refresh_generate_preview()

    @on(Select.Changed, "#frame-rate-preset")
    def frame_rate_preset_changed(self) -> None:
        self._form.sync_custom_visibility("#frame-rate-preset", "#frame-rate")

    @on(Select.Changed, "#resolution-preset")
    def resolution_preset_changed(self) -> None:
        self._form.sync_resolution_visibility()

    @on(Button.Pressed, "#browse-output")
    def browse_output(self) -> None:
        start_dir, default_name = self._form.browse_save_defaults()
        self._browse_into_input(
            "#output-path",
            start_dir,
            save=True,
            default_name=default_name,
        )

    @on(Button.Pressed, "#browse-image")
    def browse_image(self) -> None:
        from ltx_tui_wrapper.file_dialog import IMAGE_EXTENSIONS

        self._browse_into_input(
            "#image-path",
            self._form.browse_start_dir("#image-path"),
            extensions=IMAGE_EXTENSIONS,
        )

    def _start_generate_run(self) -> None:
        result = self._validator.validate()
        if not result.ok:
            self._set_validation_highlights(result.highlight_widget_ids)
            if result.highlight_widget_ids:
                self.query_one(result.highlight_widget_ids[0]).focus()
            self._set_status(result.error_message or "")
            return

        self._clear_validation_highlights()
        options = self._form.collect()
        self._remember_last_run(options)
        self._pending_run = GenerateRun(
            command=build_command_argv(options),
            options=options,
        )
        self.exit()
