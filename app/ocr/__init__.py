import logging


def start_run(values) -> None:
    from app.ocr.crawler import Crawler
    from app.ocr.ocr_image import OCRImage
    from app.ocr.ocr_queue import OCRQueue, OCRQueue

    from app.events import RUN_BUTTON
    from app.ocr.crawler import Crawler
    from app.overlay.overlay_updates import OverlayUpdateHandler
    from app.selected_settings import SELECTED_SETTINGS

    if SELECTED_SETTINGS.server_id is None:
        logging.error("Can't start run because server ID is not set. Please let us know on Discord!")
        return

    SELECTED_SETTINGS.crawler = Crawler(OCRQueue())
    SELECTED_SETTINGS.crawler.start()
    OverlayUpdateHandler.disable(RUN_BUTTON)
