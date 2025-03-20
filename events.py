from textual.widget import Widget
from textual.events import Message


class FSUpdated(Message):
    def __init__(self, sender: Widget):
        super().__init__()
        self.sender = sender
        self.stop = False
