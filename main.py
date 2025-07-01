import logging
import os
from datetime import datetime

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


def setup_logging(log_filename):
    handler = logging.FileHandler(log_filename)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s"
        )
    )
    logger = logging.getLogger("prompt_override")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


if __name__ == "__main__":
    os.makedirs("./logs", exist_ok=True)
    log_filename = f'./logs/log_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'
    setup_logging(log_filename)

    MainApp().run()
