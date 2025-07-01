import glob
import os

from base_objects.level import Level
from settings import settings

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.level_files = self.get_level_files()
        self.selected_level_idx = 0

    def get_level_files(self):
        pattern = os.path.join(settings.assets_dir, "level*.json")
        return sorted([os.path.basename(f) for f in glob.glob(pattern)])

    def compose(self) -> ComposeResult:
        yield Center(
            Static(self.load_title(), id="title"),
            Container(
                Grid(
                    Button(
                        f"Level: {self.selected_level_idx + 1 if self.level_files else 'N/A'}",
                        variant="default",
                        id="level_select",
                        classes="menu_buttons",
                    ),
                    Button(
                        "Start Level",
                        variant="default",
                        id="new_game",
                        classes="menu_buttons",
                    ),
                    Button(
                        "Options",
                        variant="primary",
                        id="settings",
                        classes="menu_buttons",
                    ),
                    Button("Exit", variant="error", id="exit", classes="menu_buttons"),
                    id="menu_grid",
                    classes="horizontal-centered",
                ),
                id="menu_container",
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
        if button_id == "level_select":
            if self.level_files:
                self.selected_level_idx = (self.selected_level_idx + 1) % len(
                    self.level_files
                )
                self.query_one("#level_select", Button).label = (
                    f"Level: {self.level_files[self.selected_level_idx]}"
                )
        elif button_id == "new_game":
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
        if not self.level_files:
            self.notify("No levels found!", severity="error")
            return
        level_file = self.level_files[self.selected_level_idx]
        level = Level.from_file(os.path.join(settings.assets_dir, level_file))
        level.initialize()
        self.app.push_screen(IntroScreen(level=level))

    def action_settings(self) -> None:
        self.app.switch_mode("settings")

    def action_quit(self) -> None:
        self.app.exit()
