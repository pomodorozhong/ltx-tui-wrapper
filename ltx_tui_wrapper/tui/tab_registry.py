"""Registry of TUI tabs and their handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TabId = Literal["generate", "batch", "extend", "extend_from", "upscale"]


@dataclass(frozen=True)
class TabSpec:
    """Declarative wiring for one tab in the app shell."""

    id: TabId
    title: str
    hotkey: str
    compose_method: str
    mount_method: str
    start_run_method: str
    apply_last_method: str | None = None
    apply_last_needs_last_run: bool = False
    activate_method: str | None = None


TAB_SPECS: tuple[TabSpec, ...] = (
    TabSpec(
        id="generate",
        title="Generate",
        hotkey="ctrl+1",
        compose_method="_compose_generate_tab",
        mount_method="_mount_generate_tab",
        start_run_method="_start_generate_run",
        apply_last_method="apply_last_generate",
        apply_last_needs_last_run=True,
    ),
    TabSpec(
        id="batch",
        title="Batch",
        hotkey="ctrl+2",
        compose_method="_compose_batch_tab",
        mount_method="_mount_batch_tab",
        start_run_method="_start_batch_run",
        apply_last_method="apply_last_batch",
        activate_method="_refresh_batch_preview",
    ),
    TabSpec(
        id="extend",
        title="Extend",
        hotkey="ctrl+3",
        compose_method="_compose_extend_tab",
        mount_method="_mount_extend_tab",
        start_run_method="_start_extend_run",
        apply_last_method="apply_last_extend",
        apply_last_needs_last_run=True,
        activate_method="_refresh_extend_preview",
    ),
    TabSpec(
        id="extend_from",
        title="Extend From",
        hotkey="ctrl+4",
        compose_method="_compose_extend_from_tab",
        mount_method="_mount_extend_from_tab",
        start_run_method="_start_extend_from_run",
        apply_last_method="apply_last_extend_from",
        activate_method="_refresh_extend_from_preview",
    ),
    TabSpec(
        id="upscale",
        title="Upscale",
        hotkey="ctrl+5",
        compose_method="_compose_upscale_tab",
        mount_method="_mount_upscale_tab",
        start_run_method="_start_upscale_run",
        apply_last_method="apply_last_upscale",
        apply_last_needs_last_run=True,
    ),
)

TAB_SPEC_BY_ID: dict[TabId, TabSpec] = {spec.id: spec for spec in TAB_SPECS}
TAB_IDS: tuple[TabId, ...] = tuple(spec.id for spec in TAB_SPECS)
