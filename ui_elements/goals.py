import json
from typing import List
from textual.widgets import Checkbox, Static
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Center
from textual.screen import Screen

from base_objects.goals import Goal
from base_objects.vfs import VirtualFileSystem
from events import GoalAchieved


class GoalsDisplay(Static):
    def __init__(self, goals: List[Goal], game_screen: Screen):
        super().__init__()
        self.game_screen = game_screen

        self._incomplete = '❌'
        self._completed = '✔'

        self._goals = goals
        self._goal_idx = 0
        self._goals_checkbox: List[Checkbox] = []
        for goal in self._goals:
            cbox = Checkbox(label=goal.name, tooltip=goal.description, value=False, disabled=True)
            cbox.BUTTON_INNER = self._incomplete
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
            curr_checkbox.BUTTON_INNER = self._completed
            self._goal_idx += 1
            self.game_screen.post_message(GoalAchieved(self))
