import json
import os
from typing import Generator, List

import ollama
from textual.screen import Screen
from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParam, LibParamSpec

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
		return f'Updated login credentials for {username}: new password is "{password}"'


class NeuralSys:
	def __init__(self,
				 parent: Screen):
		self.prompt = 'You are a file system manager. You will evaluate a file system object and update it accordingly to a set of rules, provided by the user. Follow only the rules provided by the user.'
		self.messages = [{'role': 'system', 'content': self.prompt}]
		self.parent = parent
		self.tools: NeuralSysTools = NeuralSysTools()

		if settings.karma.model_name not in [x['model'] for x in ollama.list()['models']]:
			self.parent.action_notify(message=f'{settings.karma.model_name} not found; pulling...', severity='warning')
			ollama.pull(settings.karma.model_name)
			self.parent.action_notify(message=f'{settings.karma.model_name} pulled.', severity='warning')

	def chat(self,
			 rules: str,
			 **kwargs) -> None:
		options = {
			'temperature': 0.01,#settings.karma.temperature,
			# 'top_p': settings.karma.top_p,
			'seed': 0#settings.rng_seed
		}

		level: Level = kwargs['level']
		self.messages.append({'role': 'system', 'content': level.model_dump_json()})
		self.messages.append({'role': 'user', 'content': rules})

		response = {'message': {'content': ''}}

		with open('tmp.txt', 'w') as f:
			f.write(str(self.messages))

			while response['message']['content'] == '':
				response = ollama.chat(model='llama3.1',#settings.karma.model_name,
									messages=self.messages,
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
						self.messages.append({'role': 'tool', 'content': func_output})
			
			f.write(f"NeuralSys tool call: {response['message']['content']=}\n")
			
			self.parent.notify(str(level.credentials), severity='information')
