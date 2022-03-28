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
from app.nwmp_api import check_latest_version, version_endpoint
from app.self_updating import installer_file_path, install_new_version, perform_update_download


def show_exception_and_exit(exc_type, exc_value, tb):
    traceback.print_exception(exc_type, exc_value, tb)
    sys.exit(-1)


sys.excepthook = show_exception_and_exit
pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')

# globals
page_stuck_counter = 0
enabled = False
canceled = False
test_run = False
img_count = 1
my_token = ''
user_name = ''
access_groups = []
server_access_ids = []


# todo: move to keyboard module
def on_press(key):
    global enabled, canceled

    if GetWindowText(GetForegroundWindow()) == 'Trade Price Scraper' or GetWindowText(GetForegroundWindow()) == "New World":
        # if key == pynput.keyboard.Key.enter:
        #     print('hit enter')

        if key == pynput.keyboard.KeyCode(char='/'):
            enabled = False
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


def look_for_scroll(section):
    global page_stuck_counter
    look_for_cancel_or_refresh()
    # look for scrollbar
    if section == 'top':
        reference_aoi = (2438, 418, 34, 34)
        reference_image_file = resource_path('app/images/new_world/top_of_scroll.png')
    elif section == 'btm':
        reference_aoi = (2442, 1314, 27, 27)
        reference_image_file = resource_path('app/images/new_world/btm_of_scroll.png')
    elif section == 'last':
        reference_aoi = (2444, 1378, 25, 25)
        reference_image_file = resource_path('app/images/new_world/btm_of_scroll2.png')

    loading_timer.restart()
    while True:
        reference_grab = grab_screen(region=reference_aoi)
        reference_img = cv2.imread(reference_image_file)
        res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # print(f'scrollbar: {max_val}')
        # file_name = resource_path('images/scrollbar_cap.png')
        # cv2.imwrite(file_name, reference_grab)
        if max_val > 0.98:
            page_stuck_counter = 0
            return True
        else:
            print(f'loading_scroll {section}')
            overlay.updatetext('status_bar', 'Loading page')
            overlay.read()
            time.sleep(0.1)
            if loading_timer.elapsed() > 3:
                #we have been loading too long. Somthing is wrong. Skip it.
                page_stuck_counter += 1
                print('loading too long. skip it')
                overlay.updatetext(f'error_output', f'Took too long waiting for page to load - {page_stuck_counter}', append=True)
                overlay.read()
                return True


def check_loading(pages, section):
    if pages > 1:
        look_for_scroll(section)
    else:
        aoi = (842, 444, 200, 70)
        img = grab_screen(aoi)
        ref_grab = ocr_image.process_image(img)
        while np.count_nonzero(ref_grab) == 112500:
            aoi = (842, 444, 200, 70)
            img = grab_screen(aoi)
            ref_grab = ocr_image.process_image(img)
            print('loading on last page')
        time.sleep(0.3)


def get_img(pages, section):
    check_loading(pages, section)
    if section == 'last':
        aoi = (927, 1198, 1510, 200)
    else:
        aoi = (927, 430, 1510, 919)
    img = grab_screen(region=aoi)
    return img


def get_updates_from_ocr():
    ocr_updates = ocr_image.ocr.get_overlay_updates()
    for x in ocr_updates:

        overlay.updatetext(x[0], x[1], append=x[2])
        ocr_image.ocr.remove_one_overlayupdate()


def ocr_cycle(pages, app_timer):
    global enabled, img_count, canceled, page_stuck_counter

    for x in range(pages):
        if look_for_tp():
            if ocr_image.ocr.get_state() == 'stopped':
                overlay.updatetext('error_output', 'Text extraction stopped prematurely due to an error', append=True)
                overlay.updatetext('status_bar', 'ERROR')
                canceled = True
                overlay.read()
                return True
            overlay.updatetext('pages_left', pages-1)
            img = get_img(pages, 'top')
            ocr_image.ocr.add_img(img, img_count)
            overlay.updatetext('key_count', img_count)
            overlay.updatetext('ocr_count', ocr_image.ocr.get_img_queue_len())
            overlay.updatetext('status_bar', 'Capturing images')
            get_updates_from_ocr()
            overlay.read()
            # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
            # cv2.imwrite(file_name, img)
            img_count += 1

            if pages == 1:
                # see if scroll bar exists on last page
                reference_aoi = (2438, 418, 34, 34)
                reference_image_file = resource_path('app/images/new_world/top_of_scroll.png')
                reference_grab = grab_screen(region=reference_aoi)
                reference_img = cv2.imread(reference_image_file)
                res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val < 0.98:
                    break


            if not enabled:
                return True
            mouse.scroll(0, -11)

            img = get_img(pages, 'btm')
            ocr_image.ocr.add_img(img, img_count)
            overlay.updatetext('key_count', img_count)
            # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
            # cv2.imwrite(file_name, img)
            img_count += 1

            #scroll to last 2 items
            if pages == 1:
                #confirm we have a full scroll bar
                reference_aoi = (2442, 874, 27, 27)
                reference_image_file = resource_path('app/images/new_world/btm_of_scroll.png')
                reference_grab = grab_screen(region=reference_aoi)
                reference_img = cv2.imread(reference_image_file)
                res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val < 0.98:
                    break

            mouse.scroll(0, -2)
            img = get_img(pages, 'last')
            ocr_image.ocr.add_img(img, img_count)
            overlay.updatetext('key_count', img_count)
            # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
            # cv2.imwrite(file_name, img)
            img_count += 1

            if page_stuck_counter > 2:
                # got stuck looking for the scrollbars. exit out and skip section
                print('page stuck too long. moving to next section')
                overlay.updatetext('error_output', 'Page stuck too long. Moving to next section', append=True)
                page_stuck_counter = 0
                break

            next_page()
            pages -= 1
            overlay.updatetext('pages', pages)
            overlay.updatetext('elapsed', format_seconds(app_timer.elapsed()))
            overlay.read()

            if not enabled:
                return True
        else:
            print('couldnt find TP marker')
            overlay.updatetext('error_output', 'Couldnt find Trading Post window', append=True)
            overlay.updatetext('status_bar', 'ERROR')
            canceled = True
            overlay.read()
            enabled = False
            return True
    # need to clear the old price list since we are moving to a new section
    ocr_image.ocr.set_section_end(img_count)
    print('finished ocr cycle')


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


app_timer = Timer('app')
round_timer = Timer('round')
loading_timer = Timer('load')
current_page = 1
prices_data_resend = ()
version_fetched_event = "-VERSION FETCHED-"
download_new_version_event = "-DOWNLOAD NEW VERSION-"
installer_launched_event = "-INSTALLING-"
login_completed_event = "-LOGIN CALLBACK-"


def version_update_events(event, values) -> None:
    if event == version_fetched_event:
        response = values[version_fetched_event]
        if response is not None:
            overlay.version_check_complete(response)
            if not response["compatible_version"]:
                overlay.show_update_window()
            return
        # otherwise, we error out.
        hide = ["un_text", "un", "pw_text", "pw", "login"]
        for element in hide:
            overlay.window[element].update(visible=False)
        endpoint = version_endpoint()
        overlay.window["title"].update(
            f"Version check failed! :(\n\nNo connection to {endpoint}\n\nPlease let us know on discord."
        )
        overlay.set_spinner_visibility(False)
    elif event == "download_update":
        download_func = lambda: perform_update_download(overlay.download_link)  # noqa
        overlay.window.perform_long_operation(download_func, download_new_version_event)
        overlay.window["download_update"].update(text="Downloading...", disabled=True)
        overlay.set_spinner_visibility(True)
    elif event == download_new_version_event:
        if values[download_new_version_event] is not None:
            exc = values[download_new_version_event]
            overlay.window["download_update_text"].update(
                f"Couldn't download file.\n\n"
                f"Please check the installer is not already open.\n\n"
                f"Please close application once you check the error log."
            )
            formatted_exception = "".join(traceback.format_exception(None, exc, exc.__traceback__))
            print(formatted_exception)
            overlay.window["download_update"].update(visible=False)
            overlay.set_spinner_visibility(False)
            return
        install_func = lambda: install_new_version(installer_file_path())  # noqa
        overlay.window.perform_long_operation(install_func, installer_launched_event)


def main():
    run_start = None

    global user_name, enabled, test_run, canceled, img_count, access_groups, server_access_ids, prices_data_resend, my_token
    app_timer.start()
    round_timer.start()
    loading_timer.start()
    overlay.window.perform_long_operation(check_latest_version, version_fetched_event)

    while True:
        if 'advanced' in access_groups:
            overlay.show_advanced()
        event, values = overlay.read()
        version_update_events(event, values)
        if event is None or event == installer_launched_event:  # quit
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
            enabled = True
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
            overlay.window.perform_long_operation(lambda: login(overlay, login_env, un, pw), login_completed_event)
        elif event == login_completed_event:
            overlay.set_spinner_visibility(False)
            response = values[login_completed_event]
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
            # insert_list = '[asdfasdf, asdfasdfasdf,asdfasdfasdf,asdfasdfasdfasdf,asdfasdf]'
            if insert_list:
                with open(f'{folder}/prices_data.txt', 'w') as f:
                    f.write(json.dumps(insert_list))
                overlay.updatetext('log_output', f'Data saved to: {folder}/prices_data.txt', append=True)
            else:
                overlay.updatetext('error_output', 'No data to export to file.', append=True)

        if enabled:
            app_timer.restart()
            clear_overlay(overlay)
            overlay.hide_confirm()
            overlay.hide('resend')
            img_count = 1
            ocr_image.ocr.clean_insert_list()
            ocr_image.ocr.set_cap_state('running')
            ocr_image.ocr.start_OCR()

            if test_run:
                print('Starting TEST run')
                overlay.updatetext('log_output', 'Test scan started', append=True)
                overlay.updatetext('status_bar', 'Test scan started')
                overlay.read()
                img = get_img(pages, 'top')
                ocr_image.ocr.add_img(img, 1)

            else:
                print('Starting REAL run')
                overlay.updatetext('log_output', 'Real scan started', append=True)
                overlay.updatetext('status_bar', 'Real scan started')
                overlay.read()
                canceled = False
                if auto_scan_sections:
                    round_timer.restart()
                    now = datetime.now()
                    run_start = now.strftime("%m/%d/%Y %H:%M:%S")
                    section_list = {
                        'Raw Resources': (368, 488),
                        'Resources Reset 1': (170, 796),
                        'Refined Resources': (368, 568),
                        'Resources Reset 2': (170, 796),
                        'Cooking Ingredients': (368, 632),
                        'Resources Reset 3': (170, 796),
                        'Craft Mods': (368, 708),
                        'Resources Reset 4': (170, 796),
                        'Components': (368, 788),
                        'Resources Reset 5': (170, 796),
                        'Potion Reagents': (368, 855),
                        'Resources Reset 6': (170, 796),
                        'Dyes': (368, 936),
                        'Resources Reset 7': (170, 796),
                        'Azoth': (368, 990),
                        'Resources Reset 8': (170, 796),
                        'Arcana': (368, 1068),
                        'Consumables': (165, 900),
                        'Ammunition': (165, 985),
                        'House Furnishings': (165, 1091)
                    }
                    keypress_exit = False
                    # click resources twice because screen won't have focus
                    click('left', (170, 796))
                    time.sleep(0.2)
                    click('left', (170, 796))
                    time.sleep(1)
                    for key in section_list:
                        click('left', section_list[key])
                        time.sleep(1)
                        mouse.position = (1300, 480)
                        if section_list[key] != (170, 796):
                            print(f'Starting new section: {key}')
                            keypress_exit = ocr_cycle(ocr_image.ocr.get_page_count(), app_timer)
                            if keypress_exit:
                                overlay.updatetext('error_output', 'Exit key press', append=True)
                                overlay.updatetext('error_output', 'Scan Canceled. No data inserted.', append=True)
                                overlay.updatetext('status_bar', 'Scan cancelled')
                                overlay.enable('Run')
                                break
                            time.sleep(0.5)

                            # check time to see if moving is required to stop idle check
                            if round_timer.elapsed() > 600:
                                print('Mid cycle pause: ', str(timedelta(seconds=app_timer.elapsed())))
                                press_key(pynput.keyboard.Key.esc)
                                time.sleep(0.5)
                                rand_time = np.random.uniform(0.10, 0.15)
                                press_key('w', rand_time)
                                press_key('s', rand_time)
                                press_key('e')
                                time.sleep(1)
                                round_timer.restart()
                else:
                    ocr_cycle(pages, app_timer)

            enabled = False
            ocr_image.ocr.set_cap_state('stopped')
            overlay.updatetext('log_output', 'Image capture finished', append=True)

        ocr_state = ocr_image.ocr.get_state()
        if ocr_state == 'running':
            overlay.updatetext('elapsed', format_seconds(app_timer.elapsed()))
            overlay.updatetext('status_bar', 'Waiting for text extraction to finish')
            # overlay.updatetext('log_output', 'Waiting for text extraction to finish', append=True)
            overlay.updatetext('ocr_count', ocr_image.ocr.get_img_queue_len())
            get_updates_from_ocr()
            overlay.read()

            if ocr_image.ocr.get_img_queue_len() == 0:
                ocr_image.ocr.stop_OCR()
                overlay.updatetext('status_bar', 'Finished extracting text')
                overlay.updatetext('log_output', 'Finished extracting text', append=True)
                overlay.updatetext('log_output', f'Total time taken: {format_seconds(app_timer.elapsed())}', append=True)
                time.sleep(1)
                get_updates_from_ocr()
                overlay.read()
                time.sleep(1)
                print('Finished: ',str(timedelta(seconds=app_timer.elapsed())))
                print('Reject List: ', ocr_image.ocr.get_rejects())
                print('Confirm list: ', ocr_image.ocr.get_confirms())

                populate_confirm_form()
                if ocr_image.ocr.get_insert_list():
                    if not canceled:
                        overlay.updatetext('status_bar', 'Cleaning data and submitting to API')
                        overlay.updatetext('log_output', 'Cleaning data and submitting to API', append=True)
                        overlay.read()
                        prep_for_api_insert(my_token, ocr_image.ocr.get_insert_list(), server_id, env)
                    else:
                        print('Scan Canceled. No data inserted.')
                        overlay.updatetext('status_bar', 'ERROR')
                        overlay.updatetext('error_output', 'Scan Canceled. No data inserted.', append=True)
                        canceled = False

                img_count = 1
                overlay.enable('Run')
                if 'confirm_names' in access_groups and ocr_image.ocr.get_confirms():
                    overlay.show_confirm()


main()
