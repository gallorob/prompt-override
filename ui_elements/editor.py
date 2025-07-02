from typing import Callable, Optional

from base_objects.vfs import File
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, TextArea


class EditorTextArea(TextArea):
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


class EditorStatusBar(Static):
    def __init__(self):
        super().__init__("")
        self.update_status(1, 1, 0)

    def update_status(self, line: int, col: int, sel_len: int):
        parts = [f"Ln {line}", f"Col {col}"]
        if sel_len > 0:
            parts.append(f"Sel {sel_len}")
        self.update("; ".join(parts))


class EditorScreen(ModalScreen):
    def __init__(self, file_obj: File, bak: Optional[File] = None) -> None:
        super().__init__()
        self.file_obj = file_obj
        self.bak = bak
        self.text_area = EditorTextArea(
            self.file_obj.contents,
            show_line_numbers=True,
            on_cursor_moved=self._on_cursor_moved,
        )
        self.text_area.theme = "vscode_dark"
        self.status_bar = EditorStatusBar()
        self.title = "Editor"
        self.sub_title = self.file_obj.name

    BINDINGS = [
        Binding("escape", "close_editor", "Quit", priority=True),
        Binding("ctrl+s", "save_contents", "Save & Exit", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="")
        yield Container(
            Horizontal(self.text_area, id="editor-text-area"),
            Horizontal(self.status_bar),
            id="editor",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.text_area.focus()
        self._update_cursor_position(self.text_area.cursor_location)

    def _on_cursor_moved(self, location: tuple[int, int]):
        self._update_cursor_position(location)

    def _update_cursor_position(self, cursor: tuple[int, int]):
        line = cursor[0] + 1
        column = cursor[1] + 1
        selection = self.text_area.selection
        sel_len = (
            len(self.text_area.selected_text) if selection.start != selection.end else 0
        )
        self.status_bar.update_status(line, column, sel_len)

    def action_close_editor(self):
        self.app.pop_screen()

    def action_save_contents(self):
        if self.bak:
            self.bak.contents = self.file_obj.contents
        self.file_obj.contents = self.text_area.text
        self.app.pop_screen()
