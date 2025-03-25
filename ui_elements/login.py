from typing import Dict
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, Center
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Static, Input, Button

from base_objects.vfs import VirtualFileSystem


class LoginScreen(ModalScreen):
	def __init__(self,  credentials: Dict[str, str], vfs: VirtualFileSystem) -> None:
		super().__init__()
		self.credentials = credentials
		self.vfs = vfs
		
		self.title = 'Login'
		
	
	BINDINGS = [
		Binding('escape', 'close_window', 'Cancel', priority=True),
		Binding('enter', 'try_login', 'Login', priority=True)
	]

	def compose(self) -> ComposeResult:
		yield Header(show_clock=True, icon='')
		yield Center(
			Container(
				Vertical(
					Static("Username:"), Input(value=self.vfs.current_user, id="input_username"),
					Static("Password:"), Input(value=self.credentials[self.vfs.current_user], id="input_password"),
					Center(Button(label='Log In', id='button_login'))
				)
			),
			id='login'
		)
		yield Footer()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		button_id = event.button.id
		if button_id == "button_login":
			self.action_try_login()

	def action_try_login(self):
		username_input = self.query_exactly_one('#input_username', Input)
		username = username_input.value
		password_input = self.query_exactly_one('#input_password', Input)
		password = password_input.value
		if username != self.vfs.current_user:
			if username not in self.vfs.known_users:
				self.notify(f'User {username} not found.', title='Login', severity='error')
			elif password != self.credentials[username]:
				self.notify(f'Invalid password for user {username}.', title='Login', severity='error')
			else:
				self.vfs.current_user = username
				self.notify(f'Logged in as {username}', title='Login', severity='information')
				self.dismiss(True)

	def action_close_window(self):
		self.dismiss(False)
	