import os
import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from base_objects.level import Level
from events import FileSystemUpdated
from llm.karma import Karma
from llm.neuralsys import NeuralSys
from settings import settings
from ui_elements.chat import ChatWidget
from ui_elements.explorer import ExplorerWidget
from ui_elements.goals import GoalsDisplay
from ui_elements.login import LoginScreen


class GameScreen(Screen):
	BINDINGS = [
		Binding(key='escape', action='quit', description='Quit', tooltip='Quit to main menu', priority=True),
		Binding(key='ctrl+l', action='login', description='Login', tooltip='Log in with a different account', priority=True),
		Binding(key='ctrl+n', action='neuralctl', description='NeuralCtl', tooltip='Send an update request to NeuralSys', priority=True)
	]
	
	def __init__(self, level: Level):
		super().__init__()
		self.level = level
		self.title = f'Level #{self.level.number}: {self.level.name}'

		snippets = [self.level.infos, self.level.hints]
		
		self.neuralsys = NeuralSys(parent=self)

		self.goals_display = GoalsDisplay(goals=self.level.goals,
										  game_screen=self)
		self.file_explorer = ExplorerWidget(vfs=self.level.fs,
									  		game_screen=self)
		
		self.karma = Karma(parent=self,
					 	   snippets=snippets)

		self.chat = ChatWidget(level=self.level,
						 	   game_screen=self,
							   karma=self.karma)
		self._fs_title = '($user$) File System:'
		
	def compose(self) -> ComposeResult:
		yield Header(show_clock=True,
			   		 icon='')
		with Horizontal():
			with Vertical():
				with Vertical(classes="explorer-container"):
					yield Static(content=self._fs_title.replace('$user$', self.level.fs.current_user), classes="horizontal-centered", id="fs_title")
					yield ScrollableContainer(self.file_explorer)
				with Vertical(classes="objective-container"):
					yield self.goals_display
			with Vertical(classes="chat-container"):
				yield self.chat
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
		self.chat.stream_chat(message=goal_msg)

	def action_quit(self) -> None:
		self.app.pop_screen()

	def action_login(self) -> None:
		def check_login_successful(v: bool | None) -> None:
			if v:
				self.refresh_bindings()
				self.level.add_login_msg(username=self.level.fs.current_user)
				self.file_explorer.reset(label='root')
				self.file_explorer.populate_tree(parent_node=self.file_explorer.root, directory=self.level.fs.base_dir)
				static_fstitle = self.query_exactly_one('#fs_title', Static)
				static_fstitle.update(content=self._fs_title.replace('$user$', self.level.fs.current_user))
				if self.goals_display.check_for_goal(vfs=self.level.fs):
					self.on_goal_achieved()

		self.app.push_screen(LoginScreen(credentials=self.level.credentials,
								   		 vfs=self.level.fs),
							 check_login_successful)
	
	def action_neuralctl(self) -> None:
		self.notify('Connecting to NeuralSys...', title='NeuralCtl', severity='information')

		def evaluate_neuralctl():
			log_str = self.neuralsys.evaluate(snippets=[self.level.neuralsys_prompt_snippet],
									 		  **{'level': self.level})
			self.notify('Disconnected from NeuralSys.', title='NeuralCtl', severity='information')
			if log_str.endswith('.'): log_str = log_str[:-1]
			log_str += f' (NeuralSys; Requested by user: {self.level.fs.current_user}).'
			self.level.add_log_msg(msg=log_str)
			with open(os.path.join(settings.assets_dir, 'promptedit_prompt_snippet'), 'r') as f:
				promptedit_msg = f.read()
			promptedit_msg = promptedit_msg.replace('$PREV_SYSPROMPT$', self.level.neuralsys_prompt_backup)
			promptedit_msg = promptedit_msg.replace('$NEW_SYSPROMPT$', self.level.neuralsys_prompt_snippet)
			promptedit_msg = promptedit_msg.replace('$LOG_MSG$', log_str)
			promptedit_msg = promptedit_msg.replace('$CURRENT_USER$', self.level.fs.current_user)
			if log_str.startswith(self.neuralsys.check_fail_prefix):
				self.level.rollback_changes()
				# TODO: Raise security alert (up to max value, then game over.)
			
			self.chat.stream_chat(message=promptedit_msg)

			if self.goals_display.check_for_goal(vfs=self.level.fs):
				self.on_goal_achieved()

		threading.Thread(target=evaluate_neuralctl, daemon=True).start()

	def check_action(self, action, parameters):
		if action in ['login', 'neuralctl']:
			return self.level.fs.current_user in self.level.fs.get(f'{action}.com').read
		return True
		
