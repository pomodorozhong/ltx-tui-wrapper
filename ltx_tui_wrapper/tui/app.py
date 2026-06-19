"""Main Textual application for ltx-2-mlx generate."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    RichLog,
    Select,
    Static,
    TextArea,
)

from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.parsing import GenerateParseError, format_command, invoke
from ltx_tui_wrapper.tui.constants import (
    APP_CSS,
    FRAME_RATE_PRESETS,
    HIGHLIGHTABLE_IDS,
    INVALID_CLASS,
    MODEL_PRESETS,
    PIPELINE_MODE_PRESETS,
    RESOLUTION_PRESETS,
)
from ltx_tui_wrapper.tui.form import GenerateForm
from ltx_tui_wrapper.tui.run_output import capture_stdio
from ltx_tui_wrapper.tui.run_progress import RunProgressController, format_elapsed
from ltx_tui_wrapper.tui.screens import FilePickScreen
from ltx_tui_wrapper.tui.validator import GenerateFormValidator

GenerateRunner = Callable[[GenerateOptions], None]


def _default_runner(options: GenerateOptions) -> None:
    from ltx_pipelines_mlx.cli import _cmd_generate

    invoke(_cmd_generate, **options.to_kwargs())


class GenerateApp(App[None]):
    """Form-driven builder for ``ltx-2-mlx generate``."""

    TITLE = "ltx-tui generate"
    CSS = APP_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+r", "run", "Run"),
    ]

    def __init__(
        self,
        *,
        initial_prompt: str | None = None,
        initial_output: Path | None = None,
        initial_image: Path | None = None,
        runner: GenerateRunner | None = None,
    ) -> None:
        super().__init__()
        self._initial_prompt = initial_prompt
        self._initial_output = initial_output
        self._initial_image = initial_image
        self._runner = runner or _default_runner
        self._form = GenerateForm(self)
        self._validator = GenerateFormValidator(self._form)
        self._progress = RunProgressController(self)

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Label("Prompt", classes="field-label")
            yield Input(
                placeholder="a sunset over the ocean",
                id="prompt",
            )

            yield Label("Output video", classes="field-label")
            with Horizontal(classes="field-row"):
                yield Input(
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
            yield Input(
                placeholder="e.g. 24",
                id="frame-rate",
                classes="hidden-custom",
            )

            with Collapsible(title="Video size & length", collapsed=False):
                yield Label("Resolution", classes="field-label")
                yield Select(RESOLUTION_PRESETS, id="resolution-preset", value="480x704")
                with Horizontal(classes="resolution-row"):
                    yield Input(value="480", id="height", disabled=True)
                    yield Static("×", classes="field-label")
                    yield Input(value="704", id="width", disabled=True)
                yield Label("Frames", classes="field-label")
                yield Input(value="97", id="frames")

            with Collapsible(title="Image-to-video (optional)", collapsed=True):
                yield Label("Reference image", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield Input(
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
                    yield Input(value="0", id="image-frame-idx", placeholder="frame idx")
                    yield Input(value="1.0", id="image-strength", placeholder="strength")
                    yield Input(id="image-crf", placeholder="CRF")
                yield Label("Additional image specs (one per line)", classes="field-label")
                yield Static(
                    "Format: PATH or PATH FRAME_IDX STRENGTH [CRF]",
                    classes="field-hint",
                )
                yield TextArea(id="extra-images")

            with Collapsible(title="Sampler & guidance", collapsed=True):
                yield Label("One-stage steps (--steps)", classes="field-label")
                yield Input(placeholder="default: 8", id="steps")
                yield Label("Stage 1 / stage 2 steps", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield Input(placeholder="stage 1", id="stage1-steps")
                    yield Input(placeholder="stage 2 (default 3)", id="stage2-steps")
                yield Label("CFG / STG scale", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield Input(placeholder="CFG (default 3.0)", id="cfg-scale")
                    yield Input(placeholder="STG", id="stg-scale")
                yield Checkbox("Enhance prompt with Gemma", id="enhance-prompt")

            with Collapsible(title="Two-stage options", collapsed=True):
                yield Label("Dev transformer", classes="field-label")
                yield Input(
                    value="transformer-dev.safetensors",
                    id="dev-transformer",
                )
                yield Label("Distilled LoRA", classes="field-label")
                yield Input(
                    value="ltx-2.3-22b-distilled-lora-384.safetensors",
                    id="distilled-lora",
                )
                yield Label("Distilled LoRA strength", classes="field-label")
                yield Input(value="1.0", id="distilled-lora-strength")
                yield Checkbox("Enable TeaCache (two-stage only)", id="enable-teacache")
                yield Label("TeaCache threshold", classes="field-label")
                yield Input(placeholder="default: 0.5", id="teacache-thresh")

            with Collapsible(title="LoRA weights (optional)", collapsed=True):
                yield Static(
                    "One LoRA per line: PATH STRENGTH",
                    classes="field-hint",
                )
                yield TextArea(id="lora-specs")

            with Collapsible(title="Model & memory", collapsed=True):
                yield Label("Model", classes="field-label")
                yield Select(MODEL_PRESETS, id="model", value="dgrauet/ltx-2.3-mlx-q8")
                yield Label("Gemma encoder", classes="field-label")
                yield Input(
                    value="mlx-community/gemma-3-12b-it-4bit",
                    id="gemma",
                )
                yield Label("Seed (-1 = random)", classes="field-label")
                yield Input(value="-1", id="seed")
                yield Checkbox("Low RAM streaming (--low-ram)", id="low-ram")
                yield Checkbox("Quiet (--quiet)", id="quiet")
                yield Label("Tiling", classes="field-label")
                with Horizontal(classes="field-row"):
                    yield Input(value="1", id="tile-frames", placeholder="tile frames")
                    yield Input(value="1", id="tile-spatial", placeholder="tile spatial")
                    yield Input(value="2", id="tile-overlap", placeholder="overlap")

        yield Static("", id="command-preview")
        with Container(id="run-panel"):
            with Horizontal(classes="run-progress-row", id="run-header"):
                yield LoadingIndicator(id="run-spinner")
                with Vertical(classes="run-progress-text"):
                    yield Static("Generating video…", id="run-message")
                    yield Static("Elapsed: 0s", id="run-timer")
            yield RichLog(
                id="run-output",
                max_lines=1000,
                wrap=True,
                highlight=False,
                markup=False,
            )
        yield Static("", id="status")
        with Horizontal(id="action-row"):
            yield Button("Run", variant="primary", id="run")
            yield Button("Quit", id="quit")
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_prompt:
            self.query_one("#prompt", Input).value = self._initial_prompt
        if self._initial_output is not None:
            self.query_one("#output-path", Input).value = str(self._initial_output)
        if self._initial_image is not None:
            self.query_one("#image-path", Input).value = str(self._initial_image)
        self._form.sync_custom_visibility("#frame-rate-preset", "#frame-rate")
        self._form.sync_resolution_visibility()
        self._progress.on_mount()
        self._refresh_command_preview()

    def _append_run_output(self, line: str) -> None:
        self.query_one("#run-output", RichLog).write(line)

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _refresh_command_preview(self) -> None:
        options = self._form.try_collect_for_preview()
        if options is None or not options.prompt or not options.output:
            self.query_one("#command-preview", Static).update("")
            return
        self.query_one("#command-preview", Static).update(format_command(options))

    def _clear_validation_highlights(self) -> None:
        for widget_id in HIGHLIGHTABLE_IDS:
            widget = self.query(widget_id).first()
            if widget is not None:
                widget.remove_class(INVALID_CLASS)

    def _set_validation_highlights(self, widget_ids: list[str]) -> None:
        self._clear_validation_highlights()
        for widget_id in widget_ids:
            self.query_one(widget_id).add_class(INVALID_CLASS)

    @on(Input.Changed)
    def input_changed(self, event: Input.Changed) -> None:
        event.input.remove_class(INVALID_CLASS)
        self._refresh_command_preview()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        event.select.remove_class(INVALID_CLASS)
        self._refresh_command_preview()

    @on(Checkbox.Changed)
    @on(TextArea.Changed)
    def form_changed(self) -> None:
        self._refresh_command_preview()

    @on(Select.Changed, "#frame-rate-preset")
    def frame_rate_preset_changed(self) -> None:
        self._form.sync_custom_visibility("#frame-rate-preset", "#frame-rate")

    @on(Select.Changed, "#resolution-preset")
    def resolution_preset_changed(self) -> None:
        self._form.sync_resolution_visibility()

    @work(exclusive=True)
    async def _browse_into_input(
        self,
        input_id: str,
        start: Path,
        *,
        save: bool = False,
    ) -> None:
        if save:
            start_dir, default_name = self._form.browse_save_defaults()
            picked = await self.push_screen_wait(FilePickScreen(start=start_dir))
            if picked is None:
                return
            if picked.is_dir():
                picked = picked / default_name
            self.query_one(input_id, Input).value = str(picked)
        else:
            picked = await self.push_screen_wait(FilePickScreen(start=start))
            if picked is not None:
                self.query_one(input_id, Input).value = str(picked)

    @on(Button.Pressed, "#browse-output")
    def browse_output(self) -> None:
        self._browse_into_input(
            "#output-path",
            self._form.browse_start_dir("#output-path"),
            save=True,
        )

    @on(Button.Pressed, "#browse-image")
    def browse_image(self) -> None:
        self._browse_into_input(
            "#image-path",
            self._form.browse_start_dir("#image-path"),
        )

    @on(Button.Pressed, "#quit")
    def quit_pressed(self) -> None:
        self.exit()

    def action_run(self) -> None:
        self.query_one("#run", Button).press()

    @on(Button.Pressed, "#run")
    def run_pressed(self) -> None:
        self._start_run()

    def _start_run(self) -> None:
        result = self._validator.validate()
        if not result.ok:
            self._set_validation_highlights(result.highlight_widget_ids)
            if result.highlight_widget_ids:
                self.query_one(result.highlight_widget_ids[0]).focus()
            self._set_status(result.error_message or "")
            return

        self._clear_validation_highlights()
        self.query_one("#run", Button).disabled = True
        self.query_one("#quit", Button).disabled = True
        self._set_status("")
        options = self._form.collect()
        self.query_one("#command-preview", Static).update(format_command(options))
        self._progress.clear_output()
        self._progress.show()
        self._run_job_worker(options)

    @work(thread=True, exclusive=True)
    def _run_job_worker(self, options: GenerateOptions) -> None:
        append = lambda line: self.call_from_thread(self._append_run_output, line)
        try:
            with capture_stdio(append):
                self._runner(options)
        except SystemExit as exc:
            message = str(exc.code) if exc.code not in (None, 0, 1) else "Generation failed."
            if exc.code == 0:
                self.call_from_thread(self._on_run_done, options.output)
                return
            self.call_from_thread(self._on_run_failed, message)
            return
        except (GenerateParseError, ValueError, OSError) as exc:
            self.call_from_thread(self._on_run_failed, str(exc))
            return
        self.call_from_thread(self._on_run_done, options.output)

    def _finish_run(self, message: str) -> None:
        elapsed = self._progress.capture_elapsed()
        self._progress.finish()
        if elapsed is not None:
            message = f"{message} in {format_elapsed(elapsed)}"
        self.query_one("#run-message", Static).update(message)
        self._set_status(message)
        self.query_one("#run", Button).disabled = False
        self.query_one("#quit", Button).disabled = False

    def _on_run_done(self, output_path: str) -> None:
        self._finish_run(f"Saved {output_path}")

    def _on_run_failed(self, message: str) -> None:
        self._finish_run(message)


def run_generate_tui(
    *,
    prompt: str | None = None,
    output: Path | None = None,
    image: Path | None = None,
    runner: GenerateRunner | None = None,
) -> None:
    """Launch the generate command builder TUI."""
    app = GenerateApp(
        initial_prompt=prompt,
        initial_output=output,
        initial_image=image,
        runner=runner,
    )
    app.run()
