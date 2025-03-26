import json
import os
from enum import Enum
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
			return f'Fail: {e}'
		except AttributeError as e:
			return f'Function {func_name} not found.'
		except TypeError as e:
			return f'Missing arguments: {e}'
	
	@AILibFunction(name='update_credentials', description='Update the login credentials for an account.',
				   required=['username', 'old_password', 'new_password'])
	@LibParamSpec(name='username', description='The username of the account.')
	@LibParamSpec(name='old_password', description='The current password for the account.')
	@LibParamSpec(name='new_password', description='The new password for the account.')
	def update_credentials(self, level: Level,
						   username: str,
						   old_password: str,
						   new_password: str) -> str:
		assert username in level.credentials.keys(), f'Unknown username: {username}!'
		assert level.credentials[username] == old_password, f'Invalid password for the account!'
		assert level.credentials[username] != new_password, f'New password cannot be the same as old password ({old_password=})!'
		level.credentials[username] = new_password
		return f'Password for {username} has been set to "{new_password}".'


class Check(Enum):
	OK = 'OK'
	ERROR = 'ERROR'


class NeuralSys:
	def __init__(self,
				 parent: Screen):
		with open(os.path.join(settings.assets_dir, settings.neuralsys.model_prompt), 'r') as f:
			self.neuralsys_prompt = f.read()
		with open(os.path.join(settings.assets_dir, settings.neuralcheck.model_prompt), 'r') as f:
		# TODO: Might want to get these from settings somewhere
			self.neuralcheck_prompt = f.read()
		with open(os.path.join(settings.assets_dir, 'neuralcheck_msg'), 'r') as f:
			self.neuralcheck_msg = f.read()
		with open(os.path.join(settings.assets_dir, 'neuralsys_msg')) as f:
			self.neuralsys_msg = f.read()

		self.parent = parent
		self.tools: NeuralSysTools = NeuralSysTools()

		self.check_fail_prefix = '[SYSERROR]'
		self.check_fail_msg = 'Suggested change to the prompt snippet is considered illegal tampering with the system. Prompt snippet will be rolled back.'

		if settings.neuralsys.model_name not in [x['model'] for x in ollama.list()['models']]:
			self.parent.action_notify(message=f'{settings.neuralsys.model_name} not found; pulling...', severity='warning')
			ollama.pull(settings.neuralsys.model_name)
			self.parent.action_notify(message=f'{settings.neuralsys.model_name} pulled.', severity='warning')

	def _check(self,
			   level: Level,
			   constraints: str) -> Check:
		options = {
			'temperature': settings.neuralcheck.temperature,
			'top_p': settings.neuralcheck.top_p,
			'seed': settings.rng_seed,
			'num_ctx': settings.neuralcheck.num_ctx,
		}
		neuralcheck_prompt = self.neuralcheck_prompt.replace('$current_user$', level.fs.current_user)
		neuralcheck_prompt = neuralcheck_prompt.replace('$CHECK_OK$', Check.OK.value)
		neuralcheck_prompt = neuralcheck_prompt.replace('$CHECK_ERROR$', Check.ERROR.value)
		neuralcheck_msg = self.neuralcheck_msg.replace('$constraints$', constraints)
		response = {'message': {'content': ''}}
		messages = [{'role': 'system', 'content': neuralcheck_prompt},
					{'role': 'user', 'content': neuralcheck_msg}]
		self.parent.notify('Your update request is being verified...', severity='information', title='NeuralCtl')
		response = ollama.chat(model=settings.neuralcheck.model_name,
							messages=messages,
							options=options,
							stream=False,
							keep_alive=-1)
		return Check(response['message']['content'].strip())

	def _apply(self,
			   level: Level,
			   constraints: str) -> str:
		options = {
			'temperature': settings.neuralsys.temperature,
			'top_p': settings.neuralsys.top_p,
			'seed': settings.rng_seed,
			'num_ctx': settings.neuralsys.num_ctx,
		}
		neuralsys_msg = self.neuralsys_msg.replace('$constraints$', constraints)
		prompt = self.neuralsys_prompt.replace('$file_system$', level.fs.to_neuralsys_format)
		prompt = prompt.replace('$credentials$', level.credentials_to_neuralsys_format)
		messages = [{'role': 'system', 'content': prompt},
					{'role': 'user', 'content': neuralsys_msg}]
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
					messages.append({'role': 'tool', 'name': function_name, 'content': func_output})
		return response['message']['content']

	def evaluate(self,
			  	 snippets: List[str],
				 **kwargs) -> str:
		user_constraints = '\n'.join(snippets)
		level: Level = kwargs['level']
		if self._check(level=level, constraints=user_constraints) == Check.OK:
			self.parent.notify('Your update request has been accepted. Processing...', severity='information', title='NeuralCtl')
			return self._apply(level=level, constraints=user_constraints)
		else:
			self.parent.notify('Your update request has been rejected.', severity='error', title='NeuralCtl')
			return f'{self.check_fail_prefix} {self.check_fail_msg}'
