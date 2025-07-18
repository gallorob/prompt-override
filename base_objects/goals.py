from typing import Dict, List

from base_objects.vfs import VirtualFileSystem

from pydantic import BaseModel, Field


class Trigger(BaseModel):
    function_name: str = Field("")
    parameters: Dict[str, str] = Field({})

    def evaluate(self, vfs: VirtualFileSystem):
        f = getattr(vfs, self.function_name)
        return f(**self.parameters)


class Goal(BaseModel):
    name: str = Field("")
    description: str = Field("")
    outcome: str = Field("")
    triggers: List[Trigger] = Field([])
    hints: str = Field("")

    _solved: bool = False

    def resolved(self, vfs: VirtualFileSystem):
        res = True
        for trigger in self.triggers:
            res &= trigger.evaluate(vfs=vfs)
        self._solved = res
        return res
