"""Per-tab mixins for the ltx-tui application."""

from ltx_tui_wrapper.tui.tabs.batch import BatchTabMixin
from ltx_tui_wrapper.tui.tabs.extend import ExtendTabMixin
from ltx_tui_wrapper.tui.tabs.generate import GenerateTabMixin
from ltx_tui_wrapper.tui.tabs.shared import TabHelpersMixin, TabMixinBase
from ltx_tui_wrapper.tui.tabs.upscale import UpscaleTabMixin

__all__ = [
    "BatchTabMixin",
    "ExtendTabMixin",
    "GenerateTabMixin",
    "TabHelpersMixin",
    "TabMixinBase",
    "UpscaleTabMixin",
]
