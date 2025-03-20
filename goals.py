from typing import Dict, List
from pydantic import BaseModel, Field

from vfs import VirtualFileSystem


class Trigger(BaseModel):
    function_name: str = Field('')
    parameters: Dict[str, str] = Field({})

    def evaluate(self, vfs: VirtualFileSystem):
        f = getattr(vfs, self.function_name)
        return f(**self.parameters)


class Goal(BaseModel):
    name: str = Field('')
    description: str = Field('')
    triggers: List[Trigger] = Field([])

    def resolved(self, vfs: VirtualFileSystem):
        res = True
        for trigger in self.triggers:
            res &= trigger.evaluate(vfs=vfs)
        return res