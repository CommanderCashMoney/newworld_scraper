import requests

from settings import SETTINGS
from overlay_settings_nw_tp import overlay
from utils import get_endpoint_from_func_name


def check_latest_version() -> str:
    target_env = "dev"
    endpoint = get_endpoint_from_func_name("version/", target_env=target_env)
    try:
        r = requests.get(endpoint)
    except requests.exceptions.ConnectionError:
        return None
    return r.json()
