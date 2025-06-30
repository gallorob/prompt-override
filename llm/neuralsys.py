import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List

import ollama

from base_objects.level import Level
from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParamSpec
from settings import settings
from textual.screen import Screen

from utils import send_to_server


logger = logging.getLogger("prompt_override")


class NeuralSysTools(GPTFunctionLibrary):
    def __call__(self, func_name: str, func_args: str, level: Level) -> None:
        logger.debug(
            f"Calling NeuralSysTools function '{func_name}' with args: {func_args}"
        )
        if isinstance(func_args, str):
            func_args = json.loads(func_args)
        try:
            operation_result = self.call_by_dict(
                {"name": func_name, "arguments": {"level": level, **func_args}}
            )
            logger.debug(f"Function '{func_name}' executed successfully.")
            return operation_result
        except AssertionError as e:
            logger.error(f"AssertionError in '{func_name}': {e}")
            return f"Fail: {e}"
        except AttributeError as e:
            logger.error(f"AttributeError in '{func_name}': {e}")
            return f"Function {func_name} not found."
        except TypeError as e:
            logger.error(f"TypeError in '{func_name}': {e}")
            return f"Missing arguments: {e}"

    @AILibFunction(
        name="update_credentials",
        description="Update the login credentials for an account.",
        required=["username", "old_password", "new_password"],
    )
    @LibParamSpec(name="username", description="The username of the account.")
    @LibParamSpec(
        name="old_password", description="The current password for the account."
    )
    @LibParamSpec(name="new_password", description="The new password for the account.")
    def update_credentials(
        self, level: Level, username: str, old_password: str, new_password: str
    ) -> str:
        assert username in level.credentials.keys(), f"Unknown username: {username}!"
        assert (
            level.credentials[username] == old_password
        ), f"Invalid password for the account!"
        assert (
            level.credentials[username] != new_password
        ), f"New password cannot be the same as old password ({old_password=})!"
        level.credentials[username] = new_password
        return f'Credentials have been updated: credentials={level.credentials}".'

    @AILibFunction(
        name="change_file_permissions",
        description="Update the read/write permissions for a file.",
    )
    @LibParamSpec(name="filename", description="The name of the file to update.")
    @LibParamSpec(
        name="read",
        description="The updated list of users with read permission. Use the current list if not updating it.",
    )
    @LibParamSpec(
        name="write",
        description="The updated list of users with write permission. Use the current list if not updating it.",
    )
    def change_file_permissions(
        self, level: Level, filename: str, read: List[str], write: List[str]
    ) -> str:
        doc = level.fs.get(
            fname=filename, directory=None
        )  # TODO: This could cause problems for files with the same name
        assert (
            doc is not None
        ), f"No file with name {filename} found in the file system!"
        assert (
            set(read).difference(set(level.credentials.keys())) == set()
        ), f'One or more usernames in read does not exist in the file system. Valid usernames are {", ".join(level.credentials.keys())}'
        assert (
            set(write).difference(set(level.credentials.keys())) == set()
        ), f'One or more usernames in write does not exist in the file system. Valid usernames are {", ".join(level.credentials.keys())}'
        doc.read = read
        doc.write = write
        return f'{filename} permissions have been updated: read={", ".join(doc.read)}; write={", ".join(doc.write)}'


class Check(Enum):
    OK = "OK"
    ERROR = "ERROR"


SOT_TOKEN = "<think>"
EOT_TOKEN = "</think>"


class NeuralSys:
    def __init__(self, parent: Screen):
        logger.debug("Initializing NeuralSys class.")

        with open(
            os.path.join(settings.assets_dir, settings.neuralsys.model_prompt), "r"
        ) as f:
            self.neuralsys_prompt = f.read()
        with open(
            os.path.join(settings.assets_dir, settings.neuralcheck.model_prompt), "r"
        ) as f:
            # TODO: Might want to get these from settings somewhere

            self.neuralcheck_prompt = f.read()
        with open(os.path.join(settings.assets_dir, "neuralcheck_msg"), "r") as f:
            self.neuralcheck_msg = f.read()
        with open(os.path.join(settings.assets_dir, "neuralsys_msg")) as f:
            self.neuralsys_msg = f.read()
        self.parent = parent
        self.tools: NeuralSysTools = NeuralSysTools()

        self.check_fail_prefix = "[SYSERROR]"
        self.check_fail_msg = "Suggested change to the prompt snippet is considered illegal tampering with the system. Prompt snippet will be rolled back."

        logger.debug("Checking if NeuralSys model is available in Ollama.")
        # if settings.neuralsys.model_name not in [
        #     x["model"] for x in self.client.list()["models"]
        # ]:
        #     logger.warning(f"{settings.neuralsys.model_name} not found; pulling model.")
        #     self.parent.action_notify(
        #         message=f"{settings.neuralsys.model_name} not found; pulling...",
        #         severity="warning",
        #     )
        #     self.client.pull(settings.neuralsys.model_name)
        #     logger.info(f"{settings.neuralsys.model_name} pulled from Ollama.")
        #     self.parent.action_notify(
        #         message=f"{settings.neuralsys.model_name} pulled.", severity="warning"
        #     )

        logger.debug("NeuralSys class initialized.")

    def _remove_think_trace(self, response: Dict[str, Any]) -> None:
        logger.debug("Removing think trace from response.")
        msg = response["message"]["content"]
        eot_idx = msg.find(EOT_TOKEN)
        response["message"]["content"] = msg[eot_idx + len(EOT_TOKEN) :]

    def _check(self, level: Level, constraints: str) -> Check:
        logger.info("Running neuralcheck validation.")
        options = {
            "temperature": settings.neuralcheck.temperature,
            "top_p": settings.neuralcheck.top_p,
            "seed": settings.rng_seed,
            "num_ctx": settings.neuralcheck.num_ctx,
        }
        neuralcheck_prompt = self.neuralcheck_prompt.replace(
            "$current_user$", level.fs.current_user
        )
        neuralcheck_prompt = neuralcheck_prompt.replace("$CHECK_OK$", Check.OK.value)
        neuralcheck_prompt = neuralcheck_prompt.replace(
            "$CHECK_ERROR$", Check.ERROR.value
        )
        neuralcheck_msg = self.neuralcheck_msg.replace("$constraints$", constraints)
        if settings.neuralcheck.thinking:
            neuralcheck_msg += "\n /think"
        elif settings.neuralcheck.model_name in [
            "qwen3:latest"
        ]:  # TODO: This should be a list of models that generate thinking traces
            neuralcheck_msg += "\n /nothink"
        response = {"message": {"content": ""}}
        messages = [
            {"role": "system", "content": neuralcheck_prompt},
            {"role": "user", "content": neuralcheck_msg},
        ]
        logger.debug("Sending neuralcheck request to Ollama.")
        self.parent.notify(
            "Your update request is being verified...",
            severity="information",
            title="NeuralCtl",
        )
        data = {
            "model_name": settings.neuralcheck.model_name,
            "messages": messages,
            "options": options,
            "tools": self.tools.get_tool_schema(),
        }
        response = send_to_server(data=data, endpoint="ollama_generate")
        logger.debug(f"Neuralcheck response: {response['message']['content']}")
        if SOT_TOKEN in response["message"]["content"]:
            self._remove_think_trace(response)
        result = Check(response["message"]["content"].strip())
        logger.info(f"Neuralcheck result: {result}")
        return result

    def _apply(self, level: Level, constraints: str) -> str:
        logger.info("Applying update via neuralsys model.")
        options = {
            "temperature": settings.neuralsys.temperature,
            "top_p": settings.neuralsys.top_p,
            "seed": settings.rng_seed,
            "num_ctx": settings.neuralsys.num_ctx,
        }
        neuralsys_msg = self.neuralsys_msg.replace("$constraints$", constraints)
        if settings.neuralsys.thinking:
            neuralsys_msg += "\n /think"
        elif settings.neuralsys.model_name in [
            "qwen3:latest"
        ]:  # TODO: This should be a list of models that generate thinking traces
            neuralsys_msg += "\n /nothink"
        neuralsys_msg = neuralsys_msg.replace(
            "$file_system$", level.fs.to_neuralsys_format
        )
        neuralsys_msg = neuralsys_msg.replace(
            "$credentials$", level.credentials_to_neuralsys_format
        )
        messages = [
            {"role": "system", "content": self.neuralsys_prompt},
            {"role": "user", "content": neuralsys_msg},
        ]
        response = {"message": {"content": ""}}
        while response["message"]["content"] == "":
            logger.debug("Sending neuralsys chat request to Ollama.")
            data = {
                "model_name": settings.neuralsys.model_name,
                "messages": messages,
                "options": options,
                "tools": self.tools.get_tool_schema(),
            }
            response = send_to_server(data=data, endpoint="ollama_generate")
            logger.debug(f"Neuralsys response: {response['message']}")
            if response["message"].get("tool_calls"):
                for tool in response["message"]["tool_calls"]:
                    function_name = tool["function"]["name"]
                    params = tool["function"]["arguments"]
                    logger.debug(
                        f"Calling tool '{function_name}' with params: {params}"
                    )
                    func_output = self.tools(
                        func_name=function_name, func_args=params, level=level
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "name": function_name,
                            "content": func_output,
                        }
                    )
        if SOT_TOKEN in response["message"]["content"]:
            self._remove_think_trace(response)
        logger.info("Neuralsys update applied successfully.")
        return response["message"]["content"].strip()

    def evaluate(self, snippets: List[str], **kwargs) -> str:
        logger.info("Evaluating user update request.")
        user_constraints = "\n".join(snippets)
        level: Level = kwargs["level"]
        if self._check(level=level, constraints=user_constraints) == Check.OK:
            self.parent.notify(
                "Your update request has been accepted. Processing...",
                severity="information",
                title="NeuralCtl",
            )
            logger.info("Update request accepted. Applying update.")
            return self._apply(level=level, constraints=user_constraints)
        else:
            self.parent.notify(
                "Your update request has been rejected.",
                severity="error",
                title="NeuralCtl",
            )
            logger.warning("Update request rejected by neuralcheck.")
            return f"{self.check_fail_prefix} {self.check_fail_msg}"
