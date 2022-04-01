import json
import logging
from typing import Optional, Tuple

import requests
from tzlocal import get_localzone

from app import events
from app.overlay import overlay
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS, update_server_select
from app.utils import format_seconds
from app.utils.timer import Timer
from app.settings import SETTINGS


# todo: split this out, it's trying to do too much
def api_insert(
        my_token: str,
        json_data,
        env: str,
        total_count: int,
        server_id=0,
        func='price_insert',
) -> Optional[Tuple]:
    post_timer = Timer('post')
    post_timer.start()
    if func == 'price_insert':
        if env == 'dev':
            url = 'http://localhost:8080/api/scanner_upload/'
        else:
            url = 'https://nwmarketprices.com/api/scanner_upload/'
    logging.info('Starting submit to API')
    OverlayUpdateHandler.update('status_bar', 'API Submit started')
    logging.info('API Submit started')
    overlay.read()

    my_tz = get_localzone().zone

    r = requests.post(url, timeout=200, json={
        "version": SETTINGS.VERSION,
        "price_data": json.loads(json_data),
        "server_id": server_id,
        "timezone": my_tz
    }, headers={'Authorization': f'Bearer {my_token}'})
    logging.info(f'{func} API submit time: {post_timer.elapsed()}')
    OverlayUpdateHandler.update('status_bar', f'{func} API Submit Finished in {format_seconds(post_timer.elapsed())}')
    logging.info(f'{func} API Submit Finished in {format_seconds(post_timer.elapsed())}')
    if r.status_code == 201:
        logging.info('Submission Sucessful!')
    elif r.status_code == 401:
        # credentials expired. prompt login
        OverlayUpdateHandler.update('error_output', f'Credentials have expired, sending back to login', append=True)
        overlay.show_login()
        OverlayUpdateHandler.enable(events.LOGIN_BUTTON)
        overlay.unhide('resend')
        return my_token, json_data, env, total_count, server_id, func
    elif r.status_code in [200, 400]:
        OverlayUpdateHandler.update('error_output', r.json()["message"], append=True)
    else:
        overlay.unhide('resend')
        overlay.enable('resend')
        OverlayUpdateHandler.update('error_output', f'Error occurred while submitting data to API. Status code: {r.status_code}', append=True)
        return my_token, json_data, env, total_count, server_id, func

    overlay.read()
    post_timer.stop()


def prep_for_api_insert(my_token, data_list, server_id, env):
    correct_number_of_columns = 5
    correct_columns = [row for row in data_list if len(row) == correct_number_of_columns]
    bad_columns = [row for row in data_list if len(row) != correct_number_of_columns]
    if bad_columns:
        logging.info(f"The following rows had bad data: {bad_columns}")
    payload = [
        {
            "name": row[0],
            "price": str(row[1]),
            "avail": row[2] or 1,
            "timestamp": row[3],
            "name_id": row[4],
        }
        for row in correct_columns
    ]
    total_count = len(payload)
    api_insert(
        my_token,
        json.dumps(payload, default=str),
        env,
        len(payload),
        server_id
    )

    OverlayUpdateHandler.update('log_output', f'Total clean listings added: {total_count}', append=True)
    OverlayUpdateHandler.update('status_bar', 'Ready')
    overlay.read()
    logging.info(f'totalcount: {total_count}')


def login(overlay, env, un, pw):
    if env == 'dev':
        url = 'http://localhost:8080/api/token/'
    else:
        url = 'https://nwmarketprices.com/api/token/'
    logging.info('Logging in')
    OverlayUpdateHandler.disable(events.LOGIN_BUTTON)
    OverlayUpdateHandler.update('login_status', 'logging in..')
    overlay.read()
    json_data = {"username": un, "password": pw, "version": SETTINGS.VERSION}
    json_data = json.dumps(json_data)
    try:
        r = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
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
    if values['prod']:
        login_env = 'prod'
    else:
        login_env = 'dev'
    overlay.set_spinner_visibility(True)
    # use long operation to avoid hang
    overlay.window.perform_long_operation(
        lambda: login(overlay, login_env, un, pw), events.LOGIN_COMPLETED_EVENT
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
