import logging
import traceback
import sys
from pathlib import Path

import pytesseract

from app import events
from app.overlay import overlay  # noqa
from app.overlay.overlay_logging import OverlayLoggingHandler
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.settings import SETTINGS
from app.utils import resource_path


OverlayLoggingHandler.setup_overlay_logging()


def rm_dir_recurse(path: Path) -> None:
    for file in path.iterdir():
        if file.is_dir():
            rm_dir_recurse(file)
        else:
            file.unlink()
    path.rmdir()


def delete_temp_folder() -> None:
    try:
        rm_dir_recurse(SETTINGS.temp_app_data)
    except PermissionError:
        logging.warning("Couldn't delete temp app data folder as it appears to be in use.")
        logging.info(f"Temp folder is: `{str(SETTINGS.temp_app_data)}`.")


def show_exception_and_exit(exc_type, exc_value, tb):
    delete_temp_folder()
    traceback.print_exception(exc_type, exc_value, tb)
    sys.exit(-1)


sys.excepthook = show_exception_and_exit
pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')


def main():
    events.handle_event(events.APP_LAUNCHED, {})

    while True:
        OverlayUpdateHandler.flush_updates()
        event, values = overlay.window.read()

        if event is None:
            break

        events.handle_event(event, values)

        if event == events.INSTALLER_LAUNCHED_EVENT:
            logging.info("Installing new version, see you soon!")
            break

        # todo: because we aren't spamming the cycle anymore, need to move these to a timer
        overlay.perform_cycle_updates()


if __name__ == "__main__":
    main()
    delete_temp_folder()
