from __future__ import annotations

from typing import Optional

from pynput.keyboard import Controller, Key


class KeyboardController:
    def __init__(self, mode: str = "tap") -> None:
        self._keyboard = Controller()
        self._current_direction: Optional[str] = None
        self.mode = mode

    def _key_for_direction(self, direction: str):
        return {
            "LEFT": Key.left,
            "RIGHT": Key.right,
            "UP": Key.up,
            "DOWN": Key.down,
        }[direction]

    def set_mode(self, mode: str) -> None:
        if mode not in {"tap", "hold"}:
            raise ValueError("mode must be 'tap' or 'hold'")
        if mode == self.mode:
            return
        self.reset()
        self.mode = mode

    def set_direction(self, direction: Optional[str]) -> None:
        if self.mode == "tap":
            if direction is None:
                self._current_direction = None
                return

            if direction == self._current_direction:
                return

            self._tap(direction)
            self._current_direction = direction
            return

        if direction == self._current_direction:
            return

        if self._current_direction is not None:
            self._keyboard.release(self._key_for_direction(self._current_direction))

        self._current_direction = direction

        if self._current_direction is not None:
            self._keyboard.press(self._key_for_direction(self._current_direction))

    def reset(self) -> None:
        if self.mode == "hold" and self._current_direction is not None:
            self._keyboard.release(self._key_for_direction(self._current_direction))
        self._current_direction = None

    def _tap(self, direction: str) -> None:
        key = self._key_for_direction(direction)
        self._keyboard.press(key)
        self._keyboard.release(key)