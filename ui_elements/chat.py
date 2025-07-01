import threading

from base_objects.level import Level
from llm.karma import Karma
from settings import settings
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Input, Static


class ChatWidget(Widget):
    def __init__(self, game_screen: Screen, level: Level, karma: Karma):
        super().__init__()
        self.level = level
        self.game_screen = game_screen
        self.karma = karma
        self._title = "Chat History$UNREAD$"
        self._unread = 0

        self.title = Static(
            self._title.replace("$UNREAD$", self._unread_str()),
            classes="horizontal-centered",
            id="chat_title",
        )
        self.history = ScrollableContainer(
            Static("", markup=True, expand=True, id="chat_history")
        )
        self.input = Input(placeholder="Type a message...", id="chat_input")

        self.watch(
            self.title,
            attribute_name="has_focus",
            callback=self.update_title,
            init=False,
        )
        self.watch(
            self.history,
            attribute_name="has_focus",
            callback=self.update_title,
            init=False,
        )
        self.watch(
            self.input,
            attribute_name="has_focus",
            callback=self.update_title,
            init=False,
        )

    def _unread_str(self) -> str:
        return "" if self._unread == 0 else f" [r]({self._unread})[/r]"

    def compose(self):
        yield self.title
        yield self.history
        yield self.input

    def update_title(self):
        self._unread = 0
        title_static = self.query_one("#chat_title", Static)
        title_static.update(self._title.replace("$UNREAD$", self._unread_str()))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value:
            prefix = settings.chat.player_prefix.replace(
                "$USER$", self.level.fs.current_user
            )
            self.append_chat(f"{prefix}{event.value}\n")
            self.stream_chat(event.value)
            event.input.clear()

    def stream_chat(self, message: str) -> None:
        input_widget = self.query_exactly_one("#chat_input", Input)
        was_focused = input_widget.has_focus
        input_widget.disabled = True

        self.karma.add_message(msg=message, role="user")

        def fetch_response():
            response_stream = self.karma.chat()  # Generator
            full_response = ""
            self.app.call_from_thread(self.append_chat, settings.chat.karma_prefix)

            for token in response_stream:
                full_response += token
                self.app.call_from_thread(self.append_chat, token)  # Stream tokens
            self.append_chat("\n")  # LLM messages do not have a \n at the end

            input_widget.disabled = False
            if was_focused:
                input_widget.focus()
            if not was_focused:
                self._unread += 1
                title_static = self.query_exactly_one("#chat_title", Static)
                title_static.update(self._title.replace("$UNREAD$", self._unread_str()))

        threading.Thread(target=fetch_response, daemon=True).start()

    def append_chat(self, text: str) -> None:
        chat_history = self.query_one("#chat_history", Static)
        chat_history.update(chat_history.renderable + text)

        chat_containter: ScrollableContainer = chat_history.parent
        if chat_containter:
            chat_containter.scroll_end(animate=True)
