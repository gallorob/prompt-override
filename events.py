from textual.events import Message
from textual.widget import Widget


class FileSystemUpdated(Message):
    def __init__(self, sender: Widget):
        super().__init__()
        self.sender = sender
        self.stop = False


class GoalAchieved(Message):
    def __init__(self, sender: Widget):
        super().__init__()
        self.sender = sender
        self.stop = False
