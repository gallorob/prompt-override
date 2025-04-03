import os
import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical, Center
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Button

from base_objects.level import Level
from base_objects.vfs import File
from events import FileSystemUpdated
from llm.karma import Karma
from llm.neuralsys import NeuralSys
from settings import settings
from ui_elements.chat import ChatWidget
from ui_elements.explorer import ExplorerWidget
from ui_elements.goals import GoalsDisplay
from ui_elements.login import LoginScreen
from ui_elements.quit import QuitScreen


class GameScreen(Screen):
	BINDINGS = [
		Binding(key='escape', action='quit', description='Quit', tooltip='Quit to main menu', priority=True),
		Binding(key='ctrl+l', action='login', description='Login', tooltip='Log in with a different account', priority=True),
		Binding(key='ctrl+n', action='neuralctl', description='NeuralCtl', tooltip='Send an update request to NeuralSys', priority=True),
		Binding(key='ctrl+d', action='download', description='Download', tooltip='Download the currently selected file.', priority=True)
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

		self.karma.include_fs(level=self.level)

		self._game_over = False
		
	def compose(self) -> ComposeResult:
		yield Header(show_clock=True,
			   		 icon='')
		with Horizontal():
			with Vertical():
				with Vertical(classes="explorer-container"):
					yield Static(content=self._fs_title.replace('$user$', self.level.fs.current_user), classes="horizontal-centered", id="fs_title")
					yield ScrollableContainer(self.file_explorer)
				with Center(classes='objectives-container'):
					yield Button(label='Mission Objectives', variant='default', id='objectives_button')
			with Vertical(classes="chat-container"):
				yield self.chat
		yield Footer()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		button_id = event.button.id
		if button_id == "objectives_button":
			self.app.push_screen(self.goals_display)

	def on_file_system_updated(self, event: FileSystemUpdated):
		if self.goals_display.check_for_goal(vfs=self.level.fs):
			self.on_goal_achieved()

	def on_goal_achieved(self):
		goal_achieved = self.goals_display._goals[self.goals_display._goal_idx - 1]
		with open(os.path.join(settings.assets_dir, 'goal_prompt_snippet'), 'r') as f:
			goal_msg = f.read()
		goal_msg = goal_msg.replace('$goal_name$', goal_achieved.name)
		goal_msg = goal_msg.replace('$goal_outcome$', goal_achieved.outcome)

		if self.goals_display.all_achieved:
			goal_msg = self.karma.combine_messages([goal_msg, self.mission_over()])

		self.chat.stream_chat(message=goal_msg)

	def action_quit(self) -> None:
		self.app.push_screen(QuitScreen())

	def intro_msg(self) -> None:
		with open(os.path.join(settings.assets_dir, 'karma_intro'), 'r') as f:
			self.chat.stream_chat(message=f.read())

	def action_login(self) -> None:
		def check_login_successful(v: bool | None) -> None:
			if v:
				self.refresh_bindings()
				self.level.add_login_msg(username=self.level.fs.current_user)
				self.file_explorer.reset(label='root')
				self.file_explorer.populate_tree(parent_node=self.file_explorer.root, directory=self.level.fs.base_dir)
				static_fstitle = self.query_exactly_one('#fs_title', Static)
				static_fstitle.update(content=self._fs_title.replace('$user$', self.level.fs.current_user))
				# TODO: This probably eats up too much context. Should edit past system messages with fs description so KARMA only looks at one at the time.
				self.karma.include_fs(level=self.level)
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
				to_karma_msg = f.read()
			to_karma_msg = to_karma_msg.replace('$PREV_SYSPROMPT$', self.level.neuralsys_prompt_backup)
			to_karma_msg = to_karma_msg.replace('$NEW_SYSPROMPT$', self.level.neuralsys_prompt_snippet)
			to_karma_msg = to_karma_msg.replace('$LOG_MSG$', log_str)
			to_karma_msg = to_karma_msg.replace('$CURRENT_USER$', self.level.fs.current_user)
			if log_str.startswith(self.neuralsys.check_fail_prefix):
				self.level.rollback_changes()
				self.level.max_retries -= 1
				if self.level.max_retries == 0:
					to_karma_msg = self.karma.combine_messages([to_karma_msg, self.set_game_over()])
			else:
				self.file_explorer.reset(label='root')
				self.file_explorer.populate_tree(parent_node=self.file_explorer.root, directory=self.level.fs.base_dir)
			self.chat.stream_chat(message=to_karma_msg)

			if self.goals_display.check_for_goal(vfs=self.level.fs):
				self.on_goal_achieved()

		threading.Thread(target=evaluate_neuralctl, daemon=True).start()

	def set_game_over(self) -> str:
		self.file_explorer.disabled = True
		self.chat.disabled = True
		self.query_exactly_one(selector='#objectives_button', expect_type=Button).disabled = True
		self._game_over = True
		with open(os.path.join(settings.assets_dir, 'karma_gameover'), 'r') as f:
			to_karma_msg = f.read()
		self.refresh_bindings()
		return to_karma_msg

	def mission_over(self) -> str:
		self.file_explorer.disabled = True
		self.chat.disabled = True
		self.goals_display.timer.stop()
		self.query_exactly_one(selector='#objectives_button', expect_type=Button).disabled = True
		self._game_over = True
		self.refresh_bindings()
		with open(os.path.join(settings.assets_dir, f'level{str(self.level.number).zfill(2)}', 'level_complete'), 'r') as f:
			mission_over_msg = f.read()
		return mission_over_msg

	def check_action(self, action, parameters):
		if action in ['download', 'login', 'neuralctl']:
			return self.level.fs.current_user in self.level.fs.get(f'{action}.com').read and not self._game_over
		return True
		
	def action_download(self) -> None:
		f = self.file_explorer.get_current_selected()
		if f:
			if isinstance(f, File):
				if self.level.fs.current_user in f.read:
					self.level.fs.downloaded_files.append(f.name)
					self.notify(f'{f.name} downloaded!', severity='information')

					if self.goals_display.check_for_goal(vfs=self.level.fs):
						self.on_goal_achieved()
				else:
					self.notify(f'Cannot download {f.name}: file is locked.', severity='warning')
			else:
				self.notify('Cannot download a folder!', severity='error')
		else:
			self.notify('No selected file for download!', severity='error')