"""Run built ltx-2-mlx commands in the terminal."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from contextlib import contextmanager
from collections.abc import Iterator


def execute_command(argv: list[str], *, echo: bool = True) -> int:
    """Print and run *argv*, returning the process exit code."""
    if echo:
        print(shlex.join(argv), flush=True)
    return subprocess.run(argv, check=False).returncode


@contextmanager
def prevent_sleep() -> Iterator[None]:
    """Keep the system awake on macOS for the duration of the block."""
    if sys.platform != "darwin" or shutil.which("caffeinate") is None:
        yield
        return

    proc = subprocess.Popen(
        ["caffeinate", "-dims", "-w", str(os.getpid())],
    )
    print("System sleep prevented (caffeinate).", flush=True)
    try:
        yield
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
