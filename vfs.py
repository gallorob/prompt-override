from typing import List, Optional, Union
from pydantic import BaseModel, Field


class File(BaseModel):
    name: str = Field('')
    read: bool = Field(True)
    write: bool = Field(False)
    contents: str = Field('')
    

class Directory(BaseModel):
    name: str = Field('')
    read: bool = Field(True)
    contents: List[Union['Directory', File]] = Field([])
    


class VirtualFileSystem:
    def __init__(self):
        # TODO: Should be loaded based on level selected, but for now it's fine
        with open('./fs_lvl1.json', 'r') as f:
            self.fs = Directory.model_validate_json(f.read())

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
