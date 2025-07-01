from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class QuitScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Are you sure you want to quit?", id="question"),
            Horizontal(
                Button("Quit", variant="error", id="quit", classes="quit_buttons"),
                Button(
                    "Cancel", variant="primary", id="cancel", classes="quit_buttons"
                ),
            ),
            id="quit_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.pop_screen()  # close the game screen
        self.app.pop_screen()  # close this dialog
