import datetime
import json
import logging
from typing import List
from urllib.parse import urljoin

import requests
from tzlocal.win32 import get_localzone

from app import events
from app.events import VERSION_FETCHED_EVENT
from app.overlay import overlay
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS
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




def submit_results(price_data: List) -> bool:
    if SETTINGS.is_dev:
        base_url = SETTINGS.nwmp_dev_api_host
    else:
        base_url = SETTINGS.nwmp_prod_api_host
    url = urljoin(base_url, "/api/scanner_upload/")
    my_tz = get_localzone().zone

    try:
        r = requests.post(url, timeout=200, data=json.dumps({
            "version": SETTINGS.VERSION,
            "price_data": price_data,
            "server_id": SELECTED_SETTINGS.server_id,
            "timezone": my_tz
        }, default=str), headers={
            'Authorization': f'Bearer {SELECTED_SETTINGS.access_token}',
            'Content-Type': "application/json"
        })
        logging.info(r.json())
    except requests.exceptions.ConnectionError:
        r = None

    success = r is not None and r.status_code == 201
    return success


def perform_latest_version_check() -> str:
    overlay.window.perform_long_operation(check_latest_version, VERSION_FETCHED_EVENT)
