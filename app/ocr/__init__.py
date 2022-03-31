import logging

from app.ocr.ocr_image import OCRImage
from app.ocr.ocr_queue import OCRQueue

from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS


def start_run(values) -> None:
    from app.events import RUN_BUTTON
    from app.ocr.crawler import Crawler
    if SELECTED_SETTINGS.server_id is None:
        logging.error("Can't start run because server ID is not set. Please let us know on Discord!")
        return
    Crawler.start()
    OCRQueue.start()
    OverlayUpdateHandler.disable(RUN_BUTTON)
