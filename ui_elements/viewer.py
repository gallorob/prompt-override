from base_objects.vfs import File
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header

from ui_elements.extended_widgets import ExtendedTextArea, StatusBar


class ViewerScreen(ModalScreen):
    def __init__(self, file_obj: File) -> None:
        super().__init__()
        self.file_obj = file_obj

        self.text_area = ExtendedTextArea(
            self.file_obj.contents,
            show_line_numbers=True,
            read_only=True,
            on_cursor_moved=self._on_cursor_moved,
        )
        self.text_area.theme = "vscode_dark"
        self.status_bar = StatusBar()

        self.title = "Viewer"
        self.sub_title = self.file_obj.name

    BINDINGS = [
        Binding("escape", "close_viewer", "Quit", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="")
        yield Container(
            Horizontal(self.text_area, id="extended-text-area"),
            Horizontal(self.status_bar),
            id="editor",
        )
        yield Footer()

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

    def action_close_viewer(self):
        self.app.pop_screen()
