from typing import List, Optional

from base_objects.goals import Goal
from base_objects.vfs import VirtualFileSystem

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Button, Checkbox, Footer, Static


class GoalsDisplay(ModalScreen):
    BINDINGS = [
        Binding("escape", "close_window", "Cancel", priority=True),
    ]

    def __init__(self, goals: List[Goal], game_screen: Screen):
        super().__init__()
        self.game_screen = game_screen

        self._incomplete = "❌"
        self._completed = "✔"

        self._goals = goals
        self._goal_idx = 0
        self._goals_checkbox: List[Checkbox] = []
        for goal in self._goals:
            cbox = Checkbox(
                label=goal.name, tooltip=goal.description, value=False, disabled=True
            )
            cbox.BUTTON_INNER = self._incomplete
            self._goals_checkbox.append(cbox)
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Center(
            Static(content="Level Objectives", classes="horizontal-centered"),
            Center(Container(VerticalScroll(*self._goals_checkbox))),
            id="objectives",
        )
        yield Footer()

        if hasattr(self, "timer") and self.timer:
            self.timer.stop()
            btn = self.game_screen.query_exactly_one(
                selector="#objectives_button", expect_type=Button
            )
            btn.label = btn.label.plain

    def flash_button(self) -> None:
        btn = self.game_screen.query_exactly_one(
            selector="#objectives_button", expect_type=Button
        )
        if "[reverse]" in btn.label.markup:
            btn.label = btn.label.plain
        else:
            btn.label = f"[r]{btn.label.plain}[/r]"

    def start_timer(self) -> None:
        self.timer = self.set_interval(interval=0.5, callback=self.flash_button)

    @property
    def next_goal(self) -> Goal:
        return self._goals[self._goal_idx]

    @property
    def all_achieved(self) -> bool:
        return self._goal_idx == len(self._goals)

    def check_for_goal(self, vfs: VirtualFileSystem) -> bool:
        curr_goal = self.next_goal
        if curr_goal.resolved(vfs=vfs):
            curr_checkbox = self._goals_checkbox[self._goal_idx]
            curr_checkbox.value = True
            curr_checkbox.tooltip = curr_goal.outcome
            curr_checkbox.BUTTON_INNER = self._completed
            self._goal_idx += 1
            self._viewed = False
            self.start_timer()
            return True
        return False

    def action_close_window(self):
        self.app.pop_screen()
