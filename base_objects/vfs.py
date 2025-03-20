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


# TODO: Reintegrate current time in files when possible, figure out a nicer way to define this in text.
# This should be done differently, likely with the timedelta defined in the text and evaluated here
#         curr_time = datetime.now()
#         time01 = curr_time - timedelta(hours=1, minutes=32, seconds=12)
#         time02 = curr_time - timedelta(hours=1, minutes=12, seconds=6)
#         tformat = "%Y/%m/%d %H:%M:%S"
#         json_str = json_str.replace('$TIME_01$', time01.strftime(tformat))
#         json_str = json_str.replace('$TIME_02$', time02.strftime(tformat))
#         json_str = json_str.replace('$TIME_03$', curr_time.strftime(tformat))


class VirtualFileSystem(BaseModel):
    base_dir: Directory = Field(None)
    known_users: List[str] = Field([])

    current_user: str = Field('')
    read_files: List[str] = Field([])

    def get(self, fname: str, directory: Optional[Directory] = None) -> Union[Directory, File]:
        if directory is None:
            directory = self.base_dir  # Start from root if no directory is specified

        for item in directory.contents:
            if item.name == fname:
                return item
            if isinstance(item, Directory):
                result = self.get(fname, item)
                if result:
                    return result
        return None
    
    def has_read(self, fname: str) -> bool:
        return fname in self.read_files

    def is_logged_as(self, username: str) -> bool:
        return self.current_user == username
