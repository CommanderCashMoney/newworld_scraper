import json
import logging
import time
from copy import deepcopy
from threading import Thread
from typing import Optional

import numpy as np
import pynput
from win32gui import GetForegroundWindow, GetWindowText

from app import events
from app.ocr.api_submission_data import APISubmission
from app.ocr.ocr_queue import OCRQueue
from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.section_crawler import SectionCrawler
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.session_data import SESSION_DATA
from app.settings import SETTINGS
from app.utils import format_seconds
from app.utils.keyboard import press_key
from app.utils.window import bring_new_world_to_foreground


class Crawler:
    def __init__(self, ocr_queue: OCRQueue, run_id: str) -> None:
        self.run_id = run_id
        self.ocr_queue = ocr_queue
        self.ocr_queue.crawler = self
        self.resolution = get_resolution_obj()
        self.section_crawlers = [SectionCrawler(self, k) for k in self.resolution.sections.keys()]
        self.current_section = 0
        self.crawler_thread = Thread(target=self.crawl, name="Crawler", daemon=True)
        self._cancelled = False
        self.started = None
        self.timer_thread = Thread(target=self.update_timer, name="Crawl Timer", daemon=True)
        self.last_moved = 0
        self.final_results = []
        self._stop_reason = None

        listener = pynput.keyboard.Listener(on_press=self.on_press)
        listener.start()

    def __str__(self) -> str:
        return f"{self.section_crawlers}: {self.current_section}"

    def on_press(self, key):
        active_window_text = GetWindowText(GetForegroundWindow())
        if active_window_text in ['Trade Price Scraper', "New World"]:
            if key == pynput.keyboard.KeyCode(char=SETTINGS.keybindings.cancel_key):
                self.stop("Manually cancelled!", is_interrupt=True)

    def update_timer(self) -> None:
        while self.running:
            elapsed = time.perf_counter() - self.started
            OverlayUpdateHandler.update("elapsed", format_seconds(elapsed))
            time.sleep(1)

    def check_move(self) -> None:
        if SETTINGS.afk_timer is None:
            return
        if self.last_moved == 0 or time.perf_counter() - self.last_moved > SETTINGS.afk_timer:  # 5 min
            logging.info("Moving character...")
            time.sleep(2)
            self.move()

    def move(self) -> None:
        try:
            bring_new_world_to_foreground()
        except:  # noqa
            self.stop(reason="New World doesn't seem to be open.", is_error=True, wait_for_death=False)
            return
        press_key(pynput.keyboard.Key.esc)
        time.sleep(0.5)
        rand_time = np.random.uniform(0.10, 0.15)
        press_key(SETTINGS.keybindings.backward_key, 0.1)
        time.sleep(rand_time)
        press_key(SETTINGS.keybindings.forward_key, 0.1)
        press_key(SETTINGS.keybindings.action_key)
        # hack time
        if not self.section_crawlers[0].look_for_tp():
            self.stop(reason="couldn't find TP", is_error=True, wait_for_death=False)
        self.last_moved = time.perf_counter()

    def crawl(self) -> None:
        self.ocr_queue.start()
        if SESSION_DATA.test_run:
            logging.info(f"Starting test run")
            pages_to_parse = 1
            self.section_crawlers = self.section_crawlers[:2]
        else:
            logging.info(f"Starting full run")
            pages_to_parse = SESSION_DATA.pages

        logging.info("Started Crawling")
        self.started = time.perf_counter()
        self.timer_thread.start()
        for section_crawler in self.section_crawlers:
            if "Reset" in section_crawler.section:
                self.check_move()  # safe because we are about to reset
            if self.stopped:
                break
            self.current_section += 1
            section_crawler.crawl(pages_to_parse)

        if self.stopped:
            logging.info(f"Stopped crawling because {self.stop_reason}.")
            self.ocr_queue.stop()
            return
        else:
            # tell the ocr thread to stop processing once it has completed all its current tasks
            self.ocr_queue.complete_current_work_and_die()
            logging.info("Crawl complete.")

        self.wait_for_parse()
        logging.info("Parsing complete.")
        should_submit = SETTINGS.is_dev or not SESSION_DATA.test_run
        if should_submit:
            logging.info("Submitting data to API.")
            pending_submissions = APISubmission(
                price_data=self.final_results,
                bad_name_data=self.ocr_queue.validator.bad_names,
                resolution=self.resolution.name,
                price_accuracy=self.ocr_queue.validator.price_accuracy * 100 or 0,
                name_accuracy=self.ocr_queue.validator.name_accuracy * 100 or 0
            )
            SESSION_DATA.pending_submission_data = pending_submissions
            SESSION_DATA.last_scan_data = pending_submissions
            self.send_pending_submissions()
            if pending_submissions.submit_success:
                OverlayUpdateHandler.update('status_bar', 'Run successfully completed.')
            else:
                OverlayUpdateHandler.update('status_bar', 'API Submit Failed.')
        logging.info("Parsing results complete.")
        self.stop(reason="run completed.", wait_for_death=False)

    def wait_for_parse(self) -> None:
        if self.ocr_queue.thread_is_alive:
            msg = "Waiting for image parsing."
            logging.info(msg)
            OverlayUpdateHandler.update("status_bar", msg)
            while self.ocr_queue.thread_is_alive:
                logging.debug("Waiting for OCR Queue to finish...")
                time.sleep(1)

        self.final_results = [
            {
                "name": listing["validated_name"],  # technically we shouldn't even be using this b/c we have id
                "avail": listing["avail"],
                "price": listing["validated_price"],
                "timestamp": listing["timestamp"],
                "name_id": listing["name_id"],
            }
            for idx, listing in enumerate(self.ocr_queue.validator.price_list)
            if idx not in self.ocr_queue.validator.bad_indexes
        ]
        self.ocr_queue.stop()
        dict_copy = deepcopy(self.ocr_queue.validator.image_accuracy)
        for filename, info in dict_copy.items():
            file_accuracy = 100 - info["bad_percent"]
            if file_accuracy < 50:
                logging.warning(f"Very bad accuracy on file {filename} ({round(file_accuracy, 1)}%)")
            elif not SETTINGS.is_dev:
                p = SETTINGS.temp_app_data / self.run_id / filename
                p.unlink(missing_ok=True)

    def send_pending_submissions(self) -> None:
        submission_data = SESSION_DATA.pending_submission_data
        submission_data.submit()
        OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-")

    def start(self) -> None:
        OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", False)
        self.started = time.perf_counter()
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str, is_interrupt=False, is_error=False, wait_for_death=True) -> None:
        self._stop_reason = reason
        self._cancelled = True
        while wait_for_death and self.crawler_thread.is_alive():
            logging.info("Stopping crawler - waiting to die.")
            time.sleep(1)

        if is_error:
            OverlayUpdateHandler.update('status_bar', 'Error while crawling TP')
        elif is_interrupt:
            OverlayUpdateHandler.update('status_bar', 'Manually stopped crawl.')
        self.reset_ui_state()

    def reset_ui_state(self) -> None:
        OverlayUpdateHandler.visible("advanced", visible=True)
        OverlayUpdateHandler.visible(events.TEST_RUN_TOGGLE, visible=True)
        OverlayUpdateHandler.enable(events.RUN_BUTTON)
        # todo: need to check this actually works
        OverlayUpdateHandler.fire_event(events.OCR_COMPLETE)

    @property
    def stopped(self) -> bool:
        return not self.running

    @property
    def stop_reason(self) -> Optional[str]:
        if self._stop_reason:
            return self._stop_reason
        elif self._cancelled:
            return "user requested cancellation"
        elif not self.crawler_thread.is_alive():
            return "there was an error in the crawl thread"
        elif not self.ocr_queue.thread_is_alive:
            return "there was an error in the OCR thread"
        return "unknown"

    @property
    def running(self) -> bool:
        return not self._cancelled and self.crawler_thread.is_alive() and self.ocr_queue.thread_is_alive
