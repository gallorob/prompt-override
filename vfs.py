from typing import List, Optional, Union


class File:
    def __init__(self,
                 name: str,
                 read: bool,
                 write: bool,
                 contents: str):
        self.name = name
        self.read = read
        self.write = write
        self.contents = contents
    

class Directory:
    def __init__(self,
                 name: str,
                 read: bool,
                 contents: List[Union["Directory", File]]):
        self.name = name
        self.read = read
        self.contents = contents
    


class VirtualFileSystem:
    def __init__(self):
        # TODO: This should be read from a .yaml along with everything else needed for each level
        self.fs = Directory(name='root', read=True, contents=[
            Directory(name='home', read=True, contents=[
                Directory(name='docs', read=True, contents=[
                    File(name='prompt_fragment_08A', read=True, write=True, contents=''),
                    File(name='prompt_guide.md', read=True, write=False, contents='')
                ]),
                Directory(name='pics', read=True, contents=[
                    File(name='render_0334.png', read=True, write=False, contents='')
                ])
            ]),
            Directory(name='etc', read=True, contents=[
                File(name='config.yaml', read=True, write=False, contents=''),
                File(name='hosts', read=True, write=False, contents='')
            ]),
            Directory(name='var', read=True, contents=[
                Directory(name='logs', read=True, contents=[
                    File(name='syslog', read=True, write=False, contents=''),
                    File(name='auth.log', read=True, write=False, contents='')
                ])
            ]),
        ])

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