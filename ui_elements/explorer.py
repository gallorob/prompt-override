from typing import Union
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

	def _get_parent_directory(self, node: Tree) -> Directory:
		path = []
		while node.parent.label.plain != self.vfs.base_dir.name:
			path.append(node.parent.label.plain)
			node = node.parent
		parent_dir = self.vfs.base_dir
		for path_dir in reversed(path):
			parent_dir = self.vfs.get(path_dir, directory=parent_dir)
		return parent_dir

	def _fs_obj_from_node(self,
					      node: Tree) -> Union[Directory, File]:
		label = node.label.plain
		fname = label.replace(self._locked, '').replace(self._writable, '').strip()
		parent_dir = self._get_parent_directory(node=node)
		return self.vfs.get(fname, directory=parent_dir)

	def on_tree_node_selected(self, event) -> None:
		doc = self._fs_obj_from_node(node=event.node)
		if isinstance(doc, File):
			if self.vfs.current_user in doc.write:
				self.vfs.read_files.append(doc.name)
				self.game_screen.post_message(FileSystemUpdated(self))
				self.app.push_screen(EditorScreen(doc, bak=self.vfs.get(doc.name.split('.')[0] + '.bak')))
			elif self.vfs.current_user in doc.read:
				if not doc.is_command:
					self.vfs.read_files.append(doc.name)
					self.game_screen.post_message(FileSystemUpdated(self))
					self.app.push_screen(ViewerScreen(doc))
				else:
					self.notify(f'{doc.name} is a command', severity='information')
			else:
				self.notify(f'{doc.name} cannot be opened', severity='information')
	
	def get_current_selected(self) -> Union[File, Directory]:
		node = self.get_node_at_line(self.cursor_line)
		if node:
			return self._fs_obj_from_node(node=node)
		return None
	