from textual.widgets import DirectoryTree, Tree
from textual.containers import ScrollableContainer
from textual.app import ComposeResult

class FakeDirectoryTree(DirectoryTree):
    def __init__(self, name: str = "root") -> None:
        super().__init__(name)
        self.virtual_fs = {
            "root": {
                "home": {
                    "user": {
                        "docs": {"prompt_fragment_08A": 'text_file', "prompt_guide.md": 'text_file'},
                        "pics": {"render_0334.png": 'image_file'},
                    }
                },
                "etc": {
                    "config.yaml": 'text_file',
                    "hosts": 'text_file',
                },
                "var": {
                    "logs": {"syslog": 'text_file', "auth.log": 'text_file'}
                },
            }
        }

        self.locked_files = ['logs', 'hosts']

        self.show_root = False

    def populate_tree(self, parent_node: Tree, directory: dict) -> None:
        for name, contents in directory.items():
            if name in self.locked_files:
                name = f'🔒 {name}'
            if isinstance(contents, dict):
                node = parent_node.add(name, expand=True)
                if not name.startswith('🔒'):
                    self.populate_tree(node, contents)
            else:
                node = parent_node.add_leaf(name)

    def on_mount(self) -> None:
        self.populate_tree(self.root, self.virtual_fs["root"])
    