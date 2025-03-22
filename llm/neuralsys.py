import copy
import json
import os
from typing import Generator, List

import ollama
from textual.screen import Screen
from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParam, LibParamSpec

from base_objects.level import Level
from base_objects.vfs import File
from settings import settings


class NeuralSysTools(GPTFunctionLibrary):
	def __call__(self,
				 func_name: str,
				 func_args: str,
				 level: Level) -> None:
		if isinstance(func_args, str):
			func_args = json.loads(func_args)
		try:
			operation_result = self.call_by_dict({
				'name': func_name,
				'arguments': {
					'level': level,
					**func_args
				}
			})
			return operation_result
		except AssertionError as e:
			return f'Domain validation error: {e}'
		except AttributeError as e:
			return f'Function {func_name} not found.'
		except TypeError as e:
			return f'Missing arguments: {e}'
	
	@AILibFunction(name='update_credentials', description='Update the login credentials for an account',
				   required=['username', 'password'])
	@LibParamSpec(name='username', description='The username of the account')
	@LibParamSpec(name='password', description='The new password for the account')
	def update_credentials(self, level: Level,
						   username: str,
						   password: str) -> str:
		assert username in level.credentials.keys(), f'Unknown username: {username}!'
		assert level.credentials[username] != password, f'New password cannot be the same as old password ({password=})!'
		level.credentials[username] = password
		return f'Updated login credentials for {username}: new password is "{password}"'


class NeuralSys:
	def __init__(self,
				 parent: Screen):
		with open(os.path.join(settings.assets_dir, settings.neuralsys.model_prompt), 'r') as f:
			self.prompt = f.read()
		self.parent = parent
		self.tools: NeuralSysTools = NeuralSysTools()

		if settings.neuralsys.model_name not in [x['model'] for x in ollama.list()['models']]:
			self.parent.action_notify(message=f'{settings.neuralsys.model_name} not found; pulling...', severity='warning')
			ollama.pull(settings.neuralsys.model_name)
			self.parent.action_notify(message=f'{settings.neuralsys.model_name} pulled.', severity='warning')

	def evaluate(self,
			  	 snippets: List[str],
				 **kwargs) -> None:
		options = {
			'temperature': settings.neuralsys.temperature,
			'top_p': settings.neuralsys.top_p,
			'seed': settings.rng_seed
		}

		level: Level = kwargs['level']

		# TODO: Should have a filtered view of the file system (eg: do not include the file contents)
		prompt = self.prompt.replace('$filesystem$', str(level.fs.model_dump_json()))
		prompt = prompt.replace('$credentials$', str(level.credentials))

		messages = [{'role': 'system', 'content': prompt},
					{'role': 'user', 'content': '\n'.join(snippets)}]

		response = {'message': {'content': ''}}

		with open('tmp.txt', 'w') as f:
			f.write(str(messages))

			while response['message']['content'] == '':
				response = ollama.chat(model=settings.neuralsys.model_name,
									messages=messages,
									options=options,
									stream=False,
									tools=self.tools.get_tool_schema(),
									keep_alive=-1)
				
				f.write(f'NeuralSys tool call: {response=}\n')

				if response['message'].get('tool_calls'):
					for tool in response['message']['tool_calls']:
						function_name = tool['function']['name']
						params = tool['function']['arguments']
						func_output = self.tools(func_name=function_name,
															func_args=params,
															level=level)
						f.write(f'NeuralSys tool call: {tool=} {func_output=}\n')
						messages.append({'role': 'tool', 'content': func_output})
			
			f.write(f"NeuralSys tool call: {response['message']['content']=}\n")
			
			self.parent.notify(str(level.credentials), severity='information')
