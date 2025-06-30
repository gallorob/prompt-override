import os

from settings import settings

from textual.app import App
from ui_elements.menu import MenuScreen
from ui_elements.settings import SettingsScreen


class MainApp(App):
    ENABLE_COMMAND_PALETTE = False

    with open(os.path.join(settings.assets_dir, "style.tcss"), "r") as f:
        CSS = f.read()
    MODES = {"menu": MenuScreen, "settings": SettingsScreen}

    def on_mount(self) -> None:
        self.switch_mode("menu")


if __name__ == "__main__":
    MainApp().run()
