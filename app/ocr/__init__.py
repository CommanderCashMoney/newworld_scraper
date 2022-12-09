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
    SESSION_DATA.update_run_id()
    OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", visible=False)
    queue = OCRQueue(overlay_update_handler=OverlayUpdateHandler)
    SESSION_DATA.crawler = Crawler(queue, run_id=SESSION_DATA.current_run_id)
    SESSION_DATA.crawler.start()
    for key in ["key_count", "ocr_count", "listings_count", "validate_fails"]:
        OverlayUpdateHandler.update(key, "0")
    OverlayUpdateHandler.update("accuracy", "-")
    OverlayUpdateHandler.update("log_output", "")
    OverlayUpdateHandler.update("error_output", "")
    OverlayUpdateHandler.disable(RUN_BUTTON)
    # OverlayUpdateHandler.visible(events.TEST_RUN_TOGGLE, visible=False)
    # OverlayUpdateHandler.visible(events.CLOSE_NW_TOGGLE, visible=False)
    OverlayUpdateHandler.visible("advanced", visible=False)
    OverlayUpdateHandler.visible(events.CHANGE_KEY_BINDS, visible=False)
    OverlayUpdateHandler.visible(events.SECTION_TOGGLE, visible=False)
