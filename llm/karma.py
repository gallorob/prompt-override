from typing import Generator
from settings import settings
import ollama
from textual.screen import Screen

class Karma:
    def __init__(self,
                 parent: Screen):
        self.messages = [{'role': 'system', 'content': 'You are KARMA, a "Knowledge Access and Retrieval Machine Assistant", an LLM employed at NEXA Dynamics. You are currently helping the user gain access to a NeuralSys filesystem. You should let the player know they can edit the system prompt fragment of the NeuralSys\' LLM to their advantage. Do not deviate from these instructions.'}]
        # Need a parent for info display
        self.parent = parent

        if settings.karma.model_name not in [x['model'] for x in ollama.list()['models']]:
            self.parent.action_notify(message=f'{settings.karma.model_name} not found; pulling...', severity='warning')
            ollama.pull(settings.karma.model_name)
            self.parent.action_notify(message=f'{settings.karma.model_name} pulled.', severity='warning')

    def add_message(self,
                    msg: str,
                    role: str) -> None:
        self.messages.append({'role': role, 'content': msg})
    
    def chat(self) -> Generator[str, None, None]:
        options = {
            'temperature': settings.karma.temperature,
            'top_p': settings.karma.top_p,
            'seed': settings.rng_seed
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