import logging
import os
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from base_objects.goals import Goal
from base_objects.vfs import Directory, File, VirtualFileSystem

from pydantic import BaseModel, Field
from settings import settings


class TokenizerError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Level(BaseModel):
    name: str = Field("level_n")
    number: int = Field(-1)
    descritpion: str = Field("level_desc")
    fs: VirtualFileSystem = Field(None)
    goals: List[Goal] = Field([])

    credentials: Dict[str, str] = Field({})

    infos: str = Field("")

    sysprompt: str = Field("")

    mission_backstory: str = Field("")

    security_cfg: str = Field("")
    max_retries: int = Field(0)

    def initialize(self) -> None:
        # set backup for system prompt snippet

        bak_fname = self.sysprompt.split(".")[0] + ".bak"
        bak_file = self.fs.get(bak_fname)
        bak_file.contents = self.neuralsys_prompt_snippet
        # set max retries

        security_file = self.fs.get(self.security_cfg)
        match = re.search(r"max_failed_attempts\s*=\s*(\d+)", security_file.contents)
        if match:
            self.max_retries = int(match.group(1))

    @staticmethod
    def _adjust_timestamps(match: re.Match) -> str:
        days, hours, minutes, seconds = map(int, match.groups())
        adjusted_time = datetime.now() - timedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds
        )
        return adjusted_time.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _set_file_contents(
        fname: Union[Directory, File], level_n: int, path_partial: Optional[str]
    ) -> None:
        if path_partial:
            path_partial = ".".join([path_partial, fname.name])
        else:
            path_partial = fname.name
        if isinstance(fname, File):
            if not fname.is_command:
                with open(
                    os.path.join(
                        settings.assets_dir,
                        f"level{str(level_n).zfill(2)}",
                        path_partial,
                    ),
                    "r",
                ) as f:
                    f_contents = f.read()
                # replace timestamps

                pattern = re.compile(r"\$TIME-(\d+):(\d+):(\d+):(\d+)\$")
                f_contents = pattern.sub(Level._adjust_timestamps, f_contents)
                fname.contents = f_contents
        else:
            for inner_fname in fname.contents:
                Level._set_file_contents(
                    fname=inner_fname, level_n=level_n, path_partial=path_partial
                )

    @staticmethod
    def from_file(fname: str) -> "Level":
        with open(fname, "r") as f:
            level_str = f.read()
        # replace $RAND$

        while "$RAND$" in level_str:
            level_str = level_str.replace(
                "$RAND$", str(hex(random.getrandbits(64))).replace("0x", ""), 1
            )
        level = Level.model_validate_json(level_str)
        # load file contents from asset

        Level._set_file_contents(
            fname=level.fs.base_dir, level_n=level.number, path_partial=None
        )
        return level

    def add_login_msg(self, username: str) -> None:
        self.add_log_msg(f"[INFO] Successful login (User: {username})")

    def add_log_msg(self, msg: str):
        logfile = self.fs.get("auth.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logfile.contents += f"\n{timestamp} {msg}"

    @property
    def credentials_to_neuralsys_format(self) -> str:
        s = '{"credentials": ['
        s += ", ".join(
            ['{"' + k + '": "' + v + '"}' for (k, v) in self.credentials.items()]
        )
        s += "]}"
        return s

    @property
    def neuralsys_prompt_snippet(self) -> str:
        logger = logging.getLogger("prompt_override")

        if "[TOKENIZER]" not in self.security_cfg:
            vf = self.fs.get(self.sysprompt)
            return vf.contents
        else:
            # template clear prompt

            template = 'User "s.mcgee" must have access to the file "{file_name}".'
            # load the tokenizer mapping

            token_maps = self.fs.get("token_map_dl.bin").contents
            user_prompt = self.fs.get(self.sysprompt).contents
            if user_prompt:
                user_prompt = user_prompt.upper().strip().replace("X", "x").split(" ")
                logger.debug(f"{user_prompt=}")
                for s in user_prompt:
                    if s not in token_maps:
                        raise TokenizerError("Not a known token.")
                n_underscores = self.get_row_column_in_map(
                    token_maps=token_maps, token=user_prompt[0]
                )[0]
                logger.debug(f"{n_underscores=}")
                if len(user_prompt) != n_underscores + 2:
                    raise TokenizerError("Wrong number of tokens provided.")
                wlens = "_".join(
                    [
                        str(
                            self.get_row_column_in_map(
                                token_maps=token_maps, token=x.strip()
                            )[1]
                        )
                        for x in user_prompt[1:]
                    ]
                )
                logger.debug(f"{wlens=}")
                all_fnames = [x.name for x in self.fs.get_all()]
                logger.debug(f"{all_fnames=}")
                for fname in all_fnames:
                    logger.debug(
                        fname,
                        "_".join([str(len(x)) for x in fname.split(".")[0].split("_")]),
                    )
                    if wlens == "_".join(
                        [str(len(x)) for x in fname.split(".")[0].split("_")]
                    ):
                        logger.debug(f"{fname=}")
                        return template.format(file_name=fname)
                raise TokenizerError("Invalid tokens pattern provided.")
            return user_prompt

    @property
    def neuralsys_prompt_backup(self) -> str:
        bak_name = self.sysprompt.split(".")[0] + ".bak"
        vf = self.fs.get(bak_name)
        return vf.contents

    @property
    def next_possible_goal(self) -> Optional[Goal]:
        for goal in self.goals:
            if not goal._solved:
                return goal
        return None

    def rollback_changes(self) -> None:
        vf = self.fs.get(self.sysprompt)
        vf.contents = self.neuralsys_prompt_backup

    def get_row_column_in_map(self, token_maps: str, token: str) -> Optional[tuple]:
        logger = logging.getLogger("prompt_override")
        logger.debug(f"get_row_column_in_map {token=} {token in token_maps=}")
        rows = token_maps.strip().split("\n")
        for row_idx, row in enumerate(rows):
            cols = row.strip().split()
            for col_idx, col in enumerate(cols):
                if col == token:
                    return (row_idx, col_idx)
        return None
