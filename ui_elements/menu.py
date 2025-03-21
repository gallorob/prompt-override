import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from base_objects.level import Level
from settings import settings
from ui_elements.game import GameScreen


class MenuScreen(Screen):

	BINDINGS = [
		Binding(key='n', action='new_game', description='Start a [N]ew game.', priority=True),
		Binding(key='o', action='settings', description='Edit [O]ptions.', priority=True),
		Binding(key='escape', action='quit', description='[Esc]ape to reality.', priority=True)
	]

	def compose(self) -> ComposeResult:
		yield Center(
			Static(self.load_title(), id="title"),
			Container(
				Vertical(
					Button("New Game", id="new_game"),
					Button("Options", id="settings"),
					Button("Exit", id="exit"),
					id="menu_buttons"
				)
			))

		yield Footer()

	def load_title(self) -> str:
		try:
			with open(os.path.join(settings.assets_dir, settings.title), "r", encoding="utf-8") as file:
				return file.read()
		except FileNotFoundError:
			return "[Title Missing]"

	def on_button_pressed(self, event: Button.Pressed) -> None:
		button_id = event.button.id
		if button_id == "new_game":
			self.action_new_game()
		elif button_id == "settings":
			self.action_settings()
		elif button_id == "exit":
			self.action_quit()

	def action_new_game(self) -> None:
		level = Level.from_file(os.path.join(settings.assets_dir, 'level01.json'))
		self.app.push_screen(GameScreen(level=level))

	def action_settings(self) -> None:
		self.app.switch_mode('settings')

	def action_quit(self) -> None:
		self.app.exit()