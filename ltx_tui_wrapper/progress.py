"""Terminal visual aids for long-running CLI workflows."""

from __future__ import annotations

import shutil
import sys

_RESET = "\033[0m"
_BOLD = "\033[1m"
_SUCCESS_BG = "\033[48;5;28m"
_FAILURE_BG = "\033[48;5;124m"
_TEXT_FG = "\033[38;5;255m"

_BAND_LINES = 3


def _terminal_width() -> int:
    return max(20, shutil.get_terminal_size(fallback=(80, 24)).columns)


def _fit_message(message: str, width: int) -> str:
    if len(message) <= width:
        return message
    if width <= 1:
        return message[:width]
    return message[: width - 1] + "…"


def _band_line(message: str, *, width: int, background: str) -> str:
    text = _fit_message(message, width)
    pad_total = max(0, width - len(text))
    left = pad_total // 2
    right = pad_total - left
    return f"{background}{_TEXT_FG}{_BOLD}{' ' * left}{text}{' ' * right}{_RESET}"


def _filled_line(*, width: int, background: str) -> str:
    return f"{background}{' ' * width}{_RESET}"


def print_status_band(message: str, *, success: bool) -> None:
    """Print a three-line color band with *message* centered inside."""
    background = _SUCCESS_BG if success else _FAILURE_BG
    stream = sys.stdout if success else sys.stderr

    if not stream.isatty():
        print(message, file=stream, flush=True)
        return

    width = _terminal_width()
    middle_index = _BAND_LINES // 2
    for line_index in range(_BAND_LINES):
        if line_index == middle_index:
            print(_band_line(message, width=width, background=background), file=stream, flush=True)
        else:
            print(_filled_line(width=width, background=background), file=stream, flush=True)
