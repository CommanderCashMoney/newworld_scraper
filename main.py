import traceback
import json
import requests
import cv2

from app.nwmp_api_old import api_insert, prep_for_api_insert
from app.ocr.utils import look_for_cancel_or_refresh, look_for_tp, next_page
from app.utils.keyboard import press_key
from app.utils.mouse import click, mouse
from app.ocr.utils import grab_screen
import time
import pytesseract
import pynput
import sys
from win32gui import GetWindowText, GetForegroundWindow
import numpy as np
from my_timer import Timer
from datetime import datetime, timedelta
from app.overlay import overlay  # noqa
import ocr_image
import difflib

from settings import SETTINGS
from app.utils import format_seconds, resource_path
from app.nwmp_api import check_latest_version
from app.self_updating import INSTALLER_LAUNCHED_EVENT, VERSION_FETCHED_EVENT, version_update_events


def show_exception_and_exit(exc_type, exc_value, tb):
    traceback.print_exception(exc_type, exc_value, tb)
    sys.exit(-1)


sys.excepthook = show_exception_and_exit
pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')

# globals
page_stuck_counter = 0
SCANNING = False
canceled = False
test_run = False
img_count = 1
my_token = ''
user_name = ''
access_groups = []
server_access_ids = []
app_timer = Timer('app')
round_timer = Timer('round')
loading_timer = Timer('load')
current_page = 1
prices_data_resend = ()


# todo: move to keyboard module
def on_press(key):
    global SCANNING, canceled

    if GetWindowText(GetForegroundWindow()) == 'Trade Price Scraper' or GetWindowText(GetForegroundWindow()) == "New World":
        # if key == pynput.keyboard.Key.enter:
        #     print('hit enter')

        if key == pynput.keyboard.KeyCode(char='/'):
            SCANNING = False
            canceled = True
            print('Exited from Key Press')
            ocr_image.ocr.stop_OCR()


listener = pynput.keyboard.Listener(on_press=on_press)
listener.start()


def add_single_item(clean_list, env, func):
    global user_name, access_groups
    # add timestamp
    now = datetime.now()
    dt_string = now.strftime('%Y-%m-%dT%X')
    clean_list.append(dt_string)
    json_data = ''
    if func == 'name_cleanup_insert':
        json_data = '{"bad_word":' + json.dumps(clean_list[0]) + ', "good_word":' + json.dumps(clean_list[1]) + ', "timestamp": "' + clean_list[2] + '", '

    elif func == 'confirmed_names_insert':

        json_data = '{"name":' + json.dumps(clean_list[0]) + ', "timestamp": "' + clean_list[2] + '", '

    if 'scanner_user' in access_groups:
        json_data = json_data + '"approved": "True", '
    else:
        json_data = json_data + '"approved": "False", '
    json_data = json_data + f'"username": "{user_name}"' + '}'

    api_insert(json_data, env, 1, 0, func)


def populate_confirm_form():
    cn = ocr_image.ocr.get_confirmed_names()
    cn_list = list(cn.keys())
    confirm_list = ocr_image.ocr.get_confirms()
    for count, value in enumerate(confirm_list):
        if count >= 10:
            break
        overlay.updatetext(f'bad_name_{count}', value, size=len(value))
        close_matches = difflib.get_close_matches(value, cn_list, n=5, cutoff=0.6)
        close_matches.insert(0, 'Add New')
        s = max(close_matches, key=len)
        overlay.add_names(f'good_name_{count}', close_matches, size=s)

        overlay.enable('add{}'.format(count))


def next_confirm_page():
    global current_page
    current_page += 1
    for x in range(10):
        overlay.updatetext(f'bad_name_{x}', '', size=10)
        overlay.updatetext(f'good_name_{x}', '', size=10)

    if len(ocr_image.ocr.get_confirms()) >= 10:
        ocr_image.ocr.del_confirms()
    populate_confirm_form()


def clear_overlay(overlay):
    field_list = ['elapsed', 'key_count', 'ocr_count', 'accuracy', 'listings_count', 'p_fails', 'rejects', 'log_output', 'error_output']
    for x in field_list:
        overlay.updatetext(x, '')


def login(overlay, env, un, pw):
    if env == 'dev':
        url = 'http://localhost:8080/api/token/'
    else:
        url = 'https://nwmarketprices.com/api/token/'
    print('Logging in')
    overlay.disable('login')
    overlay.updatetext('login_status', 'logging in..')
    overlay.read()
    json_data = {"username": un, "password": pw, "version": SETTINGS.VERSION}
    json_data = json.dumps(json_data)
    try:
        r = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    except requests.exceptions.ConnectionError:
        r = None

    status_code = r.status_code if r is not None else None
    if status_code == 200:
        print('login successful')
        return r
    elif r is None:
        print("Login failed - no connection to server")
    else:
        print('login failed!')
        print(r.status_code)
        print(r.json())
    return None


def main():
    LOGIN_COMPLETED_EVENT = "-LOGIN CALLBACK-"  # noqa

    global user_name, SCANNING, test_run, canceled, img_count, access_groups, server_access_ids, prices_data_resend, my_token
    app_timer.start()
    round_timer.start()
    loading_timer.start()
    overlay.window.perform_long_operation(check_latest_version, VERSION_FETCHED_EVENT)

    while True:
        if 'advanced' in access_groups:
            overlay.show_advanced()
        event, values = overlay.read()
        version_update_events(event, values)
        if event is None or event == INSTALLER_LAUNCHED_EVENT:  # quit
            break
        overlay.update_spinner()

        if values.get('test_t'):
            test_run = True
            ocr_image.ocr.test_run(True)
        else:
            test_run = False
            ocr_image.ocr.test_run(False)

        auto_scan_sections = bool(values.get('sections_auto'))
        env = 'dev' if values.get('dev') else 'prod'
        ocr_image.ocr.set_env(env)

        server_id = values.get('server_select', '')

        try:
            pages = int(values['pages'])
        except ValueError:
            pages = 1

        if event == 'Run' and server_id != '':
            SCANNING = True
            if pages == 0 and not auto_scan_sections:
                pages = ocr_image.ocr.get_page_count()
            overlay.disable('Run')
        if event == 'Clear':
            ocr_image.ocr.clear()
            for x in range(10):
                overlay.updatetext(f'good_name_{x}', '')
                overlay.updatetext(f'bad_name_{x}', '')

                overlay.disable('add{}'.format(x))
        if event[:3] == 'add':
            # manually add from the confirm form
            row_num = event[3:]
            name_list = []
            name_list.append(values[f'bad_name_{row_num}'])
            name_list.append(values[f'good_name_{row_num}'])
            overlay.disable(event)
            if values[f'good_name_{row_num}'] == 'Add New':
                print(f'adding to confirmed names: {name_list}')
                add_single_item(name_list, env, 'confirmed_names_insert')
                overlay.updatetext('log_output', f'adding to confirmed names: {name_list}', append=True)
            else:
                print(f'adding to name cleanup dict: {name_list}')
                add_single_item(name_list, env, 'name_cleanup_insert')
                overlay.updatetext('log_output', f'adding to name cleanup: {name_list}', append=True)

        if event == 'next_btn':
            next_confirm_page()

        if event == 'login':
            un = values['un']
            pw = values['pw']
            if values['prod']:
                login_env = 'prod'
            else:
                login_env = 'dev'
            overlay.set_spinner_visibility(True)
            # use long operation to avoid hang
            overlay.window.perform_long_operation(lambda: login(overlay, login_env, un, pw), LOGIN_COMPLETED_EVENT)
        elif event == LOGIN_COMPLETED_EVENT:
            overlay.set_spinner_visibility(False)
            response = values[LOGIN_COMPLETED_EVENT]
            if response is None:
                overlay.enable('login')
                overlay.updatetext('login_status', 'login failed')
                overlay.read()
            else:
                json_response = response.json()
                my_token = json_response['access']
                overlay.updatetext('login_status', '')
                user_name = json_response['username']
                access_groups = json_response['groups']
                for x in access_groups:
                    if 'server-' in x:
                        server_access_ids.append(x[7:])
                overlay.updatetext('server_select', server_access_ids)
                overlay.show_main()

        if event == 'resend':
            overlay.disable('resend')
            overlay.read()
            prices_data_resend = api_insert(*prices_data_resend)

        if event == '-FOLDER-':
            folder = values['-FOLDER-']
            insert_list = ocr_image.ocr.get_insert_list()
            if insert_list:
                with open(f'{folder}/prices_data.txt', 'w') as f:
                    f.write(json.dumps(insert_list))
                overlay.updatetext('log_output', f'Data saved to: {folder}/prices_data.txt', append=True)
            else:
                overlay.updatetext('error_output', 'No data to export to file.', append=True)

        # if SCANNING:


        # ocr_state = ocr_image.ocr.get_state()
        # if ocr_state == 'running':
        #     overlay.updatetext('elapsed', format_seconds(app_timer.elapsed()))
        #     overlay.updatetext('status_bar', 'Waiting for text extraction to finish')
        #     # overlay.updatetext('log_output', 'Waiting for text extraction to finish', append=True)
        #     overlay.updatetext('ocr_count', ocr_image.ocr.get_img_queue_len())
        #     get_updates_from_ocr()
        #     overlay.read()
        #
        #     if ocr_image.ocr.get_img_queue_len() == 0:
        #         ocr_image.ocr.stop_OCR()
        #         overlay.updatetext('status_bar', 'Finished extracting text')
        #         overlay.updatetext('log_output', 'Finished extracting text', append=True)
        #         overlay.updatetext('log_output', f'Total time taken: {format_seconds(app_timer.elapsed())}', append=True)
        #         time.sleep(1)
        #         get_updates_from_ocr()
        #         overlay.read()
        #         time.sleep(1)
        #         print('Finished: ',str(timedelta(seconds=app_timer.elapsed())))
        #         print('Reject List: ', ocr_image.ocr.get_rejects())
        #         print('Confirm list: ', ocr_image.ocr.get_confirms())
        #
        #         populate_confirm_form()
        #         if ocr_image.ocr.get_insert_list():
        #             if not canceled:
        #                 overlay.updatetext('status_bar', 'Cleaning data and submitting to API')
        #                 overlay.updatetext('log_output', 'Cleaning data and submitting to API', append=True)
        #                 overlay.read()
        #                 prep_for_api_insert(my_token, ocr_image.ocr.get_insert_list(), server_id, env)
        #             else:
        #                 print('Scan Canceled. No data inserted.')
        #                 overlay.updatetext('status_bar', 'ERROR')
        #                 overlay.updatetext('error_output', 'Scan Canceled. No data inserted.', append=True)
        #                 canceled = False
        #
        #         img_count = 1
        #         overlay.enable('Run')
        #         if 'confirm_names' in access_groups and ocr_image.ocr.get_confirms():
        #             overlay.show_confirm()


if __name__ == "__main__":
    main()
