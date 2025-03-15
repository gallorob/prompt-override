from textual.app import App

from ui_elements.game import GameScreen
from ui_elements.menu import MenuScreen
from settings import settings
from ui_elements.options import SettingsScreen

class MainApp(App):
	ENABLE_COMMAND_PALETTE = False
	
	with open('style.tcss', 'r') as f:
		CSS = f.read()

	MODES = {
		'menu': MenuScreen,
		'in_game': GameScreen,
		'options': SettingsScreen
	}

	def on_mount(self) -> None:
		self.switch_mode('menu')


if __name__ == "__main__":
	MainApp().run()
