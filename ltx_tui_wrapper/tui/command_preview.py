"""Preview text for batch and extend generate commands."""

from __future__ import annotations

from dataclasses import replace

from ltx_tui_wrapper.last_run import load_last_run
from ltx_tui_wrapper.output_paths import timestamped_output_path
from ltx_tui_wrapper.parsing import format_command

_NO_LAST_RUN = (
    "No saved generate settings. Use the Generate tab and press Run once first."
)


def batch_generate_command_preview() -> str:
    """Return the ``ltx-2-mlx generate`` command used for each batch run."""
    base = load_last_run()
    if base is None:
        return _NO_LAST_RUN
    options = replace(base, output=timestamped_output_path(base.output))
    return format_command(options)


def extend_first_segment_command_preview() -> str:
    """Return the first-segment ``ltx-2-mlx generate`` command for extend runs."""
    base = load_last_run()
    if base is None:
        return _NO_LAST_RUN
    options = replace(base, output=timestamped_output_path(base.output))
    command = format_command(options)
    return (
        f"{command}\n\n"
        "(Later segments reuse these settings with -i <last-frame> until the "
        "target duration is exceeded.)"
    )
