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
RUN_BUTTON = "-RUN-BUTTON-"


def event_map(event_name: str) -> Callable:
    from app.events import events
    return events.EVENT_MAP.get(event_name)


def handle_event(event_name: str, gui_values: dict) -> None:
    func = event_map(event_name)
    sig = signature(func)
    if func is None:
        logging.debug(f"Unhandled event {event_name}")
        return
    arg = gui_values.get(event_name)
    if len(sig.parameters) == 0:
        func()
    elif arg is None:
        func(gui_values)
    else:
        func(arg)
