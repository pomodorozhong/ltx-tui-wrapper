"""Per-tab mixins for the ltx-tui application."""

from ltx_tui_wrapper.tui.tabs.batch import BatchTabMixin
from ltx_tui_wrapper.tui.tabs.extend import ExtendTabMixin
from ltx_tui_wrapper.tui.tabs.extend_from import ExtendFromTabMixin
from ltx_tui_wrapper.tui.tabs.generate import GenerateTabMixin
from ltx_tui_wrapper.tui.tabs.inspect import InspectTabMixin
from ltx_tui_wrapper.tui.tabs.shared import TabHelpersMixin, TabMixinBase
from ltx_tui_wrapper.tui.tabs.upscale import UpscaleTabMixin

__all__ = [
    "BatchTabMixin",
    "ExtendTabMixin",
    "ExtendFromTabMixin",
    "GenerateTabMixin",
    "InspectTabMixin",
    "TabHelpersMixin",
    "TabMixinBase",
    "UpscaleTabMixin",
]
