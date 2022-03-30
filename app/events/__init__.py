import logging
from typing import Callable

LOGIN_BUTTON = "-LOGIN-CLICKED-"
LOGIN_COMPLETED_EVENT = "-LOGIN CALLBACK-"  # noqa
VERSION_FETCHED_EVENT = "-VERSION FETCHED-"
BEGIN_DOWNLOAD_UPDATE = "-BEGIN-DOWNLOAD-UPDATE-"
NEW_VERSION_DOWNLOADED = "-DOWNLOADED-NEW-VERSION-"
INSTALLER_LAUNCHED_EVENT = "-INSTALLING-"
RUN_BUTTON = "-RUN-BUTTON-"


def event_map(event_name: str) -> Callable:
    from app.events import events
    return events.EVENT_MAP.get(event_name)


def handle_event(event_name: str, gui_values: dict) -> None:
    func = event_map(event_name)
    if func is None:
        logging.debug(f"Unhandled event {event_name}")
        return
    arg = gui_values.get(event_name)
    if arg is None:
        func(gui_values)
    else:
        func(arg)
