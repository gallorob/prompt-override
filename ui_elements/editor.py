from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container
from textual.widgets import TextArea, Footer, Header
from textual.binding import Binding

from base_objects.vfs import File

class EditorScreen(ModalScreen):
    def __init__(self, file_obj: File) -> None:
        super().__init__()
        self.file_obj = file_obj
        self.text_area = TextArea(self.file_obj.contents,
                                  show_line_numbers=True)
        self.text_area.theme = 'vscode_dark'

        self.title = 'Editor'
        self.sub_title = self.file_obj.name
        
    
    BINDINGS = [
        Binding('escape', 'close_editor', 'Quit', priority=True),
        Binding('ctrl+s', 'save_contents', 'Save & Exit', priority=True)
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon='')
        yield Container(self.text_area,
                        id='editor')
        yield Footer()

    def action_close_editor(self):
        self.app.pop_screen()
    
    def action_save_contents(self):
        self.file_obj.contents = self.text_area.text
        self.app.pop_screen()
    