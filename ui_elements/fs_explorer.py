from textual.widgets import DirectoryTree, Tree

from ui_elements.editor import EditorScreen
from vfs import Directory, File, VirtualFileSystem

class FakeDirectoryTree(DirectoryTree):
	def __init__(self, name: str = "root") -> None:
		super().__init__(name)
		self.virtual_fs = VirtualFileSystem()
		self.show_root = False

		self._locked = '🔒'
		self._writable = '🖊'

	def populate_tree(self, parent_node: Tree, directory: dict) -> None:
		for content in directory.contents:
			name = content.name
			if not content.read: name = f'{self._locked} {name}'
			if isinstance(content, Directory):
				node = parent_node.add(label=name, expand=True)
				if content.read:
					self.populate_tree(node, content)
			elif isinstance(content, File):
				if content.write: name = f'{name} {self._writable}'
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
			if doc.write:
				self.app.push_screen(EditorScreen(doc))
			else:
				self.notify(f'{doc.name} cannot be edited', severity='information')
	