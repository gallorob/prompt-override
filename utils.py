import json
import logging
from hashlib import sha224
from typing import Any, Dict, Optional

from requests import get, post, Response
from settings import settings


def check_server_connection() -> bool:
    server_url = settings.server_url
    try:
        response = get(f"{server_url}/ollama_list_models")
        if response.status_code == 200:
            logging.getLogger("prompt_override").debug(
                f"Server response: {response.status_code} - {response.text}"
            )
            return True
        return False
    except ConnectionError:
        return False


def send_to_server(data: Optional[Dict[str, Any]], endpoint) -> Response:
    server_url = settings.server_url
    username = settings.user_name
    if data:
        uid = sha224(username.encode("utf-8")).hexdigest()
        payload = {"uid": uid, **data}
        response = post(f"{server_url}/{endpoint}", json=payload)
    else:
        response = get(f"{server_url}/{endpoint}")
    if response.status_code != 200:
        logging.getLogger("prompt_override").error(
            f"Server error: {response.status_code} - {response.text}"
        )
        raise ConnectionError(json.loads(response.text)["message"])
    return response.json()
