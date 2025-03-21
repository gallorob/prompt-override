import os
import re
from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field

from base_objects.goals import Goal
from base_objects.vfs import VirtualFileSystem
from settings import settings


class Level(BaseModel):
    name: str = Field('level_n')
    number: int = Field(-1)
    descritpion: str = Field('level_desc')
    fs: VirtualFileSystem = Field(None)
    goals: List[Goal] = Field([])


    # more properties to load here
    # eg: hints, story snippets etc...

    @staticmethod
    def _adjust_timestamps(match: re.Match) -> str:
        days, hours, minutes, seconds = map(int, match.groups())
        adjusted_time = datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return adjusted_time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def from_file(fname: str) -> "Level":
        with open(fname, 'r') as f:
            level_str = f.read()
        # replace timestamps
        pattern = re.compile(r"\$TIME-(\d+):(\d+):(\d+):(\d+)\$")
        level_str = pattern.sub(Level._adjust_timestamps, level_str)
        return Level.model_validate_json(level_str)


if __name__ == '__main__':
    import json

    from vfs import Directory

    with open('./fs_lvl1.json', 'r') as f:
        json_str = f.read()
        base_dir = Directory.model_validate_json(json_str)
    
    with open('./goals_lvl1.json', 'r') as f:
        goals_json = json.load(f)
    goals = [Goal.model_validate(goal) for goal in goals_json]
    
    level = Level(name='Access Escalation', number=1, descritpion='The first level in the game',
                  fs=VirtualFileSystem(base_dir=base_dir, known_users=["admin", "guest", "j.davies", "t.miller", "w.jones"], current_user='guest'),
                  goals=goals)

    with open(os.path.join(settings.assets_dir, 'level01.json'), 'w') as f:
        f.write(level.model_dump_json(indent=2))