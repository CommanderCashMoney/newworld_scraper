from app import events
from app.nwmp_api_old import login_event, login_completed
from app.self_updating import download_update, version_fetched, download_complete

DO_NOTHING = lambda x: ...  # noqa

EVENT_MAP = {
    events.LOGIN_BUTTON: login_event,
    events.LOGIN_COMPLETED_EVENT: login_completed,
    events.VERSION_FETCHED_EVENT: version_fetched,
    events.BEGIN_DOWNLOAD_UPDATE: download_update,
    events.NEW_VERSION_DOWNLOADED: download_complete,
    events.INSTALLER_LAUNCHED_EVENT: DO_NOTHING,  # todo: should this be calling some exit func?
}
