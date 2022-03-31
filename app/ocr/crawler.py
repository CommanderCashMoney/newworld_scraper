import logging
import time
from enum import Enum
from threading import Thread
from typing import Any

import cv2
import numpy as np
import pynput
from pytesseract import pytesseract
from win32gui import GetForegroundWindow, GetWindowText

from app import events
from app.api import submit_results
from app.ocr import OCRQueue
from app.ocr.resolution_settings import Resolution, res_1440p
from app.ocr.utils import grab_screen, pre_process_image
from app.overlay import overlay
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.selected_settings import SELECTED_SETTINGS
from app.utils import format_seconds
from app.utils.keyboard import press_key
from app.utils.mouse import click, mouse
from app.utils.timer import Timer
from app.utils.window import bring_new_world_to_foreground
from app.settings import SETTINGS


class ScrollState(Enum):
    top = "top"
    mid = "middle"
    btm = "bottom"


def update_overlay(key: str, value: str):
    overlay = None
    overlay.updatetext(key, value)
    overlay.read()  # this is here to unstick the ui


class _SectionCrawler:
    def __init__(self, parent: "Crawler", section: str) -> None:
        self.parent: "Crawler" = parent
        self.section = section
        self.loading_timer = Timer('load')
        self.pages = None
        self.current_page = 1
        self.scroll_state = ScrollState.top

    def __str__(self) -> str:
        return f"{self.section}: Page {self.current_page} / {self.pages}"

    def __repr__(self) -> str:
        return f"<SectionCrawler: {self}>"

    @property
    def stopped(self) -> bool:
        return self.parent.stopped

    @property
    def resolution(self) -> Resolution:
        return res_1440p

    def crawl(self, pages_to_parse: int = 500) -> None:
        bring_new_world_to_foreground()
        if not self.look_for_tp():
            self.parent.stop(reason="trading post could not be found.")
        self.select_section()
        if "Reset" in self.section:
            return
        self.pages = self.get_current_screen_page_count()
        if pages_to_parse:
            self.pages = min(self.pages, pages_to_parse)
            logging.info(f"Parsing {self.pages} pages in section {self.section}.")
        success = self.crawl_section()
        if not self.stopped and not success:
            self.parent.stop(f"something is wrong - couldn't find any items at all in section {self.section}")
        else:
            logging.info(f"Crawl for section {self.section} complete.")

    def crawl_section(self) -> bool:
        for i in range(self.pages):
            if self.stopped:
                break
            self.crawl_page()
            if self.stopped:
                return False
            self.next_page()
        return True

    def crawl_page(self) -> bool:
        app_data_temp = SETTINGS.temp_app_data
        for _ in ScrollState:
            if self.stopped or not self.check_scrollbar():
                return False
            self.reset_mouse_position()
            image = self.snap_items()
            file_name = app_data_temp / f"{self.section}-{self.current_page}-{self.scroll_state.value}.png"
            cv2.imwrite(str(file_name), image)
            OCRQueue.add_to_queue(file_name)
            self.scroll()
        OverlayUpdateHandler.update("pages_left", self.pages - self.current_page)
        return True

    def snap_items(self) -> Any:  # todo: what type is this?
        if self.scroll_state == ScrollState.btm:
            return grab_screen(self.resolution.items_bbox_last)
        return grab_screen(self.resolution.items_bbox)

    def scroll(self) -> None:
        scroll_distance = -11 if self.scroll_state != ScrollState.btm else -2
        mouse.scroll(0, scroll_distance)
        if self.scroll_state == ScrollState.top:
            self.scroll_state = ScrollState.mid
        elif self.scroll_state == ScrollState.mid:
            self.scroll_state = ScrollState.btm

    def get_current_screen_page_count(self) -> int:
        pages_bbox = self.resolution.pages_bbox
        img = grab_screen(pages_bbox)
        img = pre_process_image(img)
        custom_config = """--psm 8 -c tessedit_char_whitelist="0123456789of " """
        txt = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)
        pages_str = txt['text'][-1]
        if not pages_str.isnumeric():
            logging.error('Page count not numeric - assuming 1 page.')
            return 1
        pages = int(pages_str)
        if pages > 500:
            logging.error('Page count greater than 500 - assuming 1 page.')
            return 1
        logging.info(f"Found {pages} pages for section {self.section}")
        return pages

    def press_cancel_or_refresh(self):
        cancel_button = self.resolution.cancel_button
        if cancel_button.compare_image_reference():
            click('left', cancel_button.center)
            logging.info("Accidentally clicked an item - cancelling purchase")
            time.sleep(0.5)

        refresh_button = self.resolution.refresh_button
        if refresh_button.compare_image_reference():
            click('left', refresh_button.center)
            logging.info("Clicked Refresh")
            time.sleep(0.1)

    def look_for_tp(self) -> bool:
        for _ in range(2):
            logging.debug("Checking for TP...")
            self.press_cancel_or_refresh()
            trading_post_ref = self.resolution.trading_post
            if trading_post_ref.compare_image_reference():
                return True
            else:
                time.sleep(1)
        return False

    def select_section(self) -> None:
        logging.info(f"Selecting new section {self.section}")
        section_loc = self.resolution.sections[self.section]
        click('left', section_loc)
        time.sleep(2)  # wait

    def next_page(self):
        click('left', self.resolution.next_page_coords)
        self.scroll_state = ScrollState.top
        self.current_page += 1
        self.reset_mouse_position()

    @staticmethod
    def reset_mouse_position() -> None:
        mouse.position = (1300, 480)  # for scroll

    def check_scrollbar(self) -> bool:
        self.press_cancel_or_refresh()
        # look for scrollbar
        if self.scroll_state == ScrollState.top:
            scroll_ref = self.resolution.top_scroll
        elif self.scroll_state == ScrollState.mid:
            scroll_ref = self.resolution.mid_scroll
        elif self.scroll_state == ScrollState.btm:
            scroll_ref = self.resolution.bottom_scroll

        for attempt in range(30):
            if scroll_ref.compare_image_reference():
                return True
            OverlayUpdateHandler.update('status_bar', 'Loading page')
            time.sleep(0.1)
        logging.error(f'Took too long waiting for page to load {self}, skipping page.')
        return False

    def wait_for_load(self):
        if self.pages > 1:
            self.check_scrollbar()
        else:
            first_listing = self.resolution.first_item_listing_bbox
            img = grab_screen(first_listing)
            ref_grab = pre_process_image(img)
            pure_black = 112500
            while np.count_nonzero(ref_grab) == pure_black:
                img = grab_screen(first_listing)
                ref_grab = pre_process_image(img)
            logging.info('Page finished loading')


class _Crawler:
    def __init__(self) -> None:
        self.section_crawlers = [_SectionCrawler(self, k) for k in res_1440p.sections.keys()]
        self.current_section = 0
        self.crawler_thread = Thread(target=self.crawl, name="Crawler", daemon=True)
        self.stopped = False
        self.started = None
        self.timer_thread = Thread(target=self.update_timer, name="Crawl Timer", daemon=True)
        self.last_moved = 0
        self.final_results = []

    def __str__(self) -> str:
        return f"{self.section_crawlers}: {self.current_section}"

    def update_timer(self) -> None:
        while self.running:
            elapsed = time.perf_counter() - Crawler.started
            OverlayUpdateHandler.update("elapsed", format_seconds(elapsed))
            time.sleep(1)

    def check_move(self) -> None:
        if self.last_moved == 0:
            self.move()
        elif time.perf_counter() - self.last_moved > 60 * 10:
            self.move()

    def move(self) -> None:
        bring_new_world_to_foreground()
        time.sleep(0.5)
        press_key(pynput.keyboard.Key.esc)
        time.sleep(0.5)
        rand_time = np.random.uniform(0.10, 0.15)
        press_key('w', 0.1)
        time.sleep(rand_time)
        press_key('s', 0.1)
        press_key('e')
        self.last_moved = time.perf_counter()

    def crawl(self) -> None:
        if SELECTED_SETTINGS.test_run:
            logging.info(f"Starting test run")
            pages_to_parse = 1
            self.section_crawlers = self.section_crawlers[:1]
        else:
            logging.info(f"Starting full run")
            pages_to_parse = SELECTED_SETTINGS.pages

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
        logging.info("Crawl complete.")
        self.wait_for_parse()
        logging.info("Parsing complete.")
        self.submit_results()
        logging.info("Parsing results complete.")
        self.stopped = True

    def wait_for_parse(self) -> None:
        if OCRQueue.queue.qsize() > 0:
            msg = "Waiting for image parsing."
            logging.info(msg)
            OverlayUpdateHandler.update("status_bar", msg)
            while OCRQueue.queue.qsize() > 0:
                time.sleep(1)
        self.final_results = [
            prices
            for idx, prices in enumerate(OCRQueue.ocr_processed_items)
            if idx not in OCRQueue.validator.bad_indexes
        ]
        OCRQueue.stop()

    def submit_results(self) -> None:
        # todo: need to check for cancel
        if submit_results(self.final_results):
            OCRQueue.clear()

    def start(self) -> None:
        self.stopped = False
        self.started = time.perf_counter()
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str, is_interrupt=False) -> None:
        logging.info("Stop signal received for Crawler.")
        self.stopped = True
        while self.crawler_thread.is_alive():
            logging.info("Waiting for crawler to die.")
            time.sleep(2)
        logging.warning(f"Stopped crawling because {reason}")
        if not is_interrupt:
            OverlayUpdateHandler.update('status_bar', 'Error while crawling TP')
        else:
            OverlayUpdateHandler.update('status_bar', 'Manually stopped crawl.')
        OverlayUpdateHandler.enable(events.RUN_BUTTON)

    @property
    def running(self) -> bool:
        return not self.stopped and self.crawler_thread.is_alive()


Crawler = _Crawler()


# todo: this is broken, it's not working when new world is focused.
def on_press(key):
    active_window_text = GetWindowText(GetForegroundWindow())
    # if active_window_text in ['Trade Price Scraper', "New World"]:
    if key == pynput.keyboard.KeyCode(char='/'):
        Crawler.stop("Manually cancelled!", is_interrupt=True)


listener = pynput.keyboard.Listener(on_press=on_press)
listener.start()
