from app import events
from app.api import perform_latest_version_check
from app.api.v1_methods import login_event, login_completed
from app.ocr import start_run
from app import session_data
from app.overlay.overlay_event_handlers import popup_keybinds
from app.self_updating import download_update, version_fetched, download_complete
from app.settings import SETTINGS, save

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
    events.PAGE_INPUT: session_data.update_pages,
    events.USERNAME_INPUT: session_data.update_username,
    events.PASSWORD_INPUT: session_data.update_password,
    events.TEST_RUN_TOGGLE: session_data.update_test_run,
    events.SERVER_SELECT: session_data.update_server_select,
    events.CHANGE_KEY_BINDS: popup_keybinds,
    events.KEYBINDS_SAVED: save,

    # events.RESEND_DATA: session_data.SESSION_DATA.submit_pending_submission_data,
    events.DOWNLOAD_SCAN_DATA: session_data.save_scan_data,
}
