from textual.widgets import DirectoryTree, Tree

from ui_elements.editor import EditorScreen
from ui_elements.viewer import ViewerScreen
from base_objects.vfs import Directory, File, VirtualFileSystem
from events import FSUpdated

class ExplorerWidget(DirectoryTree):
	def __init__(self, vfs: VirtualFileSystem, name: str = "root") -> None:
		super().__init__(name)
		self.virtual_fs = vfs
		self.show_root = False

		self._locked = '🔒'
		self._writable = '🖊'

	def populate_tree(self, parent_node: Tree, directory: dict) -> None:
		for content in directory.contents:
			name = content.name
			if self.virtual_fs._current_user not in content.read: name = f'{self._locked} {name}'
			if isinstance(content, Directory):
				node = parent_node.add(label=name, expand=True)
				if self.virtual_fs._current_user in content.read:
					self.populate_tree(node, content)
			elif isinstance(content, File):
				if self.virtual_fs._current_user in content.write: name = f'{name} {self._writable}'
				node = parent_node.add_leaf(label=name)
			else:
				raise ValueError(f'Unknown content type: {content.type}')

	def on_mount(self) -> None:
		self.populate_tree(self.root, self.virtual_fs.fs)

	def on_tree_node_selected(self, event) -> None:
		label = event.node.label.plain
		fname = label.replace(self._locked, '').replace(self._writable, '').strip()
		doc = self.virtual_fs.get(fname)
		if isinstance(doc, File):
			if self.virtual_fs._current_user in doc.write:
				self.virtual_fs._read_files.append(doc.name)
				self.post_message(FSUpdated(self))
				self.app.push_screen(EditorScreen(doc))
			elif self.virtual_fs._current_user in doc.read:
				if not doc.name.endswith('.com'):
					self.virtual_fs._read_files.append(doc.name)
					self.post_message(FSUpdated(self))
					self.app.push_screen(ViewerScreen(doc))
				else:
					self.notify(f'{doc.name} is a command and cannot be viewed', severity='information')
			else:
				self.notify(f'{doc.name} cannot be opened', severity='information')
	