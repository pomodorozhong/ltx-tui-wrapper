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
from ltx_tui_wrapper.tui.constants import APP_CSS
from ltx_tui_wrapper.tui.form import GenerateForm
from ltx_tui_wrapper.tui.prefill import (
    AppPrefill,
    BatchPrefill,
    ExtendPrefill,
    ExtendFromPrefill,
    GeneratePrefill,
    InspectPrefill,
    UpscalePrefill,
)
from ltx_tui_wrapper.tui.run_actions import RunAction, execute_run_action
from ltx_tui_wrapper.tui.screens import FilePickScreen
from ltx_tui_wrapper.tui.tab_registry import TAB_SPEC_BY_ID, TAB_SPECS, TabId
from ltx_tui_wrapper.tui.tabs import (
    BatchTabMixin,
    ExtendTabMixin,
    ExtendFromTabMixin,
    GenerateTabMixin,
    InspectTabMixin,
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
    ExtendFromTabMixin,
    UpscaleTabMixin,
    InspectTabMixin,
    App[None],
):
    """Tabbed builder for generate, batch, extend, and upscale commands."""

    TITLE = "ltx-tui"
    CSS = APP_CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+r", "run", "Run"),
        *[(spec.hotkey, f"show_tab('{spec.id}')", spec.title) for spec in TAB_SPECS],
    ]

    def __init__(
        self,
        *,
        prefill: AppPrefill | None = None,
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
        extend_from_input: str | None = None,
        extend_from_length: str | None = None,
        extend_from_retries: int | None = None,
        extend_from_output: str | None = None,
        extend_from_keep_segments: bool | None = None,
        extend_from_continue_on_error: bool | None = None,
        extend_from_upscale: bool | None = None,
        extend_from_upscale_model: str | None = None,
        extend_from_upscale_scale: int | None = None,
        extend_from_realesrgan_bin: str | None = None,
        extend_from_models_dir: str | None = None,
        extend_from_frames: int | None = None,
        extend_from_regenerate_base: bool | None = None,
        extend_from_random_seed: bool | None = None,
        upscale_input: str | None = None,
        upscale_output: str | None = None,
        upscale_model: str | None = None,
        upscale_scale: int | None = None,
        upscale_realesrgan_bin: str | None = None,
        upscale_models_dir: str | None = None,
        upscale_keep_frames: bool | None = None,
        inspect_input: str | None = None,
    ) -> None:
        super().__init__()
        if prefill is None:
            prefill = AppPrefill(
                initial_tab=initial_tab,
                generate=GeneratePrefill(
                    prompt=initial_prompt,
                    output=initial_output,
                    image=initial_image,
                ),
                batch=BatchPrefill(
                    count=batch_count,
                    retries=batch_retries,
                    continue_on_error=batch_continue_on_error,
                ),
                extend=ExtendPrefill(
                    length=extend_length,
                    retries=extend_retries,
                    count=extend_count,
                    output=extend_output,
                    timestamp=extend_timestamp,
                    keep_segments=extend_keep_segments,
                    continue_on_error=extend_continue_on_error,
                    upscale=extend_upscale,
                    upscale_model=extend_upscale_model,
                    upscale_scale=extend_upscale_scale,
                    realesrgan_bin=extend_realesrgan_bin,
                    models_dir=extend_models_dir,
                ),
                extend_from=ExtendFromPrefill(
                    input_path=extend_from_input,
                    length=extend_from_length,
                    retries=extend_from_retries,
                    output=extend_from_output,
                    keep_segments=extend_from_keep_segments,
                    continue_on_error=extend_from_continue_on_error,
                    upscale=extend_from_upscale,
                    upscale_model=extend_from_upscale_model,
                    upscale_scale=extend_from_upscale_scale,
                    realesrgan_bin=extend_from_realesrgan_bin,
                    models_dir=extend_from_models_dir,
                    frames=extend_from_frames,
                    regenerate_base=extend_from_regenerate_base,
                    random_seed=extend_from_random_seed,
                ),
                upscale=UpscalePrefill(
                    input=upscale_input,
                    output=upscale_output,
                    model=upscale_model,
                    scale=upscale_scale,
                    realesrgan_bin=upscale_realesrgan_bin,
                    models_dir=upscale_models_dir,
                    keep_frames=upscale_keep_frames,
                ),
                inspect=InspectPrefill(input=inspect_input),
            )
        self._initial_tab = prefill.initial_tab
        self._initial_prompt = prefill.generate.prompt
        self._initial_output = prefill.generate.output
        self._initial_image = prefill.generate.image
        self._prefill_batch_count = prefill.batch.count
        self._prefill_batch_retries = prefill.batch.retries
        self._prefill_batch_continue_on_error = prefill.batch.continue_on_error
        self._extend_length = prefill.extend.length
        self._extend_retries = prefill.extend.retries
        self._extend_count = prefill.extend.count
        self._extend_output = prefill.extend.output
        self._extend_timestamp = prefill.extend.timestamp
        self._extend_keep_segments = prefill.extend.keep_segments
        self._extend_continue_on_error = prefill.extend.continue_on_error
        self._extend_upscale = prefill.extend.upscale
        self._extend_upscale_model = prefill.extend.upscale_model
        self._extend_upscale_scale = prefill.extend.upscale_scale
        self._extend_realesrgan_bin = prefill.extend.realesrgan_bin
        self._extend_models_dir = prefill.extend.models_dir
        self._extend_from_input = prefill.extend_from.input_path
        self._extend_from_length = prefill.extend_from.length
        self._extend_from_retries = prefill.extend_from.retries
        self._extend_from_output = prefill.extend_from.output
        self._extend_from_keep_segments = prefill.extend_from.keep_segments
        self._extend_from_continue_on_error = prefill.extend_from.continue_on_error
        self._extend_from_upscale = prefill.extend_from.upscale
        self._extend_from_upscale_model = prefill.extend_from.upscale_model
        self._extend_from_upscale_scale = prefill.extend_from.upscale_scale
        self._extend_from_realesrgan_bin = prefill.extend_from.realesrgan_bin
        self._extend_from_models_dir = prefill.extend_from.models_dir
        self._extend_from_frames = prefill.extend_from.frames
        self._extend_from_regenerate_base = prefill.extend_from.regenerate_base
        self._extend_from_random_seed = prefill.extend_from.random_seed
        self._upscale_input = prefill.upscale.input
        self._upscale_output = prefill.upscale.output
        self._upscale_model = prefill.upscale.model
        self._upscale_scale = prefill.upscale.scale
        self._upscale_realesrgan_bin = prefill.upscale.realesrgan_bin
        self._upscale_models_dir = prefill.upscale.models_dir
        self._upscale_keep_frames = prefill.upscale.keep_frames
        self._inspect_input = prefill.inspect.input
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
            for spec in TAB_SPECS:
                with TabPane(spec.title, id=spec.id):
                    yield from getattr(self, spec.compose_method)()
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
        for spec in TAB_SPECS:
            getattr(self, spec.mount_method)()
        self._update_tab_actions()

    def _update_tab_actions(self) -> None:
        spec = TAB_SPEC_BY_ID[self._active_tab()]
        run_button = self.query_one("#run", Button)
        run_hint = self.query_one("#run-hint", Static)
        if spec.run_enabled:
            run_button.disabled = False
            run_hint.update(
                "Run closes this TUI and executes the command in your terminal."
            )
        else:
            run_button.disabled = True
            run_hint.update(
                "Select a video to view its embedded ltx-tui command metadata."
            )

    def _active_tab(self) -> TabId:
        active = self.query_one("#tabs", TabbedContent).active
        if active in TAB_SPEC_BY_ID:
            return active  # type: ignore[return-value]
        return "generate"

    def _show_tab(self, tab_id: TabId) -> None:
        self.query_one("#tabs", TabbedContent).active = tab_id

    def action_show_tab(self, tab_id: str) -> None:
        if tab_id in TAB_SPEC_BY_ID:
            self._show_tab(tab_id)  # type: ignore[arg-type]

    @on(TabbedContent.TabActivated, "#tabs")
    def tab_activated(self) -> None:
        self._set_status("")
        self._update_tab_actions()
        spec = TAB_SPEC_BY_ID[self._active_tab()]
        if spec.activate_method:
            getattr(self, spec.activate_method)()

    @work(exclusive=True)
    async def _browse_into_input(
        self,
        input_id: str,
        start: Path,
        *,
        save: bool = False,
        extensions: tuple[str, ...] | None = None,
        default_name: str = "output.mp4",
        allow_directory: bool = False,
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
            picked = await self.push_screen_wait(
                FilePickScreen(start=start, allow_directory=allow_directory)
            )
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
        spec = TAB_SPEC_BY_ID[self._active_tab()]
        if spec.apply_last_method is None:
            self._set_status(f"Apply last run is not available for {spec.title}.")
            return
        if spec.apply_last_needs_last_run and last_run is None:
            self._set_status("No saved generate settings found.")
            return

        if last_run is not None:
            self._last_run_options = last_run
            self._set_last_run_available(True)
        self._clear_validation_highlights()
        apply_last = getattr(self, spec.apply_last_method)
        if spec.apply_last_needs_last_run:
            apply_last(last_run)
            return
        apply_last()

    @on(Button.Pressed, "#quit")
    def quit_pressed(self) -> None:
        self.exit()

    def action_run(self) -> None:
        spec = TAB_SPEC_BY_ID[self._active_tab()]
        if not spec.run_enabled:
            return
        self.query_one("#run", Button).press()

    @on(Button.Pressed, "#run")
    def run_pressed(self) -> None:
        spec = TAB_SPEC_BY_ID[self._active_tab()]
        if not spec.run_enabled:
            return
        getattr(self, spec.start_run_method)()


GenerateApp = LtxTuiApp


def run_ltx_tui(
    *,
    prefill: AppPrefill | None = None,
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
    extend_from_input: str | None = None,
    extend_from_length: str | None = None,
    extend_from_retries: int | None = None,
    extend_from_output: str | None = None,
    extend_from_keep_segments: bool | None = None,
    extend_from_continue_on_error: bool | None = None,
    extend_from_upscale: bool | None = None,
    extend_from_upscale_model: str | None = None,
    extend_from_upscale_scale: int | None = None,
    extend_from_realesrgan_bin: str | None = None,
    extend_from_models_dir: str | None = None,
    extend_from_frames: int | None = None,
    extend_from_regenerate_base: bool | None = None,
    extend_from_random_seed: bool | None = None,
    upscale_input: str | None = None,
    upscale_output: str | None = None,
    upscale_model: str | None = None,
    upscale_scale: int | None = None,
    upscale_realesrgan_bin: str | None = None,
    upscale_models_dir: str | None = None,
    upscale_keep_frames: bool | None = None,
    inspect_input: str | None = None,
) -> int:
    """Launch the unified ltx-tui builder.

    Returns the exit code of the built command, or ``0`` if the user quit without running.
    """
    app = LtxTuiApp(
        prefill=prefill,
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
        extend_from_input=extend_from_input,
        extend_from_length=extend_from_length,
        extend_from_retries=extend_from_retries,
        extend_from_output=extend_from_output,
        extend_from_keep_segments=extend_from_keep_segments,
        extend_from_continue_on_error=extend_from_continue_on_error,
        extend_from_upscale=extend_from_upscale,
        extend_from_upscale_model=extend_from_upscale_model,
        extend_from_upscale_scale=extend_from_upscale_scale,
        extend_from_realesrgan_bin=extend_from_realesrgan_bin,
        extend_from_models_dir=extend_from_models_dir,
        extend_from_frames=extend_from_frames,
        extend_from_regenerate_base=extend_from_regenerate_base,
        extend_from_random_seed=extend_from_random_seed,
        upscale_input=upscale_input,
        upscale_output=upscale_output,
        upscale_model=upscale_model,
        upscale_scale=upscale_scale,
        upscale_realesrgan_bin=upscale_realesrgan_bin,
        upscale_models_dir=upscale_models_dir,
        upscale_keep_frames=upscale_keep_frames,
        inspect_input=inspect_input,
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
