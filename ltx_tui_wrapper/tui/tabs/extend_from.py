"""Extend From tab for the ltx-tui application."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Collapsible, Label, Select, Static

from ltx_tui_wrapper.extend import parse_target_duration
from ltx_tui_wrapper.output_paths import extend_from_output_path
from ltx_tui_wrapper.last_extend_from_run import (
    load_last_extend_from_run,
    save_last_extend_from_run,
)
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.options import GenerateOptions
from ltx_tui_wrapper.output_paths import latest_output_path
from ltx_tui_wrapper.tui.command_preview import extend_from_command_preview
from ltx_tui_wrapper.tui.constants import EXTEND_UPSCALE_MODEL_PRESETS
from ltx_tui_wrapper.tui.run_actions import ExtendFromRun
from ltx_tui_wrapper.tui.tabs.shared import TabMixinBase
from ltx_tui_wrapper.tui.widgets import CopyInput
from ltx_tui_wrapper.upscale import AI_SCALES


class ExtendFromTabMixin(TabMixinBase):
    """Compose, events, and run logic for the Extend From tab."""

    def _compose_extend_from_tab(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "Continue an existing generated video using its embedded settings. "
                "Folder input extends every video inside; already-extended files are skipped. "
                "Interrupted segment runs resume from segments/<stem>/.",
                classes="field-hint",
            )
            yield Label("Input video or folder", classes="field-label")
            with Horizontal(classes="field-row"):
                yield CopyInput(
                    placeholder="path/to/video.mp4 or path/to/folder",
                    id="extend-from-input",
                )
                yield Button("Browse…", id="browse-extend-from-input")
            yield Label("Target duration", classes="field-label")
            yield CopyInput(placeholder="60, 90s, or 1.5m", id="extend-from-length")
            yield Static(
                "Seconds (60), suffixed seconds (90s), or minutes (1.5m).",
                classes="field-hint",
            )
            yield Label("Retries per segment", classes="field-label")
            yield CopyInput(value="1", id="extend-from-retries")
            yield Label("Final output path (optional, single input only)", classes="field-label")
            yield CopyInput(
                placeholder="default: extended/<input-stem>_extended.mp4",
                id="extend-from-output",
            )
            yield Checkbox("Keep segment files", id="extend-from-keep-segments")
            yield Checkbox("Continue on error", id="extend-from-continue-on-error")
            with Collapsible(title="Override embedded generate settings", collapsed=True):
                yield Label("Frame count (optional)", classes="field-label")
                yield CopyInput(
                    placeholder="leave empty to use embedded value",
                    id="extend-from-frames",
                )
                yield Static(
                    "When set, new segments use this frame count instead of the "
                    "value stored in the input video metadata.",
                    classes="field-hint",
                )
                yield Checkbox(
                    "Regenerate base segment from input last frame",
                    id="extend-from-regenerate-base",
                )
                yield Static(
                    "Re-run the first segment from the input's last frame so a frame "
                    "count override applies before chaining further segments. The "
                    "original input video is replaced in the final output.",
                    classes="field-hint",
                )
                yield Checkbox(
                    "Use random seed for all new segments",
                    id="extend-from-random-seed",
                )
                yield Static(
                    "Pick one random seed at the start and reuse it for every new "
                    "segment in this run.",
                    classes="field-hint",
                )
            with Collapsible(title="Upscale last frame between segments", collapsed=True):
                yield Checkbox(
                    "AI-upscale last frame before next segment",
                    id="extend-from-upscale",
                )
                yield Label("Upscale model", classes="field-label")
                yield Select(
                    EXTEND_UPSCALE_MODEL_PRESETS,
                    id="extend-from-upscale-model",
                    value="realesrgan-x4plus",
                )
                yield Label("Upscale scale (optional)", classes="field-label")
                yield CopyInput(
                    placeholder=f"auto or one of {', '.join(map(str, AI_SCALES))}",
                    id="extend-from-upscale-scale",
                )
                yield Label("realesrgan-ncnn-vulkan binary (optional)", classes="field-label")
                yield CopyInput(id="extend-from-realesrgan-bin")
                yield Label("Models directory (optional)", classes="field-label")
                yield CopyInput(id="extend-from-models-dir")
            yield Label("First new ltx-2-mlx generate command", classes="field-label")
            yield Static("", id="extend-from-command-preview", classes="command-preview")

    def _mount_extend_from_tab(self) -> None:
        if self._extend_from_input is not None:
            self.query_one("#extend-from-input", CopyInput).value = self._extend_from_input
        if self._extend_from_length is not None:
            self.query_one("#extend-from-length", CopyInput).value = self._extend_from_length
        if self._extend_from_retries is not None:
            self.query_one("#extend-from-retries", CopyInput).value = str(
                self._extend_from_retries
            )
        if self._extend_from_output is not None:
            self.query_one("#extend-from-output", CopyInput).value = self._extend_from_output
        if self._extend_from_keep_segments is not None:
            self.query_one("#extend-from-keep-segments", Checkbox).value = (
                self._extend_from_keep_segments
            )
        if self._extend_from_continue_on_error is not None:
            self.query_one("#extend-from-continue-on-error", Checkbox).value = (
                self._extend_from_continue_on_error
            )
        if self._extend_from_frames is not None:
            self.query_one("#extend-from-frames", CopyInput).value = str(
                self._extend_from_frames
            )
        if self._extend_from_regenerate_base is not None:
            self.query_one("#extend-from-regenerate-base", Checkbox).value = (
                self._extend_from_regenerate_base
            )
        if self._extend_from_random_seed is not None:
            self.query_one("#extend-from-random-seed", Checkbox).value = (
                self._extend_from_random_seed
            )
        if self._extend_from_upscale is not None:
            self.query_one("#extend-from-upscale", Checkbox).value = self._extend_from_upscale
        if self._extend_from_upscale_model is not None:
            self.query_one("#extend-from-upscale-model", Select).value = (
                self._extend_from_upscale_model
            )
        if self._extend_from_upscale_scale is not None:
            self.query_one("#extend-from-upscale-scale", CopyInput).value = str(
                self._extend_from_upscale_scale
            )
        if self._extend_from_realesrgan_bin is not None:
            self.query_one("#extend-from-realesrgan-bin", CopyInput).value = (
                self._extend_from_realesrgan_bin
            )
        if self._extend_from_models_dir is not None:
            self.query_one("#extend-from-models-dir", CopyInput).value = (
                self._extend_from_models_dir
            )
        self._refresh_extend_from_preview()

    def _extend_from_override_values(self) -> tuple[int | None, bool, bool]:
        frames_text = self.query_one("#extend-from-frames", CopyInput).value.strip()
        frames: int | None = None
        if frames_text:
            try:
                frames = int(frames_text)
            except ValueError:
                frames = -1
            if frames < 1:
                frames = -1
        regenerate_base = self.query_one(
            "#extend-from-regenerate-base", Checkbox
        ).value
        random_seed = self.query_one("#extend-from-random-seed", Checkbox).value
        return frames, regenerate_base, random_seed

    def _refresh_extend_from_preview(self) -> None:
        input_text = self.query_one("#extend-from-input", CopyInput).value.strip()
        if not input_text:
            self.query_one("#extend-from-command-preview", Static).update(
                "Set an input video or folder to preview the first new segment command."
            )
            return
        frames, regenerate_base, random_seed = self._extend_from_override_values()
        if frames == -1:
            self.query_one("#extend-from-command-preview", Static).update(
                "Frame count override must be a positive integer."
            )
            return
        self.query_one("#extend-from-command-preview", Static).update(
            extend_from_command_preview(
                input_text,
                frames=frames,
                regenerate_base=regenerate_base,
                random_seed=random_seed,
            )
        )

    def apply_last_extend_from(self, last_run: GenerateOptions | None = None) -> None:
        settings = load_last_extend_from_run()
        if settings is not None:
            self.query_one("#extend-from-input", CopyInput).value = settings.input_path
            self.query_one("#extend-from-length", CopyInput).value = settings.target_duration_text
            self.query_one("#extend-from-retries", CopyInput).value = str(settings.max_retries)
            self.query_one("#extend-from-output", CopyInput).value = settings.final_output or ""
            self.query_one("#extend-from-keep-segments", Checkbox).value = settings.keep_segments
            self.query_one("#extend-from-continue-on-error", Checkbox).value = (
                settings.continue_on_error
            )
            self.query_one("#extend-from-frames", CopyInput).value = (
                "" if settings.frames is None else str(settings.frames)
            )
            self.query_one("#extend-from-regenerate-base", Checkbox).value = (
                settings.regenerate_base
            )
            self.query_one("#extend-from-random-seed", Checkbox).value = (
                settings.random_seed
            )
            self.query_one("#extend-from-upscale", Checkbox).value = settings.upscale
            self.query_one("#extend-from-upscale-model", Select).value = settings.upscale_model
            self.query_one("#extend-from-upscale-scale", CopyInput).value = (
                "" if settings.upscale_scale is None else str(settings.upscale_scale)
            )
            self.query_one("#extend-from-realesrgan-bin", CopyInput).value = (
                settings.realesrgan_bin or ""
            )
            self.query_one("#extend-from-models-dir", CopyInput).value = settings.models_dir or ""
            self._refresh_extend_from_preview()
            self._set_status("Applied settings from last extend-from run.")
            return

        if last_run is None:
            last_run = load_last_run()
        if last_run is None:
            self._set_status(
                "No saved extend-from settings found. Run once or set fields manually."
            )
            return

        candidate = Path(latest_output_path(last_run.output)).expanduser()
        if not candidate.is_file():
            candidate = self._latest_video_in_parent(Path(last_run.output).expanduser())
        if candidate is None:
            self._set_status(
                "Could not find a video from last run. Generate once or set input manually."
            )
            return

        input_path = str(candidate)
        self.query_one("#extend-from-input", CopyInput).value = input_path
        self.query_one("#extend-from-output", CopyInput).value = extend_from_output_path(
            input_path
        )
        self._refresh_extend_from_preview()
        self._set_status("Applied last run output as extend-from input.")

    def _latest_video_in_parent(self, output_path: Path) -> Path | None:
        parent = output_path.parent
        if not parent.is_dir():
            return None
        candidates = [
            path
            for path in parent.iterdir()
            if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".m4v"}
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    @on(Button.Pressed, "#browse-extend-from-input")
    def browse_extend_from_input(self) -> None:
        from ltx_tui_wrapper.file_dialog import VIDEO_EXTENSIONS

        self._browse_into_input(
            "#extend-from-input",
            self._browse_start_dir("#extend-from-input"),
            extensions=VIDEO_EXTENSIONS,
            allow_directory=True,
        )

    @on(CopyInput.Changed, "#extend-from-input")
    @on(CopyInput.Changed, "#extend-from-frames")
    def extend_from_input_changed(self) -> None:
        self._refresh_extend_from_preview()

    @on(Checkbox.Changed, "#extend-from-regenerate-base")
    @on(Checkbox.Changed, "#extend-from-random-seed")
    def extend_from_override_changed(self) -> None:
        self._refresh_extend_from_preview()

    def _start_extend_from_run(self) -> None:
        self._clear_validation_highlights()

        input_text = self.query_one("#extend-from-input", CopyInput).value.strip()
        if not input_text:
            self._set_validation_highlights(["#extend-from-input"])
            self.query_one("#extend-from-input").focus()
            self._set_status("Input video or folder is required.")
            return

        input_path = Path(input_text).expanduser()
        if not input_path.is_file() and not input_path.is_dir():
            self._set_validation_highlights(["#extend-from-input"])
            self.query_one("#extend-from-input").focus()
            self._set_status(f"Input path not found: {input_path}")
            return

        length_text = self.query_one("#extend-from-length", CopyInput).value.strip()
        if not length_text:
            self._set_validation_highlights(["#extend-from-length"])
            self.query_one("#extend-from-length").focus()
            self._set_status("Target duration is required.")
            return
        try:
            target_duration = parse_target_duration(length_text)
        except ValueError as exc:
            self._set_validation_highlights(["#extend-from-length"])
            self.query_one("#extend-from-length").focus()
            self._set_status(str(exc))
            return

        retries = self._parse_positive_int(
            self.query_one("#extend-from-retries", CopyInput).value,
            field="Retries per segment",
            widget_id="#extend-from-retries",
        )
        if retries is None:
            return

        frames_text = self.query_one("#extend-from-frames", CopyInput).value.strip()
        frames: int | None = None
        if frames_text:
            try:
                frames = int(frames_text)
            except ValueError:
                self._set_validation_highlights(["#extend-from-frames"])
                self.query_one("#extend-from-frames").focus()
                self._set_status("Frame count override must be an integer.")
                return
            if frames < 1:
                self._set_validation_highlights(["#extend-from-frames"])
                self.query_one("#extend-from-frames").focus()
                self._set_status("Frame count override must be at least 1.")
                return

        regenerate_base = self.query_one(
            "#extend-from-regenerate-base", Checkbox
        ).value
        random_seed = self.query_one("#extend-from-random-seed", Checkbox).value

        upscale_scale_text = self.query_one("#extend-from-upscale-scale", CopyInput).value
        try:
            upscale_scale = self._parse_optional_scale(
                upscale_scale_text,
                widget_id="#extend-from-upscale-scale",
            )
        except ValueError:
            return

        output_text = self.query_one("#extend-from-output", CopyInput).value.strip()
        realesrgan_bin = self.query_one("#extend-from-realesrgan-bin", CopyInput).value.strip()
        models_dir = self.query_one("#extend-from-models-dir", CopyInput).value.strip()
        keep_segments = self.query_one("#extend-from-keep-segments", Checkbox).value
        continue_on_error = self.query_one("#extend-from-continue-on-error", Checkbox).value
        upscale = self.query_one("#extend-from-upscale", Checkbox).value
        upscale_model = str(self.query_one("#extend-from-upscale-model", Select).value)

        save_last_extend_from_run(
            input_path=str(input_path),
            target_duration_text=length_text,
            max_retries=retries,
            final_output=output_text or None,
            keep_segments=keep_segments,
            continue_on_error=continue_on_error,
            upscale=upscale,
            upscale_model=upscale_model,
            upscale_scale=upscale_scale,
            realesrgan_bin=realesrgan_bin or None,
            models_dir=models_dir or None,
            frames=frames,
            regenerate_base=regenerate_base,
            random_seed=random_seed,
        )

        self._pending_run = ExtendFromRun(
            input_path=str(input_path),
            target_duration=target_duration,
            max_retries=retries,
            final_output=output_text or None,
            keep_segments=keep_segments,
            continue_on_error=continue_on_error,
            upscale=upscale,
            upscale_model=upscale_model,
            upscale_scale=upscale_scale,
            realesrgan_bin=realesrgan_bin or None,
            models_dir=models_dir or None,
            frames=frames,
            regenerate_base=regenerate_base,
            random_seed=random_seed,
        )
        self.exit()
