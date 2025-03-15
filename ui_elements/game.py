import threading

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Input, MarkdownViewer, TextArea
from textual.binding import Binding

from llm.karma import Karma
from settings import settings

class GameScreen(Screen):

	BINDINGS = [
		Binding(key='escape', action='quit', description='Back to main menu', priority=True)
	]

	def compose(self) -> ComposeResult:
		self.karma = Karma(parent=self)
		with Horizontal():
			# Left panel: Console and Objectives
			with Vertical():
				with Vertical(classes="console-container"):
					yield Static("Console", classes="console-header")
					yield TextArea(id="console_output", soft_wrap=True)
				with Vertical(classes="objective-container"):
					# TODO: Should be a list with checkboxes instead
					yield MarkdownViewer("# Your Objectives\n- ⬜ Complete the mission\n- ✔ Stay undetected\n", show_table_of_contents=False, id="objective_viewer")
			
			# Right panel: Chat widget
			with Vertical(classes="chat-container"):
				yield Static("Chat History", classes="chat-header")
				yield ScrollableContainer(Static("", markup=True, expand=True, id="chat_history"))
				yield Input(placeholder="Type a message...", id="chat_input")

		yield Footer()

	def on_input_submitted(self, event: Input.Submitted) -> None:
		if event.value:
			self.append_chat(f'{settings.chat.player_prefix}{event.value}\n')
			self.stream_chat(event.value)
			event.input.clear()
	
	def stream_chat(self, message: str) -> None:
		self.karma.add_message(msg=message, role='user')
		def fetch_response():
			response_stream = self.karma.chat()  # Generator
			full_response = ""
			self.app.call_from_thread(self.append_chat, settings.chat.karma_prefix)

			for token in response_stream:
				full_response += token
				self.app.call_from_thread(self.append_chat, token)  # Stream tokens
			
			# Store full response in chat history
			self.karma.add_message(msg=full_response, role="assistant")

		threading.Thread(target=fetch_response, daemon=True).start()

	def append_chat(self, text: str) -> None:
		chat_history = self.query_one("#chat_history", Static)
		chat_history.update(chat_history.renderable + text)

		chat_containter: ScrollableContainer = chat_history.parent
		if chat_containter:
			chat_containter.scroll_end(animate=True)

	def action_quit(self) -> None:
		self.app.switch_mode('menu')
