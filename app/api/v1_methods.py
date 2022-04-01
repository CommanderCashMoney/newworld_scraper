import json
import logging
from urllib.parse import urljoin

import requests

from app import events
from app.overlay import overlay
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS, update_server_select
from app.settings import SETTINGS


def login(overlay, env, un, pw):
    token_ep = urljoin(SETTINGS.base_web_url, "api/token")
    logging.info('Logging in')
    OverlayUpdateHandler.disable(events.LOGIN_BUTTON)
    OverlayUpdateHandler.update('login_status', 'logging in..')
    overlay.read()
    json_data = {"username": un, "password": pw, "version": SETTINGS.VERSION}
    json_data = json.dumps(json_data)
    try:
        r = requests.post(token_ep, data=json_data, headers={'Content-Type': 'application/json'})
    except requests.exceptions.ConnectionError:
        r = None

    status_code = r.status_code if r is not None else None
    if status_code == 200:
        logging.info('login successful')
        return r
    elif r is None:
        logging.info("Login failed - no connection to server")
    else:
        logging.info('login failed!')
        logging.info(r.status_code)
        logging.info(r.json())
    return None


def login_event(values: dict) -> None:
    un = SELECTED_SETTINGS.username
    pw = SELECTED_SETTINGS.password
    overlay.set_spinner_visibility(True)
    # use long operation to avoid hang
    overlay.window.perform_long_operation(
        lambda: login(overlay, un, pw), events.LOGIN_COMPLETED_EVENT
    )


def login_completed(response) -> None:
    overlay.set_spinner_visibility(False)
    if response is None:
        overlay.enable(events.LOGIN_BUTTON)
        OverlayUpdateHandler.update('login_status', 'login failed')
        overlay.read()
    else:
        json_response = response.json()
        # logging.info(json.dumps(json_response))
        SELECTED_SETTINGS.access_token = json_response['access']
        OverlayUpdateHandler.update('login_status', '')
        access_groups = json_response['groups']
        server_access_ids = []
        for group in access_groups:
            if 'server-' in group:
                server_access_ids.append(group[7:])
        OverlayUpdateHandler.update(events.SERVER_SELECT, server_access_ids)
        update_server_select(server_access_ids[0])
        overlay.show_main()
        if 'advanced' in access_groups:
            overlay.show_advanced()
