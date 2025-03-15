from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Center, Vertical, Container
from textual.widgets import Button, Static, Footer
from textual.binding import Binding

from settings import settings

class MenuScreen(Screen):

	BINDINGS = [
		Binding(key='n', action='new_game', description='Start a [N]ew game.', priority=True),
		Binding(key='o', action='options', description='Edit [O]ptions.', priority=True),
		Binding(key='escape', action='quit', description='[Esc]ape to reality.', priority=True)
	]

	def compose(self) -> ComposeResult:
		yield Center(
			Static(self.load_title(), id="title"),
			Container(
				Vertical(
					Button("New Game", id="new_game"),
					Button("Options", id="options"),
					Button("Exit", id="exit"),
					id="menu_buttons"
				)
			))
		yield Footer()

	def load_title(self) -> str:
		try:
			with open(settings.title, "r", encoding="utf-8") as file:
				return file.read()
		except FileNotFoundError:
			return "[Title Missing]"

	def on_button_pressed(self, event: Button.Pressed) -> None:
		button_id = event.button.id
		if button_id == "new_game":
			self.action_new_game()
		elif button_id == "options":
			self.action_options()
		elif button_id == "exit":
			self.action_quit()

	def action_new_game(self) -> None:
		self.app.switch_mode('in_game')

	def action_options(self) -> None:
		self.app.switch_mode('options')

	def action_quit(self) -> None:
		self.app.exit()