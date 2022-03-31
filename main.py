import logging
import traceback
import sys

import pytesseract

from app import events
from app.overlay import overlay  # noqa
from app.overlay.overlay_logging import OverlayLoggingHandler
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.utils import resource_path


OverlayLoggingHandler.setup_overlay_logging()


def show_exception_and_exit(exc_type, exc_value, tb):
    traceback.print_exception(exc_type, exc_value, tb)
    sys.exit(-1)


sys.excepthook = show_exception_and_exit
pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')


def main():
    from app.ocr.crawler import Crawler
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
