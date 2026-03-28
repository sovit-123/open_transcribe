"""Typing helpers for dictation output."""

from __future__ import annotations


class CursorTyperError(RuntimeError):
    """Raised when automatic typing cannot be initialized."""


class CursorTyper:
    """Types text into the currently focused application."""

    def __init__(self, append_space: bool = True) -> None:
        self.append_space = append_space
        try:
            import pyautogui  # type: ignore
        except Exception as exc:
            raise CursorTyperError(
                "pyautogui is required for --type-text mode. "
                "Install it with: pip install pyautogui"
            ) from exc

        self._pyautogui = pyautogui

    def type_text(self, text: str) -> None:
        payload = text
        if self.append_space:
            payload = f"{payload} "
        self._pyautogui.typewrite(payload)
