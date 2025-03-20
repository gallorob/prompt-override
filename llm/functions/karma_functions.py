from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParamSpec
import json

from base_objects.vfs import VirtualFileSystem

class KarmaFunctions(GPTFunctionLibrary):
	def try_call_func(self,
					  func_name: str,
					  func_args: str,
					  vfs: VirtualFileSystem) -> str:
		if isinstance(func_args, str):
			func_args = json.loads(func_args)
		try:
			operation_result = self.call_by_dict({
				'name': func_name,
				'arguments': {
					'vfs': vfs,
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