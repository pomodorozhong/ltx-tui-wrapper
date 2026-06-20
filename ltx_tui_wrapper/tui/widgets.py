"""Custom Textual widgets for the ltx-tui generate builder."""

from __future__ import annotations

from typing import ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import Input, TextArea

_VISIBLE_TEXT_BINDINGS: tuple[Binding, ...] = (
    Binding("ctrl+c,super+c", "copy", "Copy", show=True),
    Binding("ctrl+shift+u", "clear_all", "Clear all", show=True),
)


def _with_visible_text_bindings(bindings: list[BindingType]) -> list[BindingType]:
    """Replace the hidden copy binding with footer-visible copy and clear actions."""
    merged = [binding for binding in bindings if getattr(binding, "action", None) != "copy"]
    merged.extend(_VISIBLE_TEXT_BINDINGS)
    return merged


class CopyInput(Input):
    """Single-line text input with Copy and Clear all shortcuts."""

    BINDINGS: ClassVar[list[BindingType]] = _with_visible_text_bindings(list(Input.BINDINGS))

    def action_copy(self) -> None:
        """Copy the selection, or the full value when nothing is selected."""
        text = self.selected_text or self.value
        if text:
            self.app.copy_to_clipboard(text)

    def action_clear_all(self) -> None:
        """Clear the entire input."""
        if self.disabled:
            return
        self.clear()


class CopyTextArea(TextArea):
    """Multi-line text input with Copy and Clear all shortcuts."""

    BINDINGS: ClassVar[list[BindingType]] = _with_visible_text_bindings(list(TextArea.BINDINGS))

    def action_copy(self) -> None:
        """Copy the selection, or the full content when nothing is selected."""
        text = self.selected_text or self.text
        if text:
            self.app.copy_to_clipboard(text)

    def action_clear_all(self) -> None:
        """Clear the entire text area."""
        if self.disabled or self.read_only:
            return
        self.clear()
