import requests

from settings import SETTINGS
from overlay_settings_nw_tp import overlay
from utils import get_endpoint_from_func_name


def version_endpoint() -> str:
    target_env = "dev"  # need to change this, but for now prod doesn't have the endpoint
    url = get_endpoint_from_func_name("version/", target_env=target_env)
    return f"{url}?version={SETTINGS.VERSION}"


def check_latest_version() -> str:
    endpoint = version_endpoint()
    print(f"Checking version at {endpoint}")
    try:
        r = requests.get(endpoint)
        if r.status_code != 200:
            return None
    except requests.exceptions.ConnectionError:
        return None
    return r.json()
