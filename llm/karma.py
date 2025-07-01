import logging
import os
from typing import Generator, List

import ollama

from base_objects.level import Level
from settings import settings
from textual.screen import Screen

from utils import send_to_server


logger = logging.getLogger("prompt_override")


class Karma:
    def __init__(self, parent: Screen, snippets: List[str]):
        logger.debug("Initializing Karma class.")

        prompt_path = os.path.join(settings.assets_dir, settings.karma.model_prompt)
        logger.debug(f"Loading karma model prompt from {prompt_path}")
        with open(prompt_path, "r") as f:
            self.prompt = f.read()
        self.prompt = self.prompt.replace("$snippets$", "\n\n".join(snippets))
        self.messages = [{"role": "system", "content": self.prompt}]
        self.parent = parent

        self._last_fs_info = None
        self._last_goals_hints = None

        logger.debug("Checking if model is available in Ollama.")

        if (
            settings.karma.model_name
            not in send_to_server(data=None, endpoint="ollama_list_models")["models"]
        ):
            logger.warning(
                f"{settings.karma.model_name} not found; pulling model. This may take a while."
            )
            self.parent.action_notify(
                message=f"{settings.karma.model_name} not found; pulling...",
                severity="warning",
                title="GameEngine",
            )
            send_to_server(
                data={"model_name": settings.karma.model_name},
                endpoint="ollama_init_model",
            )
            logger.info(f"{settings.karma.model_name} pulled from Ollama.")
            self.parent.action_notify(
                message=f"{settings.karma.model_name} pulled from Ollama.",
                severity="warning",
                title="GameEngine",
            )
        logger.debug("Karma class initialized.")

    def combine_messages(self, msgs: List[str]) -> str:
        logger.debug(f"Combining {len(msgs)} messages.")
        return "\n\n".join(msgs)

    def add_message(self, msg: str, role: str) -> None:
        logger.debug(f"Adding message with role '{role}'.")
        self.messages.append({"role": role, "content": msg})

    def include_fs(self, level: Level) -> None:
        logger.debug("Including filesystem info in messages.")
        fs_prompt_path = os.path.join(settings.assets_dir, "karma_fs_prompt")
        with open(fs_prompt_path, "r") as f:
            msg = f.read()
        msg = msg.replace("$current_user$", level.fs.current_user)
        msg = msg.replace("$filesystem$", level.fs.to_karma_format)
        if self._last_fs_info is not None:
            logger.debug("Removing previous filesystem info from messages.")
            self.messages.remove(self._last_fs_info)
        self.messages.append({"role": "system", "content": msg})
        self._last_fs_info = self.messages[-1]
        logger.debug("Filesystem info included.")

    def include_goal_hints(self, level: Level) -> None:
        logger.debug("Including goal hints in messages.")
        if self._last_goals_hints is not None:
            logger.debug("Removing previous goal hints from messages.")
            self.messages.remove(self._last_goals_hints)
        if level.next_possible_goal is not None:
            logger.debug("Next possible goal found, adding hints.")
            self.messages.append(
                {
                    "role": "system",
                    "content": f"Hints for the current goal:\n{level.next_possible_goal.hints}",
                }
            )
            self._last_goals_hints = self.messages[-1]
            logger.debug("Goal hints included.")
        else:
            logger.debug("No next possible goal found, skipping hints inclusion.")
            self._last_goals_hints = None

    def chat(self, **kwargs) -> str:
        logger.debug("Starting chat with Ollama model.")
        options = {
            "temperature": settings.karma.temperature,
            "top_p": settings.karma.top_p,
            "seed": settings.rng_seed,
            "num_ctx": settings.neuralsys.num_ctx,
        }
        logger.debug(f"Chat options: {options}")
        data = {
            "model_name": settings.karma.model_name,
            "messages": self.messages,
            "options": options,
        }
        msg = send_to_server(data=data, endpoint="ollama_generate")["message"][
            "content"
        ]
        logger.debug(f"Chat response: {msg}")
        logger.debug("Chat completed. Adding assistant message to history.")
        self.add_message(msg=msg, role="assistant")
        return msg
