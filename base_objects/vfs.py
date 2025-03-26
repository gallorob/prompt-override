from typing import List, Optional, Union

from pydantic import BaseModel, Field


class File(BaseModel):
	name: str = Field('')
	read: List[str] = Field([])
	write: List[str] = Field([])
	contents: str = Field('')

	@property
	def is_command(self):
		return self.name.endswith('.com')
	
	def to_neuralsys_format(self, username: str) -> str:
		return '{"file_name": "' + self.name + '"}'
	

class Directory(BaseModel):
	name: str = Field('')
	read: List[str] = Field([])
	contents: List[Union['Directory', File]] = Field([])

	def to_neuralsys_format(self, username: str) -> str:
		return '{"directory_name": "' + self.name + '", "contents": [' + ','.join([x.to_neuralsys_format(username=username) for x in self.contents if username in self.read]) + "]}"


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
	
	@property
	def to_neuralsys_format(self) -> str:
		return self.base_dir.to_neuralsys_format(self.current_user)
