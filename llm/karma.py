import os
from typing import Generator, List

import ollama
from textual.screen import Screen

from base_objects.level import Level
from settings import settings


class Karma:
    def __init__(self,
                 parent: Screen,
                 snippets: List[str]):
        with open(os.path.join(settings.assets_dir, settings.karma.model_prompt), 'r') as f:
            self.prompt = f.read()
        self.prompt = self.prompt.replace('$snippets$', '\n\n'.join(snippets))
        self.messages = [{'role': 'system', 'content': self.prompt}]
        self.parent = parent

        if settings.karma.model_name not in [x['model'] for x in ollama.list()['models']]:
            self.parent.action_notify(message=f'{settings.karma.model_name} not found; pulling...', severity='warning')
            ollama.pull(settings.karma.model_name)
            self.parent.action_notify(message=f'{settings.karma.model_name} pulled.', severity='warning')

    def add_message(self,
                    msg: str,
                    role: str) -> None:
        self.messages.append({'role': role, 'content': msg})
    
    def include_fs(self,
                   level: Level) -> None:
        with open(os.path.join(settings.assets_dir, 'karma_fs_prompt'), 'r') as f:
            msg = f.read()
        msg = msg.replace('$current_user$', level.fs.current_user)
        msg = msg.replace('$filesystem$', level.fs.to_karma_format)
        self.messages.append({'role': 'system', 'content': msg})

    def chat(self,
             **kwargs) -> Generator[str, None, None]:
        options = {
            'temperature': settings.karma.temperature,
            'top_p': settings.karma.top_p,
            'seed': settings.rng_seed,
            'num_ctx': settings.neuralsys.num_ctx,
        }
        response = ollama.chat(model=settings.karma.model_name,
                               messages=self.messages,
                               options=options,
                               stream=True,
                               keep_alive=-1)
        msg = ''
        for chunk in response:
            token = chunk['message']['content']
            msg += token
            yield token
        
        self.add_message(msg=msg, role='assistant')