import logging
import time
from enum import Enum
from typing import Any

import numpy as np
from pytesseract import pytesseract


from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.resolution_settings import Resolution
from app.ocr.utils import parse_page_count, pre_process_page_count_image, screenshot_bbox, pre_process_listings_image
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
        self.section_images_count = 0
        self.load_fail_count = 0
        self.retry_count = 0

    def __str__(self) -> str:
        return f"{self.section}: Page {self.current_page} / {self.pages}"

    def __repr__(self) -> str:
        return f"<SectionCrawler: {self}>"

    @property
    def stopped(self) -> bool:
        return self.parent.stopped

    @property
    def resolution(self) -> Resolution:
        return get_resolution_obj()

    def crawl(self, pages_to_parse: int = 500) -> None:
        bring_new_world_to_foreground()
        if not self.look_for_tp():
            logging.error("Couldn't find TP")
            self.parent.stop(reason="trading post could not be found.", wait_for_death=False)
            return
        self.select_section()
        self.pages = self.get_current_screen_page_count()
        logging.info(f"Found {self.pages} pages for section {self.section}")
        if pages_to_parse:
            self.pages = min(self.pages, pages_to_parse)
        success = self.crawl_section()
        if not self.stopped and not success:
            self.parent.stop(f"Couldn't find any items at all in section {self.section}", wait_for_death=False)
        else:
            logging.info(f"Crawl for section {self.section} complete.")

    def crawl_section(self) -> bool:
        for i in range(self.pages):
            if self.stopped:
                break
            crawl_success = self.crawl_page()
            if not crawl_success and (self.load_fail_count > 4 or self.retry_count > 4):
                self.retry_count = 0
                return True
            if self.stopped:
                return False
            if not self.next_page():
                self.parent.stop("Couldn't find TP.", wait_for_death=False)
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
            if self.retry_count > 4:
                logging.error(f'Too many consecutive page resets, skipping to next section.')
                return False
            self.reset_mouse_position()
            screenshot = self.snap_items()
            self.parent.ocr_queue.add_to_queue(screenshot.file_path, self.section)
            self.scroll()
        OverlayUpdateHandler.update("pages_left", self.pages - self.current_page)
        return True

    def snap_items(self) -> Any:
        self.section_images_count += 1
        prefix = str(self.section_images_count).zfill(3)
        fn = f"{self.section}-{prefix}-{self.scroll_state.value}.png"
        full_path = SETTINGS.temp_app_data / self.parent.run_id / fn
        if self.scroll_state == ScrollState.btm:
            return screenshot_bbox(*self.resolution.items_bbox_last, str(full_path))
        return screenshot_bbox(*self.resolution.items_bbox, str(full_path))

    def scroll(self) -> None:
        scroll_distance = -11 if self.scroll_state != ScrollState.btm else -2
        mouse.scroll(0, scroll_distance)
        if self.scroll_state == ScrollState.top:
            self.scroll_state = ScrollState.mid
        elif self.scroll_state == ScrollState.mid:
            self.scroll_state = ScrollState.btm

    def get_current_screen_page_count(self) -> int:
        pages_bbox = self.resolution.pages_bbox
        screenshot = screenshot_bbox(*pages_bbox)
        res = pre_process_page_count_image(screenshot.img_array)
        custom_config = """--psm 8 -c tessedit_char_whitelist="0123456789of " """
        txt = pytesseract.image_to_data(res, output_type=pytesseract.Output.DICT, config=custom_config)
        pages_str = txt['text'][-1]
        pages, validation_success = parse_page_count(txt)
        if not validation_success:
            bpc = SETTINGS.temp_app_data / self.parent.run_id / "bad-page-counts"
            bpc.mkdir(exist_ok=True, parents=True)
            bpc = bpc / f"{self.parent.run_id}-{self.section}-0.png"
            screenshot.save_image(str(bpc), pil_high_quality=True)
        logging.debug(f"{self.section} - Number of pages looks like: {pages_str} - got {pages}")
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
            self.retry_count += 1
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

        if self.resolution.sections[self.section][1]:
            # resource reset required
            click('left', self.resolution.resources_reset_loc)
            time.sleep(2)

        logging.info(f"Selecting new section {self.section}")
        section_loc = self.resolution.sections[self.section][0]
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
                self.load_fail_count = 0
                return True
            time.sleep(0.1)
        if self.current_page != self.pages:
            logging.error(f'Took too long waiting for page to load {self}, skipping page.')
            self.load_fail_count += 1
            if self.load_fail_count > 4:
                logging.error(f'Too many page load fails, moving to next section. Failed at {self}')
        return False

    def wait_for_load(self):
        if self.pages != self.current_page:
            self.check_scrollbar()
        else:
            first_listing = self.resolution.first_item_listing_bbox
            img = screenshot_bbox(*first_listing).img_array
            ref_grab = pre_process_listings_image(img)
            pure_black = 112500
            while np.count_nonzero(ref_grab) == pure_black:
                img = screenshot_bbox(*first_listing).img_array
                ref_grab = pre_process_listings_image(img)
            logging.info('Page finished loading')
