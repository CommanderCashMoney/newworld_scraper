import json
import logging
from typing import DefaultDict, Dict, List
from urllib.parse import urljoin

import requests
from tzlocal import get_localzone

from app.events import VERSION_FETCHED_EVENT
from app.overlay import overlay
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


def submit_price_data(price_data) -> bool:
    url = urljoin(SETTINGS.base_web_url, "/api/scanner_upload/")
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


def submit_bad_names(bad_names: DefaultDict[str, int]) -> None:
    url = urljoin(SETTINGS.base_web_url, "/api/submit_bad_names/")

    try:
        r = requests.post(
            url,
            json=[{
                "bad_name": name,
                "number_times_seen": seen_no,
            } for name, seen_no in bad_names.items()],
            headers={'Authorization': f'Bearer {SELECTED_SETTINGS.access_token}'}
        )
        logging.info(r.json())
    except requests.exceptions.ConnectionError:
        r = None

    success = r is not None and r.status_code == 201
    if not success:
        logging.warning(f"Bad name submissions failed")


def perform_latest_version_check() -> str:
    overlay.window.perform_long_operation(check_latest_version, VERSION_FETCHED_EVENT)
