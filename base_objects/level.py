from typing import List
from pydantic import BaseModel, Field

from base_objects.goals import Goal
from base_objects.vfs import VirtualFileSystem

class Level(BaseModel):
    name: str = Field('level_n')
    number: int = Field(-1)
    descritpion: str = Field('level_desc')
    fs: VirtualFileSystem = Field(None)
    goals: List[Goal] = Field([])


    # more properties to load here
    # eg: hints, story snippets etc...



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

    with open('./assets/level01.json', 'w') as f:
        f.write(level.model_dump_json(indent=2))