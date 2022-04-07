import logging
from pathlib import Path
from queue import Queue
from threading import Thread

from app.ocr.ocr_image import OCRImage
from app.ocr.validation.listing_validation import ListingValidator


class OCRQueue:
    def __init__(self, overlay_update_handler: "OverlayUpdateHandler" = None) -> None:
        self.overlay_update_handler = overlay_update_handler
        self._continue_processing = True
        self.queue = Queue()
        self.queue.empty()
        self._processing_thread = Thread(target=self.process_queue, name="OCR Queue", daemon=True)
        self.total_images = 0
        self.total_removals = 0
        self.validator = ListingValidator()
        self.crawler = None  # type: Crawler
        self.to_validate = []
        self.SECTION_COMPLETE_EVENT = "RESET"
        self.RUN_COMPLETE_EVENT = "FINISHED"
        self.PREMATURELY_STOP_EVENT = "STOP"
        self.ocr_processed_listings = 0

    def update_overlay(self, key, value) -> None:
        if not self.overlay_update_handler:
            return
        self.overlay_update_handler.update(key, value)

    def add_to_queue(self, img_path: Path, section: str = None):
        self.total_images += 1
        self.update_overlay("key_count", self.total_images)
        ocr_image = OCRImage(img_path, section)
        self.queue.put(ocr_image)

    def notify_section_complete(self) -> None:
        self.queue.put(self.SECTION_COMPLETE_EVENT)

    def complete_current_work_and_die(self) -> None:
        self.queue.put(self.RUN_COMPLETE_EVENT)

    def process_queue(self) -> None:
        logging.info(f"OCR Queue is ready to accept images.")
        while self.continue_processing:
            next_item: OCRImage = self.queue.get()
            self.update_overlay("ocr_count", self.queue.qsize())
            if next_item in [self.PREMATURELY_STOP_EVENT, self.RUN_COMPLETE_EVENT]:
                break

            if not self.continue_processing:
                break

            if next_item != self.SECTION_COMPLETE_EVENT:
                parsed_prices = next_item.parse_prices()
                self.ocr_processed_listings += len(parsed_prices)
                self.update_overlay("listings_count", self.ocr_processed_listings)
                self.to_validate.extend(parsed_prices)
                continue
            elif len(self.to_validate) == 0:
                continue

            section = self.to_validate[0]["section"]
            self.update_overlay('status_bar', f'Validating section {section}')
            self.validator.validate_section(self.to_validate)
            self.to_validate.clear()

            bad_indexes = len(self.validator.bad_indexes)
            accuracy = 1 - bad_indexes / len(self.validator.price_list) or 1
            accuracy_pc = round(accuracy * 100, 1)
            self.update_overlay("accuracy", f"{accuracy_pc}%")
            self.update_overlay("validate_fails", bad_indexes)
            logging.info(f"Section validated: `{section}`")

        logging.info(f"OCRQueue stopped processing")

    def start(self) -> None:
        if not self._processing_thread.is_alive():
            self._processing_thread.start()
        else:
            logging.warning("start() called on OCRQueue, but it is already running!")

    @property
    def thread_is_alive(self) -> bool:
        return self._processing_thread.is_alive()

    @property
    def continue_processing(self) -> None:
        has_crawler = bool(self.crawler)
        keep_going = not has_crawler or not self.crawler.stopped
        return keep_going and self._continue_processing is True

    def stop(self) -> None:
        self._continue_processing = False
        self.queue.empty()
        if self.queue.qsize() == 0:
            self.queue.put(self.RUN_COMPLETE_EVENT)  # noqa - unstick the queue since it is waiting

    def clear(self) -> None:
        self.total_images = 0
        # delete images
