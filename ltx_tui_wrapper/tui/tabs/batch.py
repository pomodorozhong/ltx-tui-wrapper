"""Batch tab for the ltx-tui application."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Label, Static

from ltx_tui_wrapper.last_batch_run import load_last_batch_run, save_last_batch_run
from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.tui.command_preview import batch_generate_command_preview
from ltx_tui_wrapper.tui.run_actions import BatchRun
from ltx_tui_wrapper.tui.tabs.shared import TabMixinBase
from ltx_tui_wrapper.tui.widgets import CopyInput


class BatchTabMixin(TabMixinBase):
    """Compose, events, and run logic for the Batch tab."""

    def _compose_batch_tab(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "Re-run the last Generate settings multiple times. "
                "Each output file gets a timestamp suffix.",
                classes="field-hint",
            )
            yield Label("Number of videos", classes="field-label")
            yield CopyInput(value="1", id="batch-count")
            yield Checkbox("Continue on error", id="batch-continue-on-error")
            yield Label("ltx-2-mlx generate command (per run)", classes="field-label")
            yield Static("", id="batch-command-preview", classes="command-preview")

    def _mount_batch_tab(self) -> None:
        if self._prefill_batch_count is not None:
            self.query_one("#batch-count", CopyInput).value = str(self._prefill_batch_count)
        if self._prefill_batch_continue_on_error is not None:
            self.query_one("#batch-continue-on-error", Checkbox).value = (
                self._prefill_batch_continue_on_error
            )
        self._refresh_batch_preview()

    def _apply_last_batch_run(self) -> bool:
        settings = load_last_batch_run()
        if settings is None:
            return False
        self.query_one("#batch-count", CopyInput).value = str(settings.count)
        self.query_one("#batch-continue-on-error", Checkbox).value = (
            settings.continue_on_error
        )
        return True

    def _refresh_batch_preview(self) -> None:
        self.query_one("#batch-command-preview", Static).update(
            batch_generate_command_preview()
        )

    def apply_last_batch(self) -> None:
        applied_batch = self._apply_last_batch_run()
        self._refresh_batch_preview()
        if applied_batch:
            self._set_status("Applied settings from last batch run.")
        else:
            self._set_status("Refreshed batch command preview from last run.")

    def _start_batch_run(self) -> None:
        self._clear_validation_highlights()
        if load_last_run() is None:
            self._set_status(
                "No saved generate settings. Use the Generate tab and press Run once first."
            )
            return

        count = self._parse_positive_int(
            self.query_one("#batch-count", CopyInput).value,
            field="Number of videos",
            widget_id="#batch-count",
        )
        if count is None:
            return

        continue_on_error = self.query_one("#batch-continue-on-error", Checkbox).value
        save_last_batch_run(count=count, continue_on_error=continue_on_error)
        self._pending_run = BatchRun(
            count=count,
            continue_on_error=continue_on_error,
        )
        self.exit()
