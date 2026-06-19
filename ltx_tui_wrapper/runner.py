"""Run built ltx-2-mlx commands in the terminal."""

from __future__ import annotations

import shlex
import subprocess


def execute_command(argv: list[str]) -> int:
    """Print and run *argv*, returning the process exit code."""
    print(shlex.join(argv), flush=True)
    return subprocess.run(argv, check=False).returncode
