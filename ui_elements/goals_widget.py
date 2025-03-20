import json
from typing import Dict, List
from textual.widgets import Checkbox, Static
from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Center

from goals import Goal
from vfs import VirtualFileSystem


class GoalsDisplay(Widget):
    def __init__(self):
        super().__init__()

        self.INCOMPLETE_GOAL = '❌'
        self.COMPLETED_GOAL = '✔'

        # TODO: Should be loaded with the level
        with open('./goals_lvl1.json', 'r') as f:
            goals_json = json.load(f)
        self._goals = [Goal.model_validate(goal) for goal in goals_json]
        self._goal_idx = 0
        self._goals_checkbox = []
        for goal in self._goals:
            cbox = Checkbox(label=goal.name, tooltip=goal.description, value=False, disabled=True)
            cbox.BUTTON_INNER = self.INCOMPLETE_GOAL
            self._goals_checkbox.append(cbox)
        
    def compose(self) -> ComposeResult:
        yield Static(content='Level Objectives:', classes="horizontal-centered")
        yield Center(
            VerticalScroll(*self._goals_checkbox)
        )
    
    @property
    def next_goal(self) -> Goal:
        return self._goals[self._goal_idx]
    
    def check_for_goal(self, vfs: VirtualFileSystem) -> None:
        curr_goal = self.next_goal
        if curr_goal.resolved(vfs=vfs):
            curr_checkbox = self._goals_checkbox[self._goal_idx]
            curr_checkbox.value = True
            curr_checkbox.BUTTON_INNER = self.COMPLETED_GOAL
            self._goal_idx += 1
