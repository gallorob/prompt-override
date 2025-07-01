import os

from base_objects.level import Level
from settings import settings

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Static
from ui_elements.game import GameScreen


class IntroScreen(Screen):
    def __init__(self, level: Level):
        super().__init__()
        self.level = level

        with open(
            os.path.join(
                settings.assets_dir, f"level{str(self.level.number).zfill(2)}", "intro"
            ),
            "r",
        ) as f:
            self.intro_text = f.read()

    def compose(self) -> ComposeResult:
        yield Center(
            Static(f"Level {self.level.number} - Intro", classes="horizontal-centered"),
            ScrollableContainer(Static(self.intro_text)),
            Center(
                Button(label="Start the level", id="start_level"),
                classes="horizontal-centered",
            ),
            id="intro_screen",
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "start_level":
            self.app.pop_screen()
            await self.app.push_screen(GameScreen(level=self.level))
            self.app.screen.intro_msg()
