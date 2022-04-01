import logging
import time
from threading import Thread

import numpy as np
import pynput
from win32gui import GetForegroundWindow, GetWindowText

from app import events
from app.ocr.api_submission_data import APISubmission
from app.ocr.ocr_queue import OCRQueue
from app.ocr.resolution_settings import res_1440p
from app.ocr.section_crawler import SectionCrawler
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS
from app.utils import format_seconds
from app.utils.keyboard import press_key
from app.utils.window import bring_new_world_to_foreground


class Crawler:
    def __init__(self, ocr_queue: OCRQueue) -> None:
        self.ocr_queue = ocr_queue
        self.ocr_queue.crawler = self
        self.section_crawlers = [SectionCrawler(self, k) for k in res_1440p.sections.keys()]
        self.current_section = 0
        self.crawler_thread = Thread(target=self.crawl, name="Crawler", daemon=True)
        self._cancelled = False
        self.started = None
        self.timer_thread = Thread(target=self.update_timer, name="Crawl Timer", daemon=True)
        self.last_moved = 0
        self.final_results = []

        listener = pynput.keyboard.Listener(on_press=self.on_press)
        listener.start()

    def __str__(self) -> str:
        return f"{self.section_crawlers}: {self.current_section}"

    def on_press(self, key):
        active_window_text = GetWindowText(GetForegroundWindow())
        if active_window_text in ['Trade Price Scraper', "New World"]:
            if key == pynput.keyboard.KeyCode(char='/'):
                self.stop("Manually cancelled!", is_interrupt=True)

    def update_timer(self) -> None:
        while self.running:
            elapsed = time.perf_counter() - self.started
            OverlayUpdateHandler.update("elapsed", format_seconds(elapsed))
            time.sleep(1)

    def check_move(self) -> None:
        if self.last_moved == 0:
            self.move()
        elif time.perf_counter() - self.last_moved > 60 * 10:
            self.move()

    def move(self) -> None:
        try:
            bring_new_world_to_foreground()
        except:  # noqa
            self.stop(reason="New World doesn't seem to be open.", is_error=True)
            return
        time.sleep(0.5)
        press_key(pynput.keyboard.Key.esc)
        time.sleep(0.5)
        rand_time = np.random.uniform(0.10, 0.15)
        press_key('w', 0.1)
        time.sleep(rand_time)
        press_key('s', 0.1)
        press_key('e')
        time.sleep(2)
        # hack time
        if not self.section_crawlers[0].look_for_tp():
            self.stop(reason="couldn't find TP", is_error=True)
        self.last_moved = time.perf_counter()

    def crawl(self) -> None:
        self.ocr_queue.start()
        if SELECTED_SETTINGS.test_run:
            logging.info(f"Starting test run")
            pages_to_parse = 1
            self.section_crawlers = self.section_crawlers[:2]
        else:
            logging.info(f"Starting full run")
            pages_to_parse = SELECTED_SETTINGS.pages

        logging.info("Started Crawling")
        self.started = time.perf_counter()
        self.timer_thread.start()
        for section_crawler in self.section_crawlers:
            if "Reset" in section_crawler.section:
                self.check_move()  # safe because we are about to reset
            if self._cancelled:
                break
            self.current_section += 1
            section_crawler.crawl(pages_to_parse)
        logging.info("Crawl complete.")
        if self._cancelled:
            # todo: shut down ocrqueue
            logging.info("Not parsing due to cancellation.")
            return
        self.wait_for_parse()
        logging.info("Parsing complete.")
        pending_submissions = APISubmission(
            price_data=self.final_results,
            bad_name_data=self.ocr_queue.validator.bad_names
        )
        SELECTED_SETTINGS.pending_submission_data = pending_submissions
        self.send_pending_submissions()
        logging.info("Parsing results complete.")
        self.stop(reason="run completed.", wait_for_sweet_release_of_death=False)

    def wait_for_parse(self) -> None:
        if self.ocr_queue.queue.qsize() > 0:
            msg = "Waiting for image parsing."
            logging.info(msg)
            OverlayUpdateHandler.update("status_bar", msg)
            while self.ocr_queue.queue.qsize() > 0:
                time.sleep(1)
        self.final_results = [
            prices
            for idx, prices in enumerate(self.ocr_queue.ocr_processed_items)
            if idx not in self.ocr_queue.validator.bad_indexes
        ]
        self.ocr_queue.stop()

    def send_pending_submissions(self) -> None:
        submission_data = SELECTED_SETTINGS.pending_submission_data
        submission_data.submit()

    def start(self) -> None:
        self._cancelled = False
        self.started = time.perf_counter()
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str, is_interrupt=False, is_error=False, wait_for_sweet_release_of_death=True) -> None:
        self._cancelled = True
        logging.warning(f"Stopped crawling because {reason}")
        while wait_for_sweet_release_of_death and self.crawler_thread.is_alive():
            logging.info("Stopping crawler - waiting for thread to die.")
            time.sleep(1)

        if is_error:
            OverlayUpdateHandler.update('status_bar', 'Error while crawling TP')
        elif is_interrupt:
            OverlayUpdateHandler.update('status_bar', 'Manually stopped crawl.')
        else:
            OverlayUpdateHandler.update('status_bar', 'Run successfully completed.')
        self.reset_ui_state()

    def reset_ui_state(self) -> None:
        # todo: this should just fire the event that we're complete
        OverlayUpdateHandler.enable(events.RUN_BUTTON)
        OverlayUpdateHandler.fire_event(events.OCR_COMPLETE)

    @property
    def stopped(self) -> bool:
        return self._cancelled

    @property
    def running(self) -> bool:
        return not self._cancelled and self.crawler_thread.is_alive()
