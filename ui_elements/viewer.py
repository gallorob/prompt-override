from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container
from textual.widgets import TextArea, Footer, Header
from textual.binding import Binding

from vfs import File

class ViewerScreen(ModalScreen):
    def __init__(self, file_obj: File) -> None:
        super().__init__()
        self.file_obj = file_obj
        self.text_area = TextArea(self.file_obj.contents,
                                  read_only=True,
                                  show_line_numbers=True)
        self.text_area.theme = 'vscode_dark'

        self.title = 'Viewer'
        self.sub_title = self.file_obj.name
        
    
    BINDINGS = [
        Binding('escape', 'close_editor', 'Quit', priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon='')
        yield Container(self.text_area,
                        id='viewer')
        yield Footer()

    def action_close_editor(self):
        self.app.pop_screen()
    