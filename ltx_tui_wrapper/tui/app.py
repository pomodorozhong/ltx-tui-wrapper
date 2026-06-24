"""Main Textual application for ltx-tui."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Static, TabbedContent, TabPane

from ltx_tui_wrapper.file_dialog import (
    native_file_dialog_available,
    pick_open_file,
    pick_save_file,
)
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.tui.constants import APP_CSS, TAB_IDS
from ltx_tui_wrapper.tui.form import GenerateForm
from ltx_tui_wrapper.tui.run_actions import RunAction, TabId, execute_run_action
from ltx_tui_wrapper.tui.screens import FilePickScreen
from ltx_tui_wrapper.tui.tabs import (
    BatchTabMixin,
    ExtendTabMixin,
    GenerateTabMixin,
    TabHelpersMixin,
    UpscaleTabMixin,
)
from ltx_tui_wrapper.tui.validator import GenerateFormValidator
from ltx_tui_wrapper.tui.widgets import CopyInput


class LtxTuiApp(
    TabHelpersMixin,
    GenerateTabMixin,
    BatchTabMixin,
    ExtendTabMixin,
    UpscaleTabMixin,
    App[None],
):
    """Tabbed builder for generate, batch, extend, and upscale commands."""

    TITLE = "ltx-tui"
    CSS = APP_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+r", "run", "Run"),
        ("ctrl+1", "show_tab_generate", "Generate"),
        ("ctrl+2", "show_tab_batch", "Batch"),
        ("ctrl+3", "show_tab_extend", "Extend"),
        ("ctrl+4", "show_tab_upscale", "Upscale"),
    ]

    def __init__(
        self,
        *,
        initial_tab: TabId = "generate",
        initial_prompt: str | None = None,
        initial_output: Path | None = None,
        initial_image: Path | None = None,
        batch_count: int | None = None,
        batch_retries: int | None = None,
        batch_continue_on_error: bool | None = None,
        extend_length: str | None = None,
        extend_retries: int | None = None,
        extend_count: int | None = None,
        extend_output: str | None = None,
        extend_timestamp: bool | None = None,
        extend_keep_segments: bool | None = None,
        extend_continue_on_error: bool | None = None,
        extend_upscale: bool | None = None,
        extend_upscale_model: str | None = None,
        extend_upscale_scale: int | None = None,
        extend_realesrgan_bin: str | None = None,
        extend_models_dir: str | None = None,
        upscale_input: str | None = None,
        upscale_output: str | None = None,
        upscale_model: str | None = None,
        upscale_scale: int | None = None,
        upscale_realesrgan_bin: str | None = None,
        upscale_models_dir: str | None = None,
        upscale_keep_frames: bool | None = None,
    ) -> None:
        super().__init__()
        self._initial_tab = initial_tab
        self._initial_prompt = initial_prompt
        self._initial_output = initial_output
        self._initial_image = initial_image
        self._prefill_batch_count = batch_count
        self._prefill_batch_retries = batch_retries
        self._prefill_batch_continue_on_error = batch_continue_on_error
        self._extend_length = extend_length
        self._extend_retries = extend_retries
        self._extend_count = extend_count
        self._extend_output = extend_output
        self._extend_timestamp = extend_timestamp
        self._extend_keep_segments = extend_keep_segments
        self._extend_continue_on_error = extend_continue_on_error
        self._extend_upscale = extend_upscale
        self._extend_upscale_model = extend_upscale_model
        self._extend_upscale_scale = extend_upscale_scale
        self._extend_realesrgan_bin = extend_realesrgan_bin
        self._extend_models_dir = extend_models_dir
        self._upscale_input = upscale_input
        self._upscale_output = upscale_output
        self._upscale_model = upscale_model
        self._upscale_scale = upscale_scale
        self._upscale_realesrgan_bin = upscale_realesrgan_bin
        self._upscale_models_dir = upscale_models_dir
        self._upscale_keep_frames = upscale_keep_frames
        self._form = GenerateForm(self)
        self._validator = GenerateFormValidator(self._form)
        self._last_run_options: GenerateOptions | None = None
        self._pending_run: RunAction | None = None

    @property
    def pending_run(self) -> RunAction | None:
        """Command to run after the TUI exits, if the user pressed Run."""
        return self._pending_run

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial=self._initial_tab, id="tabs"):
            with TabPane("Generate", id="generate"):
                yield from self._compose_generate_tab()
            with TabPane("Batch", id="batch"):
                yield from self._compose_batch_tab()
            with TabPane("Extend", id="extend"):
                yield from self._compose_extend_tab()
            with TabPane("Upscale", id="upscale"):
                yield from self._compose_upscale_tab()
        yield Static(
            "Run closes this TUI and executes the command in your terminal.",
            classes="field-hint",
            id="run-hint",
        )
        yield Static("", id="status")
        with Horizontal(id="action-row"):
            yield Button("Run", variant="primary", id="run")
            yield Button("Apply last run", id="apply-last", disabled=True)
            yield Button("Quit", id="quit")
        yield Footer()

    def on_mount(self) -> None:
        self._mount_generate_tab()
        self._mount_batch_tab()
        self._mount_extend_tab()
        self._mount_upscale_tab()

    def _active_tab(self) -> TabId:
        active = self.query_one("#tabs", TabbedContent).active
        if active in TAB_IDS:
            return active  # type: ignore[return-value]
        return "generate"

    def _show_tab(self, tab_id: TabId) -> None:
        self.query_one("#tabs", TabbedContent).active = tab_id

    def action_show_tab_generate(self) -> None:
        self._show_tab("generate")

    def action_show_tab_batch(self) -> None:
        self._show_tab("batch")

    def action_show_tab_extend(self) -> None:
        self._show_tab("extend")

    def action_show_tab_upscale(self) -> None:
        self._show_tab("upscale")

    @on(TabbedContent.TabActivated, "#tabs")
    def tab_activated(self) -> None:
        self._set_status("")
        tab = self._active_tab()
        if tab == "batch":
            self._refresh_batch_preview()
        elif tab == "extend":
            self._refresh_extend_preview()

    @work(exclusive=True)
    async def _browse_into_input(
        self,
        input_id: str,
        start: Path,
        *,
        save: bool = False,
        extensions: tuple[str, ...] | None = None,
        default_name: str = "output.mp4",
    ) -> None:
        if save:
            start_dir = start if start.is_dir() else start.parent
            picked = await asyncio.to_thread(
                pick_save_file,
                title="Save output as",
                start=start_dir,
                default_name=default_name,
            )
        else:
            picked = await asyncio.to_thread(
                pick_open_file,
                title="Select file",
                start=start,
                extensions=extensions,
            )
        if picked is None:
            if native_file_dialog_available():
                return
            picked = await self.push_screen_wait(FilePickScreen(start=start))
            if picked is None:
                return
            if save and picked.is_dir():
                picked = picked / default_name
        self.query_one(input_id, CopyInput).value = str(picked)

    def _browse_start_dir(self, input_id: str) -> Path:
        text = self.query_one(input_id, CopyInput).value.strip()
        if text:
            path = Path(text).expanduser()
            if path.is_file():
                return path.parent
            if path.parent.is_dir():
                return path.parent
            if path.is_dir():
                return path
        return Path.home()

    @on(Button.Pressed, "#apply-last")
    def apply_last_pressed(self) -> None:
        last_run = load_last_run()
        if last_run is None:
            self._set_status("No saved generate settings found.")
            return

        self._last_run_options = last_run
        self._set_last_run_available(True)
        self._clear_validation_highlights()
        tab = self._active_tab()
        if tab == "generate":
            self.apply_last_generate(last_run)
        elif tab == "batch":
            self.apply_last_batch()
        elif tab == "extend":
            self.apply_last_extend(last_run)
        else:
            self.apply_last_upscale(last_run)

    @on(Button.Pressed, "#quit")
    def quit_pressed(self) -> None:
        self.exit()

    def action_run(self) -> None:
        self.query_one("#run", Button).press()

    @on(Button.Pressed, "#run")
    def run_pressed(self) -> None:
        tab = self._active_tab()
        if tab == "generate":
            self._start_generate_run()
        elif tab == "batch":
            self._start_batch_run()
        elif tab == "extend":
            self._start_extend_run()
        else:
            self._start_upscale_run()


GenerateApp = LtxTuiApp


def run_ltx_tui(
    *,
    initial_tab: TabId = "generate",
    prompt: str | None = None,
    output: Path | None = None,
    image: Path | None = None,
    batch_count: int | None = None,
    batch_retries: int | None = None,
    batch_continue_on_error: bool | None = None,
    extend_length: str | None = None,
    extend_retries: int | None = None,
    extend_count: int | None = None,
    extend_output: str | None = None,
    extend_timestamp: bool | None = None,
    extend_keep_segments: bool | None = None,
    extend_continue_on_error: bool | None = None,
    extend_upscale: bool | None = None,
    extend_upscale_model: str | None = None,
    extend_upscale_scale: int | None = None,
    extend_realesrgan_bin: str | None = None,
    extend_models_dir: str | None = None,
    upscale_input: str | None = None,
    upscale_output: str | None = None,
    upscale_model: str | None = None,
    upscale_scale: int | None = None,
    upscale_realesrgan_bin: str | None = None,
    upscale_models_dir: str | None = None,
    upscale_keep_frames: bool | None = None,
) -> int:
    """Launch the unified ltx-tui builder.

    Returns the exit code of the built command, or ``0`` if the user quit without running.
    """
    app = LtxTuiApp(
        initial_tab=initial_tab,
        initial_prompt=prompt,
        initial_output=output,
        initial_image=image,
        batch_count=batch_count,
        batch_retries=batch_retries,
        batch_continue_on_error=batch_continue_on_error,
        extend_length=extend_length,
        extend_retries=extend_retries,
        extend_count=extend_count,
        extend_output=extend_output,
        extend_timestamp=extend_timestamp,
        extend_keep_segments=extend_keep_segments,
        extend_continue_on_error=extend_continue_on_error,
        extend_upscale=extend_upscale,
        extend_upscale_model=extend_upscale_model,
        extend_upscale_scale=extend_upscale_scale,
        extend_realesrgan_bin=extend_realesrgan_bin,
        extend_models_dir=extend_models_dir,
        upscale_input=upscale_input,
        upscale_output=upscale_output,
        upscale_model=upscale_model,
        upscale_scale=upscale_scale,
        upscale_realesrgan_bin=upscale_realesrgan_bin,
        upscale_models_dir=upscale_models_dir,
        upscale_keep_frames=upscale_keep_frames,
    )
    app.run()
    if app.pending_run is None:
        return 0
    return execute_run_action(app.pending_run)


def run_generate_tui(
    *,
    prompt: str | None = None,
    output: Path | None = None,
    image: Path | None = None,
) -> int:
    """Launch the generate tab (backward-compatible alias)."""
    return run_ltx_tui(prompt=prompt, output=output, image=image)
