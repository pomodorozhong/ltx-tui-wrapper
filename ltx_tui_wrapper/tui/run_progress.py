"""Run progress display for the generate TUI."""

from __future__ import annotations

import time
from typing import Protocol

from textual.timer import Timer
from textual.widgets import RichLog, Static


class ProgressHost(Protocol):
    """Widget query surface for run progress UI."""

    def query_one(self, selector: str, expect_type: type): ...
    def set_interval(self, interval: float, callback, *, name: str, pause: bool): ...


def format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


class RunProgressController:
    """Shows elapsed time and output log while generation runs."""

    def __init__(self, host: ProgressHost) -> None:
        self._host = host
        self._run_started: float | None = None
        self._run_timer: Timer | None = None

    def on_mount(self) -> None:
        self._run_timer = self._host.set_interval(
            0.25, self._update_run_timer, name="run_elapsed", pause=True
        )

    def clear_output(self) -> None:
        self._host.query_one("#run-output", RichLog).clear()

    def show(self, message: str = "Generating video…") -> None:
        self._run_started = time.perf_counter()
        panel = self._host.query_one("#run-panel")
        panel.add_class("visible")
        header = self._host.query_one("#run-header")
        header.remove_class("finished")
        self._host.query_one("#run-message", Static).update(message)
        self._host.query_one("#run-timer", Static).update("Elapsed: 0s")
        self._update_run_timer()
        if self._run_timer is not None:
            self._run_timer.resume()

    def finish(self) -> None:
        self._host.query_one("#run-header").add_class("finished")
        self._run_started = None
        if self._run_timer is not None:
            self._run_timer.pause()

    def capture_elapsed(self) -> float | None:
        if self._run_started is None:
            return None
        return time.perf_counter() - self._run_started

    def _update_run_timer(self) -> None:
        if self._run_started is None:
            return
        elapsed = time.perf_counter() - self._run_started
        self._host.query_one("#run-timer", Static).update(
            f"Elapsed: {format_elapsed(elapsed)}"
        )
