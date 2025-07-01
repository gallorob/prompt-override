import os

from base_objects.level import Level
from settings import settings

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static
from ui_elements.game import GameScreen
from ui_elements.intro import IntroScreen
from utils import check_server_connection


class MenuScreen(Screen):

    BINDINGS = [
        Binding(
            key="n", action="new_game", description="Start a [N]ew game.", priority=True
        ),
        Binding(
            key="o", action="settings", description="Edit [O]ptions.", priority=True
        ),
        Binding(
            key="escape",
            action="quit",
            description="[Esc]ape to reality.",
            priority=True,
        ),
    ]

    def compose(self) -> ComposeResult:
        yield Center(
            Static(self.load_title(), id="title"),
            Container(
                Vertical(
                    Button("New Game", variant="default", id="new_game"),
                    Button("Options", variant="primary", id="settings"),
                    Button("Exit", variant="error", id="exit"),
                    id="menu_buttons",
                )
            ),
        )

        yield Footer()

    def load_title(self) -> str:
        try:
            with open(
                os.path.join(settings.assets_dir, settings.title), "r", encoding="utf-8"
            ) as file:
                return file.read()
        except FileNotFoundError:
            return "[Title Missing]"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "new_game":
            if check_server_connection():
                self.action_new_game()
            else:
                self.notify(
                    f"Cannot start game: server is unreachable or username is wrong.",
                    severity="error",
                )
        elif button_id == "settings":
            self.action_settings()
        elif button_id == "exit":
            self.action_quit()

    def action_new_game(self) -> None:
        level = Level.from_file(os.path.join(settings.assets_dir, "level01.json"))
        level.initialize()
        self.app.push_screen(IntroScreen(level=level))

    def action_settings(self) -> None:
        self.app.switch_mode("settings")

    def action_quit(self) -> None:
        self.app.exit()
