import os
import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from base_objects.level import Level
from events import FileSystemUpdated, GoalAchieved
from llm.karma import Karma
from settings import settings
from ui_elements.explorer import ExplorerWidget
from ui_elements.goals import GoalsDisplay


class GameScreen(Screen):
	def __init__(self, level: Level):
		super().__init__()
		self.level = level
		self.title = f'Level #{self.level.number}: {self.level.name}'

		# TODO: Should be defined by level
		snippets = []
		for fname in [os.path.join(settings.assets_dir, 'level01_infos_snippet'),
					  os.path.join(settings.assets_dir, 'level01_hints_snippet')]:
			with open(fname, 'r') as f:
				snippets.append(f.read())

		self.karma = Karma(parent=self,
					 	   snippets=snippets)

		self.goals_display = GoalsDisplay(goals=self.level.goals,
										  game_screen=self)
		self.file_explorer = ExplorerWidget(vfs=self.level.fs,
									  		game_screen=self)

	BINDINGS = [
		Binding(key='escape', action='quit', description='Quit to main menu', priority=True)
	]

	def compose(self) -> ComposeResult:

		yield Header(show_clock=True,
			   		 icon='')

		with Horizontal():
			with Vertical():
				with Vertical(classes="explorer-container"):
					yield Static("File Explorer", classes="horizontal-centered")
					yield ScrollableContainer(self.file_explorer)
				with Vertical(classes="objective-container"):
					yield self.goals_display
			
			with Vertical(classes="chat-container"):
				yield Static("Chat History", classes="horizontal-centered")
				yield ScrollableContainer(Static("", markup=True, expand=True, id="chat_history"))
				yield Input(placeholder="Type a message...", id="chat_input")

		yield Footer()

	def on_file_system_updated(self, event: FileSystemUpdated):
		self.goals_display.check_for_goal(vfs=self.level.fs)
		

	def on_goal_achieved(self, event: GoalAchieved):
		goal_achieved = self.goals_display._goals[self.goals_display._goal_idx - 1]
		with open(os.path.join(settings.assets_dir, 'goal_prompt_snippet'), 'r') as f:
			goal_msg = f.read()
		goal_msg = goal_msg.replace('$goal_name$', goal_achieved.name)
		goal_msg = goal_msg.replace('$goal_outcome$', goal_achieved.outcome)
		self.stream_chat(message=goal_msg, drop_last=True)

	def on_input_submitted(self, event: Input.Submitted) -> None:
		if event.value:
			self.append_chat(f'{settings.chat.player_prefix}{event.value}\n')
			self.stream_chat(event.value)
			event.input.clear()
			# shold disable the input until the answer is streamed
	
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
