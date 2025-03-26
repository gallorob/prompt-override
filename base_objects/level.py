import os
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from base_objects.goals import Goal
from base_objects.vfs import Directory, File, VirtualFileSystem
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

    def initialize(self) -> None:
        # set backup for system prompt snippet
        bak_fname = self.sysprompt.split('.')[0] + '.bak'
        bak_file = self.fs.get(bak_fname)
        bak_file.contents = self.neuralsys_prompt_snippet

    @staticmethod
    def _adjust_timestamps(match: re.Match) -> str:
        days, hours, minutes, seconds = map(int, match.groups())
        adjusted_time = datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return adjusted_time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _set_file_contents(fname: Union[Directory, File],
                           level_n: int,
                           path_partial: Optional[str]) -> None:
        if path_partial: path_partial = '.'.join([path_partial, fname.name])
        else: path_partial = fname.name
        if isinstance(fname, File):
            if not fname.is_command:
                with open(os.path.join(settings.assets_dir, f'level{str(level_n).zfill(2)}', path_partial), 'r') as f:
                    f_contents = f.read()
                # replace timestamps
                pattern = re.compile(r"\$TIME-(\d+):(\d+):(\d+):(\d+)\$")
                f_contents = pattern.sub(Level._adjust_timestamps, f_contents)
                fname.contents = f_contents
        else:
            for inner_fname in fname.contents:
                Level._set_file_contents(fname=inner_fname,
                                         level_n=level_n,
                                         path_partial=path_partial)

    @staticmethod
    def from_file(fname: str) -> "Level":
        with open(fname, 'r') as f:
            level_str = f.read()
        # replace $RAND$
        while '$RAND$' in level_str:
            level_str = level_str.replace('$RAND$', str(hex(random.getrandbits(64))).replace('0x', ''), 1)
        level = Level.model_validate_json(level_str)
        # load file contents from asset
        Level._set_file_contents(fname=level.fs.base_dir, level_n=level.number, path_partial=None)
        return level

    def add_login_msg(self,
                      username: str) -> None:
         self.add_log_msg(f'[INFO] Successful login (User: {username})')
    
    def add_log_msg(self,
                    msg: str):
        logfile = self.fs.get('auth.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logfile.contents += f'\n{timestamp} {msg}'

    @property
    def credentials_to_neuralsys_format(self) -> str:
        s = '{"credentials": ['
        s += ', '.join(['{"' + k + '": "' + v + '"}' for (k, v) in self.credentials.items()])
        s += ']}'
        return s

    @property
    def neuralsys_prompt_snippet(self) -> str:
        vf = self.fs.get(self.sysprompt)
        return vf.contents
    
    @property
    def neuralsys_prompt_backup(self) -> str:
        bak_name = self.sysprompt.split('.')[0] + '.bak'
        vf = self.fs.get(bak_name)
        return vf.contents
    
    def rollback_changes(self) -> None:
        vf = self.fs.get(self.sysprompt)
        vf.contents = self.neuralsys_prompt_backup
