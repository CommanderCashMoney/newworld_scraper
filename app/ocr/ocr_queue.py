import logging
from pathlib import Path
from queue import Queue
from threading import Thread

from app.ocr.ocr_image import OCRImage
from app.ocr.price_validation import PriceValidator


class OCRQueue:
    def __init__(self, overlay_update_handler: "OverlayUpdateHandler" = None) -> None:
        self.overlay_update_handler = overlay_update_handler
        self._continue_processing = True
        self.queue = Queue()
        self.queue.empty()
        self._processing_thread = Thread(target=self.process_queue, name="OCR Queue", daemon=True)
        self.total_images = 0
        self.total_removals = 0
        self.ocr_processed_items = []
        self.validator = PriceValidator(self.ocr_processed_items)
        self.crawler = None  # type: Crawler
        self.last_received_section = None

    def update_overlay(self, key, value) -> None:
        if not self.overlay_update_handler:
            return
        self.overlay_update_handler.update(key, value)

    def add_to_queue(self, img_path: Path, section: str = None):
        reset_price = self.last_received_section != section
        if reset_price:
            self.last_received_section = section
            self.queue.put("RESET")

        self.total_images += 1
        self.update_overlay("key_count", self.total_images)
        ocr_image = OCRImage(img_path)
        self.queue.put(ocr_image)

    def process_queue(self) -> None:
        logging.info(f"OCR Queue is ready to accept images.")
        while self.continue_processing:
            next_item: OCRImage = self.queue.get()
            if not self.continue_processing or next_item is None:  # a none object was put in to unstick the queue
                break

            if next_item == "RESET":
                self.validator.last_good_price = None
                continue

            self.ocr_processed_items.extend(next_item.parse_prices())
            self.validator.validate_next_batch()
            self.update_overlay("listings_count", len(self.ocr_processed_items))
            self.update_overlay("ocr_count", self.queue.qsize())
            bad_indexes = len(self.validator.bad_indexes)
            accuracy = 1 - bad_indexes / len(self.ocr_processed_items) or 1
            accuracy_pc = round(accuracy * 100, 1)
            self.update_overlay("accuracy", f"{accuracy_pc}%")
            self.update_overlay("validate_fails", bad_indexes)
            logging.debug(f"Processed `{next_item.original_path}`")

        logging.info("OCRQueue stopped processing.")

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
            self.queue.put(None)  # noqa - unstick the queue since it is waiting

    def clear(self) -> None:
        self.ocr_processed_items = []
        self.total_images = 0
        # delete images
