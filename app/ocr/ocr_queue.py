import logging
from pathlib import Path
from queue import Queue
from threading import Thread

from app.ocr.ocr_image import OCRImage
from app.ocr.validation.listing_validation import ListingValidator
from app.ocr.api_submission_data import APISubmission
from app.session_data import SESSION_DATA
from app.settings import SETTINGS

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
        self.section_results = []

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
            logging.debug(f"Section validated: `{section}`")
            # SEND SECTION TO API
            should_submit = SETTINGS.is_dev or not SESSION_DATA.test_run
            if should_submit:
                self.section_results = [
                    {
                        "name": listing["validated_name"],  # technically we shouldn't even be using this b/c we have id
                        "avail": listing["avail"],
                        "price": listing["validated_price"],
                        "timestamp": listing["timestamp"],
                        "name_id": listing["name_id"],
                    }
                    for idx, listing in enumerate(self.validator.price_list)
                    if idx not in self.validator.bad_indexes
                ]
                logging.info(f"Submitting {section} data to API.")
                pending_submissions = APISubmission(
                    price_data=self.section_results,
                    bad_name_data=self.validator.bad_names,
                    resolution=self.crawler.resolution.name,
                    price_accuracy=(self.validator.price_accuracy or 0) * 100,
                    name_accuracy=(self.validator.name_accuracy or 0) * 100,
                    section_name=section,
                    session_id=SESSION_DATA.session_hash
                )
                SESSION_DATA.pending_submission_data = pending_submissions
                SESSION_DATA.last_scan_data = pending_submissions
                self.send_pending_submissions()
                if pending_submissions.submit_success:
                    logging.info(f"{section} sent sucessfully.")
                else:
                    logging.info(f"{section} failed to send.")
                self.validator.empty()






        logging.info(f"OCRQueue stopped processing")

    def send_pending_submissions(self) -> None:
        submission_data = SESSION_DATA.pending_submission_data
        submission_data.submit()
        # OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-")

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
