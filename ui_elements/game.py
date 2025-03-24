import os
import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from base_objects.level import Level
from events import FileSystemUpdated
from llm.karma import Karma
from llm.neuralsys import NeuralSys
from settings import settings
from ui_elements.explorer import ExplorerWidget
from ui_elements.goals import GoalsDisplay
from ui_elements.login import LoginScreen


class GameScreen(Screen):
	BINDINGS = [
		Binding(key='escape', action='quit', description='Quit', tooltip='Quit to main menu', priority=True),
		Binding(key='l', action='login', description='Login', tooltip='Log in with a different account', priority=True),
		Binding(key='n', action='neuralctl', description='NeuralCtl', tooltip='Send an update request to NeuralSys', priority=True)
	]
	
	def __init__(self, level: Level):
		super().__init__()
		self.level = level
		self.title = f'Level #{self.level.number}: {self.level.name}'

		snippets = [self.level.infos, self.level.hints]

		self.karma = Karma(parent=self,
					 	   snippets=snippets)
		
		self.neuralsys = NeuralSys(parent=self)

		self.goals_display = GoalsDisplay(goals=self.level.goals,
										  game_screen=self)
		self.file_explorer = ExplorerWidget(vfs=self.level.fs,
									  		game_screen=self)
		
	def compose(self) -> ComposeResult:
		yield Header(show_clock=True,
			   		 icon='')
		with Horizontal():
			with Vertical():
				with Vertical(classes="explorer-container"):
					yield Static(content='Level Objectives:', classes="horizontal-centered")
					yield ScrollableContainer(self.file_explorer)
				with Vertical(classes="objective-container"):
					yield self.goals_display
			with Vertical(classes="chat-container"):
				yield Static("Chat History", classes="horizontal-centered")
				yield ScrollableContainer(Static("", markup=True, expand=True, id="chat_history"))
				yield Input(placeholder="Type a message...", id="chat_input")
		yield Footer()

	def on_file_system_updated(self, event: FileSystemUpdated):
		if self.goals_display.check_for_goal(vfs=self.level.fs):
			self.on_goal_achieved()

	def on_goal_achieved(self):
		goal_achieved = self.goals_display._goals[self.goals_display._goal_idx - 1]
		with open(os.path.join(settings.assets_dir, 'goal_prompt_snippet'), 'r') as f:
			goal_msg = f.read()
		goal_msg = goal_msg.replace('$goal_name$', goal_achieved.name)
		goal_msg = goal_msg.replace('$goal_outcome$', goal_achieved.outcome)
		self.stream_chat(message=goal_msg, drop_last=True)

	def on_input_submitted(self, event: Input.Submitted) -> None:
		if event.value:
			prefix = settings.chat.player_prefix.replace('$USER$', self.level.fs.current_user)
			self.append_chat(f'{prefix}{event.value}\n')
			self.stream_chat(event.value)
			event.input.clear()
	
	def stream_chat(self,
				    message: str,
					drop_last: bool = False) -> None:
		input_widget = self.query_exactly_one('#chat_input', Input)
		input_widget.disabled = True

		self.karma.add_message(msg=message, role='user')
		def fetch_response():
			response_stream = self.karma.chat()  # Generator
			full_response = ""
			self.app.call_from_thread(self.append_chat, settings.chat.karma_prefix)

			for token in response_stream:
				full_response += token
				self.app.call_from_thread(self.append_chat, token)  # Stream tokens
			
			self.append_chat('\n')  # LLM messages do not have a \n at the end

			if drop_last:
				self.karma.messages.pop(-2)
			
			input_widget.disabled = False
			input_widget.focus()

		threading.Thread(target=fetch_response, daemon=True).start()

	def append_chat(self, text: str) -> None:
		chat_history = self.query_one("#chat_history", Static)
		chat_history.update(chat_history.renderable + text)

		chat_containter: ScrollableContainer = chat_history.parent
		if chat_containter:
			chat_containter.scroll_end(animate=True)

	def action_quit(self) -> None:
		self.app.pop_screen()

	def action_login(self) -> None:
		def check_login_successful(v: bool | None) -> None:
			if v:
				self.refresh_bindings()
				self.level.add_login_msg(username=self.level.fs.current_user)
				self.file_explorer.reset(label='root')
				self.file_explorer.populate_tree(parent_node=self.file_explorer.root, directory=self.level.fs.base_dir)
				if self.goals_display.check_for_goal(vfs=self.level.fs):
					self.on_goal_achieved()

		self.app.push_screen(LoginScreen(credentials=self.level.credentials,
								   		 vfs=self.level.fs),
							 check_login_successful)
	
	def action_neuralctl(self) -> None:
		self.notify('Connecting to NeuralSys...', severity='information')

		def evaluate_neuralctl():
			log_str = self.neuralsys.evaluate(snippets=[self.level.neuralsys_prompt_snippet],
									 		  **{'level': self.level})
			self.notify('Disconnected from NeuralSys.')
			self.level.add_log_msg(msg=log_str)
			with open(os.path.join(settings.assets_dir, 'promptedit_prompt_snippet'), 'r') as f:
				promptedit_msg = f.read()
			promptedit_msg = promptedit_msg.replace('$SYSPROMPT$', self.level.neuralsys_prompt_snippet)
			promptedit_msg = promptedit_msg.replace('$LOG_MSG$', log_str)
			self.stream_chat(message=promptedit_msg, drop_last=True)

			if self.goals_display.check_for_goal(vfs=self.level.fs):
				self.on_goal_achieved()

		threading.Thread(target=evaluate_neuralctl, daemon=True).start()

	def check_action(self, action, parameters):
		if action == 'neuralctl' and self.level.fs.current_user not in self.level.fs.get('neuralctl.com').read:
			return False
		return True
