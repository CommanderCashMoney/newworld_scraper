import logging
from pathlib import Path
from queue import Queue
from threading import Thread

from app.ocr.ocr_image import OCRImage
from app.ocr.price_validation import PriceValidator
from app.overlay.overlay_updates import OverlayUpdateHandler


class _OCRQueue:
    def __init__(self) -> None:
        self.continue_processing = True
        self.queue = Queue()
        self.queue.empty()
        self._processing_thread = Thread(target=self.process_queue, name="OCR Queue", daemon=True)
        self.total_images = 0
        self.total_removals = 0
        self.ocr_processed_items = []
        self.validator = PriceValidator(self.ocr_processed_items)

    def add_to_queue(self, img_path: Path):
        self.total_images += 1
        OverlayUpdateHandler.update("key_count", self.total_images)
        ocr_image = OCRImage(img_path)
        self.queue.put(ocr_image)

    def process_queue(self) -> None:
        logging.info(f"OCR Queue is ready to accept images.")
        while self.continue_processing:
            next_item: OCRImage = self.queue.get()
            if not self.continue_processing or next_item is None:  # a none object was put in to unstick the queue
                break

            self.ocr_processed_items.extend(next_item.parse_prices())
            self.validator.validate_next_batch()
            OverlayUpdateHandler.update("listings_count", len(self.ocr_processed_items))
            OverlayUpdateHandler.update("ocr_count", self.queue.qsize())
            bad_indexes = len(self.validator.bad_indexes)
            accuracy = 1 - bad_indexes / len(self.ocr_processed_items) or 1
            accuracy_pc = round(accuracy * 100, 1)
            OverlayUpdateHandler.update("accuracy", f"{accuracy_pc}%")
            OverlayUpdateHandler.update("validate_fails", bad_indexes)
            logging.debug(f"Processed `{next_item.original_path}`")

        logging.info("OCRQueue stopped processing.")

    def start(self) -> None:
        if not self._processing_thread.is_alive():
            self._processing_thread.start()
        else:
            logging.warning("start() called on OCRQueue, but it is already running!")

    def stop(self) -> None:
        self.continue_processing = False
        if self.queue.qsize() == 0:
            self.queue.put(None)  # noqa - unstick the queue since it is waiting

    def clear(self) -> None:
        self.ocr_processed_items = []
        self.total_images = 0
        # delete images


OCRQueue = _OCRQueue()
