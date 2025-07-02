from typing import Callable, Optional

from textual.widgets import Static, TextArea


class ExtendedTextArea(TextArea):
    def __init__(
        self,
        *args,
        on_cursor_moved: Optional[Callable[[tuple[int, int]], None]] = None,
        **kwargs,
    ):
        self.on_cursor_moved = on_cursor_moved
        self._last_cursor_location = (0, 0)  # Initialize before super().__init__
        super().__init__(*args, **kwargs)

    def _watch_selection(self, old, new):
        # Call the callback if the cursor location changed

        if self.cursor_location != self._last_cursor_location:
            self._last_cursor_location = self.cursor_location
            if self.on_cursor_moved:
                self.on_cursor_moved(self.cursor_location)
        super()._watch_selection(old, new)


class StatusBar(Static):
    def __init__(self):
        super().__init__("")
        self.update_status(1, 1, 0)

    def update_status(self, line: int, col: int, sel_len: int):
        parts = [f"Ln {line}", f"Col {col}"]
        if sel_len > 0:
            parts.append(f"Sel {sel_len}")
        self.update("; ".join(parts))
