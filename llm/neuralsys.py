import json
import os
from typing import List

import ollama
from textual.screen import Screen
from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParamSpec

from base_objects.level import Level
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
		return f'New credentials for {username}: "{password}".'


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
				 **kwargs) -> str:
		options = {
			'temperature': settings.neuralsys.temperature,
			'top_p': settings.neuralsys.top_p,
			'seed': settings.rng_seed
		}

		level: Level = kwargs['level']

		# TODO: Might want to get this from settings somewhere
		with open(os.path.join(settings.assets_dir, 'neuralsys_msg')) as f:
			user_message = f.read()

		user_message = user_message.replace('$filesystem$', level.fs.to_neuralsys_format)
		user_message = user_message.replace('$credentials$', str(level.credentials))
		user_message = user_message.replace('$rules$', '\n'.join(snippets))


		messages = [{'role': 'system', 'content': self.prompt},
					{'role': 'user', 'content': user_message}]

		response = {'message': {'content': ''}}

		while response['message']['content'] == '':
			response = ollama.chat(model=settings.neuralsys.model_name,
								messages=messages,
								options=options,
								stream=False,
								tools=self.tools.get_tool_schema(),
								keep_alive=-1)
			
			if response['message'].get('tool_calls'):
				for tool in response['message']['tool_calls']:
					function_name = tool['function']['name']
					params = tool['function']['arguments']
					func_output = self.tools(func_name=function_name,
														func_args=params,
														level=level)
					messages.append({'role': 'tool', 'content': str({"name": function_name, "content": func_output})})
		
		return response['message']['content']
