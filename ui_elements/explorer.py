from textual.screen import Screen
from textual.widgets import DirectoryTree, Tree

from base_objects.vfs import Directory, File, VirtualFileSystem
from events import FileSystemUpdated
from ui_elements.editor import EditorScreen
from ui_elements.viewer import ViewerScreen


class ExplorerWidget(DirectoryTree):
	def __init__(self, game_screen: Screen, vfs: VirtualFileSystem, name: str = "root") -> None:
		super().__init__(name)
		self.game_screen = game_screen

		self.vfs = vfs
		self.show_root = False

		self._locked = '🔒'
		self._writable = '🖊'

	def populate_tree(self, parent_node: Tree, directory: Directory) -> None:
		for content in directory.contents:
			name = content.name
			if self.vfs.current_user not in content.read: name = f'{self._locked} {name}'
			if isinstance(content, Directory):
				node = parent_node.add(label=name, expand=True)
				if self.vfs.current_user in content.read:
					self.populate_tree(node, content)
			elif isinstance(content, File):
				if self.vfs.current_user in content.write: name = f'{name} {self._writable}'
				node = parent_node.add_leaf(label=name)
			else:
				raise ValueError(f'Unknown content type: {content.type}')
			
	def on_mount(self):
		self.populate_tree(parent_node=self.root, directory=self.vfs.base_dir)

	def on_tree_node_selected(self, event) -> None:
		label = event.node.label.plain
		fname = label.replace(self._locked, '').replace(self._writable, '').strip()
		doc = self.vfs.get(fname)
		if isinstance(doc, File):
			if self.vfs.current_user in doc.write:
				self.vfs.read_files.append(doc.name)
				self.game_screen.post_message(FileSystemUpdated(self))
				self.app.push_screen(EditorScreen(doc))
			elif self.vfs.current_user in doc.read:
				if not doc.is_command:
					self.vfs.read_files.append(doc.name)
					self.game_screen.post_message(FileSystemUpdated(self))
					self.app.push_screen(ViewerScreen(doc))
				else:
					self.notify(f'{doc.name} is a command', severity='information')
			else:
				self.notify(f'{doc.name} cannot be opened', severity='information')
	