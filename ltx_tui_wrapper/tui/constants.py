"""TUI constants for the ltx-tui application."""

from __future__ import annotations

from ltx_tui_wrapper.options import MODEL_IDS, PIPELINE_MODES

INVALID_CLASS = "-invalid"

HIGHLIGHTABLE_IDS = (
    "#prompt",
    "#output-path",
    "#pipeline-mode",
    "#frame-rate",
    "#height",
    "#width",
    "#frames",
    "#image-path",
    "#image-frame-idx",
    "#image-strength",
    "#image-crf",
    "#extra-images",
    "#lora-specs",
    "#steps",
    "#stage1-steps",
    "#stage2-steps",
    "#cfg-scale",
    "#stg-scale",
    "#teacache-thresh",
    "#seed",
    "#model",
    "#gemma",
)

MODEL_PRESETS: tuple[tuple[str, str], ...] = tuple((model_id, model_id) for model_id in MODEL_IDS)

PIPELINE_MODE_PRESETS: tuple[tuple[str, str], ...] = PIPELINE_MODES

FRAME_RATE_PRESETS: tuple[tuple[str, str], ...] = (
    ("24 fps (trained default)", "24"),
    ("Custom…", "custom"),
)

RESOLUTION_PRESETS: tuple[tuple[str, str], ...] = (
    ("480×704 (default)", "480x704"),
    ("768×512", "768x512"),
    ("Custom…", "custom"),
)

NCNN_MODEL_PRESETS: tuple[tuple[str, str], ...] = (
    ("FFmpeg Lanczos (default)", "__lanczos__"),
    ("realesrgan-x4plus", "realesrgan-x4plus"),
    ("realesr-animevideov3", "realesr-animevideov3"),
    ("realesrgan-x4plus-anime", "realesrgan-x4plus-anime"),
    ("realesrnet-x4plus", "realesrnet-x4plus"),
)

EXTEND_UPSCALE_MODEL_PRESETS: tuple[tuple[str, str], ...] = (
    ("realesrgan-x4plus (default)", "realesrgan-x4plus"),
    ("realesr-animevideov3", "realesr-animevideov3"),
    ("realesrgan-x4plus-anime", "realesrgan-x4plus-anime"),
    ("realesrnet-x4plus", "realesrnet-x4plus"),
)

TAB_IDS = ("generate", "batch", "extend", "upscale")

APP_CSS = """
Screen {
    layout: vertical;
}
VerticalScroll {
    height: 1fr;
    padding: 0 1;
}
.field-label {
    margin-top: 1;
    text-style: bold;
}
.field-hint {
    color: $text-muted;
    margin-bottom: 1;
}
.field-row {
    height: auto;
    margin-bottom: 1;
}
.field-row CopyInput {
    width: 1fr;
}
CopyInput.-invalid, Select.-invalid, CopyTextArea.-invalid {
    border: tall $error;
}
Collapsible {
    margin: 1 0;
    border: solid $primary;
    padding: 0 1 1 1;
}
TabbedContent {
    height: 1fr;
}
TabbedContent > ContentSwitcher {
    height: 1fr;
}
.command-preview {
    height: auto;
    margin: 0 1;
    padding: 1;
    border: solid $accent;
    background: $surface;
    color: $text;
}
#command-preview {
    height: auto;
    margin: 0 1;
    padding: 1;
    border: solid $accent;
    background: $surface;
    color: $text;
}
#run-hint {
    margin: 0 1 1 1;
}
#status {
    height: auto;
    padding: 0 1;
    color: $warning;
}
#action-row {
    height: auto;
    padding: 0 1 1 1;
    align: center middle;
}
#action-row Button {
    margin-right: 1;
}
.resolution-row CopyInput {
    width: 1fr;
}
.resolution-row {
    height: auto;
    margin-bottom: 1;
}
.hidden-custom {
    display: none;
}
.hidden-custom.visible {
    display: block;
}
FilePickScreen DirectoryTree {
    height: 1fr;
}
.pick-actions {
    height: auto;
    padding: 1;
    align: center middle;
}
CopyTextArea {
    height: 3;
    margin-bottom: 1;
}
"""
