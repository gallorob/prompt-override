from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta


class File(BaseModel):
    name: str = Field('')
    read: List[str] = Field([])
    write: List[str] = Field([])
    contents: str = Field('')
    

class Directory(BaseModel):
    name: str = Field('')
    read: List[str] = Field([])
    contents: List[Union['Directory', File]] = Field([])
    


class VirtualFileSystem:
    # TODO: Should be loaded based on level selected, but for now it's fine
    def __init__(self):
        with open('./fs_lvl1.json', 'r') as f:
            json_str = f.read()

            curr_time = datetime.now()
            # TODO: This should be done differently, likely with the timedelta defined in the text and evaluated here
            time01 = curr_time - timedelta(hours=1, minutes=32, seconds=12)
            time02 = curr_time - timedelta(hours=1, minutes=12, seconds=6)
            tformat = "%Y/%m/%d %H:%M:%S"
            json_str = json_str.replace('$TIME_01$', time01.strftime(tformat))
            json_str = json_str.replace('$TIME_02$', time02.strftime(tformat))
            json_str = json_str.replace('$TIME_03$', curr_time.strftime(tformat))

            self.fs = Directory.model_validate_json(json_str)
        self.known_users = ["admin", "guest", "j.davies", "t.miller", "w.jones"]
        self._current_user = 'guest'

        self._read_files = []

    def get(self, fname: str, directory: Optional[Directory] = None) -> Union[Directory, File]:
        if directory is None:
            directory = self.fs  # Start from root if no directory is specified

        for item in directory.contents:
            if item.name == fname:
                return item
            if isinstance(item, Directory):
                result = self.get(fname, item)
                if result:
                    return result
        return None
    
    def has_read(self, fname: str) -> bool:
        return fname in self._read_files

    def is_logged_as(self, username: str) -> bool:
        return self._current_user == username
