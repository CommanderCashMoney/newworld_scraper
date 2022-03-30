import json
import logging
import traceback

from app import events
from app.nwmp_api_old import login_event
from app.ocr import OCRQueue
from app.ocr.crawler import Crawler
from app.overlay.overlay_updates import OverlayUpdateHandler
import pytesseract
import sys
from app.overlay import overlay  # noqa
from app.overlay.overlay_logging import OverlayLoggingHandler

from app.utils import resource_path
from app.nwmp_api import check_latest_version


OverlayLoggingHandler.setup_overlay_logging()


def show_exception_and_exit(exc_type, exc_value, tb):
    traceback.print_exception(exc_type, exc_value, tb)
    sys.exit(-1)


sys.excepthook = show_exception_and_exit
pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')


def main():
    overlay.window.perform_long_operation(check_latest_version, events.VERSION_FETCHED_EVENT)

    while True:
        OverlayUpdateHandler.flush_updates()
        event, values = overlay.window.read()
        events.handle_event(event, values)
        if event is None or event == events.INSTALLER_LAUNCHED_EVENT:  # quit
            break
        # todo: because we aren't spamming the cycle anymore, need to move these to a timer
        overlay.perform_cycle_updates()
        Crawler.update_elapsed()

        # test_t event -> Crawler
        # if values.get('test_t'):
        #     test_run = True
        #     ocr_image.ocr.test_run(True)
        # else:
        #     test_run = False
        #     ocr_image.ocr.test_run(False)

        # sections_auto -> crawler
        # auto_scan_sections = bool(values.get('sections_auto'))

        # remove this, only set in settings
        # env = 'dev' if values.get('dev') else 'prod'
        # ocr_image.ocr.set_env(env)

        # server_select only important for submission
        server_id = values.get('server_select', '')

        # crawler should be handling this
        # try:
        #     pages = int(values.get('pages', 1))
        # except ValueError:
        #     pages = 1

        if event == events.RUN_BUTTON and server_id != '':
            Crawler.start()
            OCRQueue.start()
            OverlayUpdateHandler.disable(events.RUN_BUTTON)

        # nowhere to put this yet
        # if event == 'Clear':
        #     ocr_image.ocr.clear()
        #     for x in range(10):
        #         OverlayUpdateHandler.update(f'good_name_{x}', '')
        #         OverlayUpdateHandler.update(f'bad_name_{x}', '')
        #
        #         overlay.disable('add{}'.format(x))

        # nowhere to put this yet
        # if event[:3] == 'add':
        #     # manually add from the confirm form
        #     row_num = event[3:]
        #     name_list = []
        #     name_list.append(values[f'bad_name_{row_num}'])
        #     name_list.append(values[f'good_name_{row_num}'])
        #     overlay.disable(event)
        #     if values[f'good_name_{row_num}'] == 'Add New':
        #         print(f'adding to confirmed names: {name_list}')
        #         add_single_item(name_list, env, 'confirmed_names_insert')
        #         OverlayUpdateHandler.update('log_output', f'adding to confirmed names: {name_list}', append=True)
        #     else:
        #         print(f'adding to name cleanup dict: {name_list}')
        #         add_single_item(name_list, env, 'name_cleanup_insert')
        #         OverlayUpdateHandler.update('log_output', f'adding to name cleanup: {name_list}', append=True)
        #
        # # nowhere to put this yet
        # if event == 'next_btn':
        #     next_confirm_page()

        # if event == 'resend':
        #     overlay.disable('resend')
        #     overlay.read()
        #     prices_data_resend = api_insert(*prices_data_resend)

        # if event == '-FOLDER-':
        #     folder = values['-FOLDER-']
        #     insert_list = ocr_image.ocr.get_insert_list()
        #     if insert_list:
        #         with open(f'{folder}/prices_data.txt', 'w') as f:
        #             f.write(json.dumps(insert_list, default=str))
        #         OverlayUpdateHandler.update('log_output', f'Data saved to: {folder}/prices_data.txt', append=True)
        #     else:
        #         OverlayUpdateHandler.update('error_output', 'No data to export to file.', append=True)


if __name__ == "__main__":
    main()
