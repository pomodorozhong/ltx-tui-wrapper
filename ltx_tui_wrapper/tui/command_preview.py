"""Preview text for batch and extend generate commands."""

from __future__ import annotations

from dataclasses import replace

from ltx_tui_wrapper.extend_from import load_generate_options_from_video
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


def extend_from_command_preview(
    input_path: str,
    *,
    frames: int | None = None,
    regenerate_base: bool = False,
    random_seed: bool = False,
) -> str:
    """Return the first new-segment command for extend-from runs."""
    from pathlib import Path

    from ltx_tui_wrapper.extend_from import scan_extend_from_segments
    from ltx_tui_wrapper.output_paths import (
        discover_extend_from_inputs,
        extend_from_segments_dir,
        extended_output_exists,
    )

    path = Path(input_path).expanduser()
    if path.is_dir():
        try:
            videos = discover_extend_from_inputs(path)
        except SystemExit:
            return f"No candidate videos found in {path}"
        for video in videos:
            if extended_output_exists(video) is None:
                path = video
                break
        else:
            return "All videos in this folder already have extended outputs."
    elif not path.is_file():
        return f"Input not found: {path}"

    if extended_output_exists(path) is not None:
        return f"{path.name} already has an extended output and would be skipped."

    completed = scan_extend_from_segments(extend_from_segments_dir(path))
    resume_note = ""
    if completed:
        resume_note = (
            f"\n\n({len(completed)} segment(s) already on disk; "
            f"next run will resume from segment {len(completed) + 1}.)"
        )

    try:
        base = load_generate_options_from_video(path)
    except ValueError as exc:
        return str(exc)

    if frames is not None:
        base = replace(base, frames=frames)

    override_notes: list[str] = []
    if frames is not None:
        override_notes.append(f"frame count overridden to {frames}")
    if random_seed:
        override_notes.append("random seed for all new segments")
    if regenerate_base:
        override_notes.append("base segment regenerated from input last frame")

    if regenerate_base and not completed:
        preview_options = replace(
            base,
            output="base_regenerated.mp4",
            image_specs=("<input-last-frame.png>",),
        )
        command = format_command(preview_options)
        chain_note = (
            "A new base segment is generated from the input's last frame first; "
            "later segments chain from there until the target duration is exceeded."
        )
    else:
        preview_options = replace(
            base,
            output="<segment>.mp4",
            image_specs=("<input-last-frame.png>",),
        )
        command = format_command(preview_options)
        chain_note = (
            "The input video is kept as the first segment; new segments chain from "
            "its last frame until the target duration is exceeded."
        )

    override_text = ""
    if override_notes:
        override_text = f"\n\nOverrides: {', '.join(override_notes)}."
    if random_seed:
        override_text += " Preview shows a placeholder seed; a new value is picked at run time."

    return f"{command}\n\n({chain_note}){override_text}{resume_note}"
