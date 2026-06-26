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


def _sanitize_terminal_text(text: str) -> str:
    """Normalize subprocess output so carriage returns do not clobber later lines."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip()


def _print_colored_band(message: str, *, background: str, stream) -> None:
    if not stream.isatty():
        print(message, file=stream, flush=True)
        return

    width = _terminal_width()
    band_text = _fit_message(message, width)
    middle_index = _BAND_LINES // 2
    for line_index in range(_BAND_LINES):
        if line_index == middle_index:
            print(_band_line(band_text, width=width, background=background), file=stream, flush=True)
        else:
            print(_filled_line(width=width, background=background), file=stream, flush=True)


def print_failure(summary: str, *, details: str | None = None) -> None:
    """Show a short summary in the red band and print full error text below."""
    _print_colored_band(summary, background=_FAILURE_BG, stream=sys.stderr)

    body = _sanitize_terminal_text(details if details is not None else summary)
    if body:
        print(body, file=sys.stdout, flush=True)


def abort_if_missing_output_directory(output: str) -> bool:
    """Print a failure band and return True when the output directory is missing."""
    from ltx_tui_wrapper.output_paths import missing_output_directory

    message = missing_output_directory(output)
    if message is None:
        return False
    print_failure(message)
    return True


def print_status_band(message: str, *, success: bool) -> None:
    """Print a three-line color band with *message* centered inside."""
    if not success:
        print_failure(message)
        return

    background = _SUCCESS_BG
    stream = sys.stdout

    if not stream.isatty():
        print(message, file=stream, flush=True)
        return

    _print_colored_band(message, background=background, stream=stream)
