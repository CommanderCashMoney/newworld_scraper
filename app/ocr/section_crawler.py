import logging
import re
import time
from enum import Enum
from typing import Any

import cv2
import numpy as np
from pytesseract import pytesseract

from app.ocr.resolution_settings import Resolution, res_1440p
from app.ocr.utils import grab_screen, pre_process_image
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.utils.mouse import click, mouse
from app.utils.timer import Timer
from app.utils.window import bring_new_world_to_foreground
from app.settings import SETTINGS


class ScrollState(Enum):
    top = "top"
    mid = "middle"
    btm = "bottom"


class SectionCrawler:
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
            logging.error("Couldn't find TP")
            self.parent.stop(reason="trading post could not be found.")
        self.select_section()
        if "Reset" in self.section:
            return
        self.pages = self.get_current_screen_page_count()
        logging.info(f"Found {self.pages} pages for section {self.section}")
        if pages_to_parse:
            self.pages = min(self.pages, pages_to_parse)
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
            if not self.next_page():
                self.parent.stop("Couldn't find TP.")
                return False
        OverlayUpdateHandler.update("pages_left", "-")
        self.parent.ocr_queue.notify_section_complete()
        return True

    def crawl_page(self) -> bool:
        OverlayUpdateHandler.update('status_bar', f'Crawling section {self.section}')
        app_data_temp = SETTINGS.temp_app_data / self.parent.run_id
        app_data_temp.mkdir(exist_ok=True)
        for _ in ScrollState:
            if self.stopped or not self.check_scrollbar():
                return False
            self.reset_mouse_position()
            image = self.snap_items()
            fn = f"{self.section}-{self.current_page}-{self.scroll_state.value}.png"
            file_name = app_data_temp / fn
            cv2.imwrite(str(file_name), image)
            self.parent.ocr_queue.add_to_queue(file_name, self.section)
            self.scroll()
        OverlayUpdateHandler.update("pages_left", self.pages - self.current_page)
        return True

    def snap_items(self) -> Any:
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
        logging.debug(f"Number of pages looks like: {pages_str}")
        if not pages_str:
            logging.error("Could not find ANY page count information. Assuming 1.")
            return 1

        pages_str = pages_str.strip()

        if pages_str.isnumeric():
            if int(pages_str) > 500:
                # try see if the o was mistaken for a 0
                try:
                    last_zero = pages_str[:-1].rindex("0")
                except ValueError:
                    logging.error(f"Captured page count is greater than 500. Reverting to 1.")
                    return 1
                pages_str = pages_str[last_zero+1:]
                if not pages_str.isnumeric() or int(pages_str) > 500:
                    logging.error(f"Captured page count is greater than 500. Reverting to 1.")
                    return 1
            return int(pages_str)

        groups = re.search(r"(\d*)\s?o?f?\s?(\d*)", pages_str).groups()
        last = groups[-1]
        if not last.isnumeric():
            logging.error(f"Captured page count info is not numeric. Original capture: {pages_str}")
            return 1

        pages = int(last)
        if pages > 500:
            logging.error('Page count greater than 500 - assuming 1 page.')
            return 1

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
            self.press_cancel_or_refresh()
            trading_post_ref = self.resolution.trading_post
            if trading_post_ref.compare_image_reference():
                return True
            else:
                logging.debug("Couldn't find TP, trying again")
                time.sleep(1)
        return False

    def select_section(self) -> None:
        logging.info(f"Selecting new section {self.section}")
        section_loc = self.resolution.sections[self.section]
        click('left', section_loc)
        time.sleep(2)  # wait

    def next_page(self):
        if not self.look_for_tp():
            return False
        click('left', self.resolution.next_page_coords)
        self.scroll_state = ScrollState.top
        self.current_page += 1
        self.reset_mouse_position()
        return True

    def reset_mouse_position(self) -> None:
        mouse.position = self.resolution.mouse_scroll_loc

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
            time.sleep(0.1)
        if self.current_page != self.pages:
            logging.error(f'Took too long waiting for page to load {self}, skipping page.')
        return False

    def wait_for_load(self):
        if self.pages != self.current_page:
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
