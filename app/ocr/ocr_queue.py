import logging
from pathlib import Path
from queue import Queue
from threading import Thread

from app.ocr.ocr_image import OCRImage


class _OCRQueue:
    def __init__(self) -> None:
        self.continue_processing = True
        self.queue = Queue()
        self.queue.empty()
        self._processing_thread = Thread(target=self.process_queue, name="OCR Queue", daemon=True)

    def add_to_queue(self, img_path: Path):
        ocr_image = OCRImage(img_path)
        self.queue.put(ocr_image)

    def process_queue(self) -> None:
        print(f"OCR Queue is ready to accept images.")
        while self.continue_processing:
            next_item: OCRImage = self.queue.get()
            if not self.continue_processing or next_item is None:  # a none object was put in to unstick the queue
                break
            next_item.parse_prices()
            print(f"Processed `{next_item.original_path}`")
        print("OCRQueue stopped processing.")

    def start(self) -> None:
        if not self._processing_thread.is_alive():
            self._processing_thread.start()
        else:
            logging.warning("start() called on OCRQueue, but it is already running!")

    def stop(self) -> None:
        self.continue_processing = False
        if self.queue.qsize() == 0:
            self.queue.put(None)  # noqa - unstick the queue since it is waiting


OCRQueue = _OCRQueue()
