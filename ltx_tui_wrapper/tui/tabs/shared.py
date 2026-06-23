"""Shared helpers mixed into :class:`~ltx_tui_wrapper.tui.app.LtxTuiApp`."""

from __future__ import annotations

from textual.message_pump import MessagePump
from textual.widgets import Button, Static

from ltx_tui_wrapper.tui.constants import HIGHLIGHTABLE_IDS, INVALID_CLASS
from ltx_tui_wrapper.upscale import AI_SCALES


class TabMixinBase(MessagePump):
    """Base for tab mixins so :func:`textual.on` handlers register with Textual."""


class TabHelpersMixin(TabMixinBase):
    """Validation, status, and parsing helpers used across tabs."""

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _set_last_run_available(self, available: bool) -> None:
        self.query_one("#apply-last", Button).disabled = not available

    def _clear_validation_highlights(self) -> None:
        for widget_id in HIGHLIGHTABLE_IDS:
            widget = self.query(widget_id).first()
            if widget is not None:
                widget.remove_class(INVALID_CLASS)

    def _set_validation_highlights(self, widget_ids: list[str]) -> None:
        self._clear_validation_highlights()
        for widget_id in widget_ids:
            self.query_one(widget_id).add_class(INVALID_CLASS)

    def _parse_positive_int(self, text: str, *, field: str, widget_id: str) -> int | None:
        stripped = text.strip()
        if not stripped:
            self._set_validation_highlights([widget_id])
            self.query_one(widget_id).focus()
            self._set_status(f"{field} is required.")
            return None
        try:
            value = int(stripped)
        except ValueError:
            self._set_validation_highlights([widget_id])
            self.query_one(widget_id).focus()
            self._set_status(f"{field} must be an integer.")
            return None
        if value < 1:
            self._set_validation_highlights([widget_id])
            self.query_one(widget_id).focus()
            self._set_status(f"{field} must be at least 1.")
            return None
        return value

    def _parse_optional_scale(self, text: str, *, widget_id: str) -> int | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            value = int(stripped)
        except ValueError:
            self._set_validation_highlights([widget_id])
            self.query_one(widget_id).focus()
            self._set_status(f"Scale must be one of {', '.join(map(str, AI_SCALES))}.")
            raise ValueError("invalid scale")
        if value not in AI_SCALES:
            self._set_validation_highlights([widget_id])
            self.query_one(widget_id).focus()
            self._set_status(f"Scale must be one of {', '.join(map(str, AI_SCALES))}.")
            raise ValueError("invalid scale")
        return value
