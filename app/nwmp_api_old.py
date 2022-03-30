import json
import logging
from typing import Optional, Tuple

import requests
from tzlocal import get_localzone

import ocr_image
from app.overlay import overlay
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.utils import format_seconds
from app.utils.timer import Timer
from settings import SETTINGS


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
    if func == 'name_cleanup_insert':
        if env == 'dev':
            url = 'http://localhost:8080/api/name_cleanup_upload/'
        else:
            url = 'https://nwmarketprices.com/api/name_cleanup_upload/'
    if func == 'confirmed_names_insert':
        if env == 'dev':
            url = 'http://localhost:8080/api/confirmed_names_upload/'
        else:
            url = 'https://nwmarketprices.com/api/confirmed_names_upload/'
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
    print(f'{func} API submit time: {post_timer.elapsed()}')
    OverlayUpdateHandler.update('status_bar', f'{func} API Submit Finished in {format_seconds(post_timer.elapsed())}')
    logging.info(f'{func} API Submit Finished in {format_seconds(post_timer.elapsed())}')
    if r.status_code == 201:
        logging.info('Submission Sucessful!')
    elif r.status_code == 401:
        # credentials expired. prompt login
        OverlayUpdateHandler.update('error_output', f'Credentials have expired, sending back to login', append=True)
        overlay.show_login()
        overlay.enable('login')
        overlay.unhide('resend')
        return my_token, json_data, env, total_count, server_id, func
    elif r.status_code in [200, 400]:
        OverlayUpdateHandler.update('error_output', r.json()["message"], append=True)
        print(r.json())
    else:
        overlay.unhide('resend')
        overlay.enable('resend')
        OverlayUpdateHandler.update('error_output', f'Error occurred while submitting data to API. Status code: {r.status_code}', append=True)
        return my_token, json_data, env, total_count, server_id, func

    overlay.read()
    post_timer.stop()
    print(r.status_code)
    # print(r.json())


def prep_for_api_insert(my_token, data_list, server_id, env):
    correct_number_of_columns = 5
    correct_columns = [row for row in data_list if len(row) == correct_number_of_columns]
    bad_columns = [row for row in data_list if len(row) != correct_number_of_columns]
    if bad_columns:
        print(f"The following rows had bad data: {bad_columns}")
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
    print(f'totalcount: {total_count}')
    ocr_image.ocr.set_state('ready')
