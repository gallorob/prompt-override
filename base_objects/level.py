import os
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List

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

    credentials: Dict[str, str] = Field({})

    infos: str = Field('')
    hints: str = Field('')

    sysprompt: str = Field('')

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
        # replace $RAND$
        while '$RAND$' in level_str:
            level_str = level_str.replace('$RAND$', str(hex(random.getrandbits(128))), 1)
        return Level.model_validate_json(level_str)

    def add_login_msg(self,
                      username: str) -> None:
         self.add_log_msg(f'[INFO] Successful login (User: {username})')
    
    def add_log_msg(self,
                    msg: str):
        logfile = self.fs.get('auth.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logfile.contents += f'\n{timestamp} {msg}'

    @property
    def neuralsys_prompt_snippet(self) -> str:
        vf = self.fs.get(self.sysprompt)
        return vf.contents