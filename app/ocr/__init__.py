import logging

from app import events


def start_run(values) -> None:
    from app.ocr.crawler import Crawler
    from app.ocr.ocr_image import OCRImage
    from app.ocr.ocr_queue import OCRQueue, OCRQueue

    from app.events import RUN_BUTTON
    from app.ocr.crawler import Crawler
    from app.overlay.overlay_updates import OverlayUpdateHandler
    from app.session_data import SESSION_DATA

    if SESSION_DATA.server_id is None:
        logging.error("Can't start run because server ID is not set. Please let us know on Discord!")
        return
    OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", visible=False)
    SESSION_DATA.crawler = Crawler(OCRQueue())
    SESSION_DATA.crawler.start()
    OverlayUpdateHandler.disable(RUN_BUTTON)
