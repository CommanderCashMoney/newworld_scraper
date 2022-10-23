import logging
from inspect import signature
from typing import Callable

APP_LAUNCHED = "-APP-LAUNCHED-"
LOGIN_BUTTON = "-LOGIN-CLICKED-"
LOGIN_COMPLETED_EVENT = "-LOGIN CALLBACK-"  # noqa
VERSION_FETCHED_EVENT = "-VERSION FETCHED-"
BEGIN_DOWNLOAD_UPDATE = "-BEGIN-DOWNLOAD-UPDATE-"
NEW_VERSION_DOWNLOADED = "-DOWNLOADED-NEW-VERSION-"
INSTALLER_LAUNCHED_EVENT = "-INSTALLING-"

# settings/inputs
RUN_BUTTON = "-RUN-BUTTON-"
PAGE_INPUT = "-PAGES-INPUT-"
USERNAME_INPUT = "-USERNAME-INPUT-"
PASSWORD_INPUT = "-PASSWORD-INPUT-"
TEST_RUN_TOGGLE = "-TEST-RUN-TOGGLE-"
AUTO_SECTIONS_TOGGLE = "-AUTO-SECTIONS-TOGGLE-"
SERVER_SELECT = "-SERVER-SELECT-"
# RESEND_DATA = "-RESEND-DATA-"
OCR_COMPLETE = "-OCR-COMPLETE-"
DOWNLOAD_SCAN_DATA = "-SAVE-SCAN-DATA-"
KEYBINDS_SAVED = '-KEYBINDS-SAVED-'
CHANGE_KEY_BINDS = "-CHANGE-KEY-BINDS-"


def event_map(event_name: str) -> Callable:
    from app.events import events
    return events.EVENT_MAP.get(event_name)


def handle_event(event_name: str, gui_values: dict) -> None:
    func = event_map(event_name)
    if func is None:
        logging.debug(f"Unhandled event {event_name}")
        return
    sig = signature(func)
    arg = gui_values.get(event_name, "-NOTHING-")
    if len(sig.parameters) == 0:
        func()
    elif arg == "-NOTHING-":
        func(gui_values)
    else:
        func(arg)
