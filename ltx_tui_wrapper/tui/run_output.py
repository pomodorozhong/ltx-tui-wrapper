"""Capture stdout/stderr from background jobs into the TUI."""

from __future__ import annotations

import io
import sys
from collections.abc import Callable
from contextlib import contextmanager


class TuiLogStream(io.TextIOBase):
    """Forward text writes to a callback, splitting on newlines."""

    def __init__(self, append_line: Callable[[str], None]) -> None:
        self._append_line = append_line
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._buffer += text.replace("\r", "\n")
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line:
                self._append_line(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self._append_line(self._buffer)
            self._buffer = ""


@contextmanager
def capture_stdio(append_line: Callable[[str], None]):
    """Redirect ``sys.stdout`` and ``sys.stderr`` to *append_line*."""
    stream = TuiLogStream(append_line)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stream
    sys.stderr = stream
    try:
        yield
    finally:
        stream.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
