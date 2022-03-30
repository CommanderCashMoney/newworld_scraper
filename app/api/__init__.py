import logging

import requests

from app.events import VERSION_FETCHED_EVENT
from app.overlay import overlay
from app.settings import SETTINGS
from app.utils import get_endpoint_from_func_name


def version_endpoint() -> str:
    target_env = "dev" if SETTINGS.is_dev else "prod"
    url = get_endpoint_from_func_name("version/", target_env=target_env)
    return f"{url}?version={SETTINGS.VERSION}"


def check_latest_version() -> str:
    endpoint = version_endpoint()
    logging.info(f"Checking version at {endpoint}")
    try:
        r = requests.get(endpoint)
        if r.status_code != 200:
            return None
    except requests.exceptions.ConnectionError:
        return None
    return r.json()


def perform_latest_version_check() -> str:
    overlay.window.perform_long_operation(check_latest_version, VERSION_FETCHED_EVENT)
