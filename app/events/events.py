from app import events
from app.api import perform_latest_version_check
from app.api.v1_methods import login_event, login_completed
from app.ocr import start_run
from app import selected_settings
from app.ocr.crawler import Crawler
from app.self_updating import download_update, version_fetched, download_complete

DO_NOTHING = lambda x: ...  # noqa

EVENT_MAP = {
    events.APP_LAUNCHED: perform_latest_version_check,
    events.LOGIN_BUTTON: login_event,
    events.LOGIN_COMPLETED_EVENT: login_completed,
    events.VERSION_FETCHED_EVENT: version_fetched,
    events.BEGIN_DOWNLOAD_UPDATE: download_update,
    events.NEW_VERSION_DOWNLOADED: download_complete,
    events.INSTALLER_LAUNCHED_EVENT: DO_NOTHING,  # todo: should this be calling some exit func?
    events.RUN_BUTTON: start_run,

    # update settings
    events.PAGE_INPUT: selected_settings.update_pages,
    events.USERNAME_INPUT: selected_settings.update_username,
    events.PASSWORD_INPUT: selected_settings.update_password,
    events.TEST_RUN_TOGGLE: selected_settings.update_test_run,
    events.AUTO_SECTIONS_TOGGLE: selected_settings.update_auto_sections,
    events.SERVER_SELECT: selected_settings.update_server_select,

    events.RESEND_DATA: Crawler.submit_results
}


# unhandled events:

# if event == '-FOLDER-':
#     folder = values['-FOLDER-']
#     insert_list = ocr_image.ocr.get_insert_list()
#     if insert_list:
#         with open(f'{folder}/prices_data.txt', 'w') as f:
#             f.write(json.dumps(insert_list, default=str))
#         OverlayUpdateHandler.update('log_output', f'Data saved to: {folder}/prices_data.txt', append=True)
#     else:
#         OverlayUpdateHandler.update('error_output', 'No data to export to file.', append=True)
