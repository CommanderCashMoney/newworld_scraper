import logging
import time
from enum import Enum
from typing import Any

import numpy as np
from pytesseract import pytesseract


from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.resolution_settings import Resolution
from app.ocr.utils import parse_page_count, pre_process_page_count_image, screenshot_bbox, pre_process_listings_image, parse_current_page, pre_process_current_page_image
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
        self.is_buy_order = False

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

    def crawl(self, pages_to_parse: int = 500, is_buy_order=False) -> None:
        self.is_buy_order = is_buy_order
        bring_new_world_to_foreground()
        if not self.look_for_tp():
            logging.error("Couldn't find TP")
            self.parent.stop(reason="trading post could not be found.", wait_for_death=False)
            return
        if not SETTINGS.ignore_sections:
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
        i = 0
        while i < self.pages:
            i += 1

            if i == self.pages:
                current_page = self.get_current_page()
                if current_page and current_page < i:
                    if current_page < self.pages:
                        logging.info(f'Reached end of section but found {self.pages - current_page} extra pages')
                        i = current_page

            if self.stopped:
                break
            crawl_success = self.crawl_page()
            if not crawl_success and (self.load_fail_count > 4 or self.retry_count > 4):
                self.retry_count = 0
                self.parent.ocr_queue.notify_section_complete()
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
            if self.is_buy_order:
                screenshot = self.snap_items(self.resolution.buy_order_items_bbox)
            else:
                screenshot = self.snap_items(self.resolution.items_bbox)
            self.parent.ocr_queue.add_to_queue(screenshot.file_path, self.section)
            self.scroll()
        OverlayUpdateHandler.update("pages_left", self.pages - self.current_page)
        return True


    def crawl_sold_items(self):
        bring_new_world_to_foreground()
        if not self.look_for_tp():
            logging.error("Couldn't find TP")
            self.parent.stop(reason="trading post could not be found.", wait_for_death=False)
            return
        self.select_section()
        # choose completed items tab
        click('left', self.resolution.sold_order_completed_tab)
        time.sleep(2)
        # choose sold order tab
        click('left', self.resolution.sold_order_sold_items_tab)
        time.sleep(2)
        # check to see if price is sorted properly. This tends to get reset
        sorted_arrow = self.resolution.sold_order_price_sort_down
        for x in range(3):
            if not sorted_arrow.compare_image_reference():
                click('left', sorted_arrow.center)
                time.sleep(1)
            else:
                break
        # crawl
        OverlayUpdateHandler.update('status_bar', f'Crawling section {self.section}')
        app_data_temp = SETTINGS.temp_app_data / self.parent.run_id
        app_data_temp.mkdir(exist_ok=True)
        #  set good mouse position
        mouse.position = self.resolution.sold_order_mouse_scroll_loc
        # check for scrollbar
        top_scroll = self.resolution.sold_order_top_scroll
        bottom_scroll = self.resolution.sold_order_bottom_scroll

        if top_scroll.compare_image_reference():
            #  has a scrollbar
            p = time.perf_counter()

            while not self.stopped and (time.perf_counter() - p) < 15:
                if bottom_scroll.compare_image_reference():
                    screenshot = self.snap_items(self.resolution.sold_order_items_full_bbox)
                    self.parent.ocr_queue.add_to_queue(screenshot.file_path, self.section)
                    break
                else:
                    screenshot = self.snap_items(self.resolution.sold_order_items_bbox)
                    self.parent.ocr_queue.add_to_queue(screenshot.file_path, self.section)

                mouse.scroll(0, -6)
                time.sleep(0.5)

        else:
            # no scroll. just take one pic. differ bbox because for scroll we only look at top 6 rows
            screenshot = self.snap_items(self.resolution.sold_order_items_full_bbox)
            self.parent.ocr_queue.add_to_queue(screenshot.file_path, self.section)

        self.parent.ocr_queue.notify_section_complete()
        return True

    def snap_items(self, bbox) -> Any:
        self.section_images_count += 1
        prefix = str(self.section_images_count).zfill(3)
        fn = f"{self.section}-{prefix}-{self.scroll_state.value}.png"
        full_path = SETTINGS.temp_app_data / self.parent.run_id / fn
        if self.scroll_state == ScrollState.btm:
            if self.is_buy_order:
                return screenshot_bbox(*self.resolution.buy_order_items_bbox_last, str(full_path))
            else:
                return screenshot_bbox(*self.resolution.items_bbox_last, str(full_path))
        return screenshot_bbox(*bbox, str(full_path))

    def scroll(self, retry=False) -> None:
        if self.is_buy_order:
            scroll_distance = -8 if self.scroll_state != ScrollState.btm else -5
        else:
            scroll_distance = -11 if self.scroll_state != ScrollState.btm else -2
        mouse.scroll(0, scroll_distance)
        if not retry:
            if self.scroll_state == ScrollState.top:
                self.scroll_state = ScrollState.mid
            elif self.scroll_state == ScrollState.mid:
                self.scroll_state = ScrollState.btm

    def get_current_screen_page_count(self) -> int:
        if self.is_buy_order:
            pages_bbox = self.resolution.buy_order_pages_bbox
        else:
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

    def get_current_page(self) -> int:
        if self.is_buy_order:
            current_page_bbox = self.resolution.buy_order_current_page_bbox
        else:
            current_page_bbox = self.resolution.current_page_bbox
        screenshot = screenshot_bbox(*current_page_bbox)
        res = pre_process_current_page_image(screenshot.img_array)
        custom_config = """--psm 7 -c tessedit_char_whitelist="0123456789Pageof " """
        txt = pytesseract.image_to_data(res, output_type=pytesseract.Output.DICT, config=custom_config)
        current_page, validation_success = parse_current_page(txt)

        if not validation_success:
            bpc = SETTINGS.temp_app_data / self.parent.run_id / "bad-page-counts"
            bpc.mkdir(exist_ok=True, parents=True)
            bpc = bpc / f"{self.parent.run_id}-{self.section}-0-current-page.png"
            screenshot.save_image(str(bpc), pil_high_quality=True)
            return None
        return current_page


    def press_cancel_or_refresh(self):
        if self.is_buy_order:
            cancel_button = self.resolution.buy_order_cancel_button
            refresh_button = self.resolution.buy_order_refresh_button
        else:
            cancel_button = self.resolution.cancel_button
            refresh_button = self.resolution.refresh_button
        if cancel_button.compare_image_reference():
            click('left', cancel_button.center)
            logging.info("Accidentally clicked an item - cancelling purchase")
            time.sleep(0.5)

        if refresh_button.compare_image_reference():
            click('left', refresh_button.center)
            logging.info("Clicked Refresh")
            self.retry_count += 1
            time.sleep(0.1)

    def look_for_tp(self) -> bool:
        for _ in range(2):
            self.press_cancel_or_refresh()
            my_orders_clip_ref = self.resolution.buy_icon
            if my_orders_clip_ref.compare_image_reference():
                return True
            else:
                logging.debug("Couldn't find TP, trying again")
                time.sleep(1)
        return False

    def select_section(self) -> None:

        if not self.is_buy_order:
            if self.resolution.sections[self.section][1]:
                # resource reset required
                click('left', self.resolution.resources_reset_loc)
                time.sleep(2)

        logging.info(f"Selecting new section {self.section}")
        if self.is_buy_order:
            section_loc = self.resolution.buy_order_sections[self.section][0]
        else:
            section_loc = self.resolution.sections[self.section][0]
        click('left', section_loc)
        time.sleep(2)  # wait

    def next_page(self):
        if not self.look_for_tp():
            return False
        if self.is_buy_order:
            click('left', self.resolution.buy_order_next_page_coords, hold=0.05)
        else:
            click('left', self.resolution.next_page_coords, hold=0.05)
        self.scroll_state = ScrollState.top
        self.current_page += 1
        self.reset_mouse_position()
        return True

    def reset_mouse_position(self) -> None:
        if self.is_buy_order:
            mouse.position = self.resolution.buy_order_mouse_scroll_loc
        else:
            mouse.position = self.resolution.mouse_scroll_loc

    def check_scrollbar(self) -> bool:
        self.press_cancel_or_refresh()
        # look for scrollbar
        if self.is_buy_order:
            if self.scroll_state == ScrollState.top:
                scroll_ref = self.resolution.buy_order_top_scroll
            elif self.scroll_state == ScrollState.mid:
                scroll_ref = self.resolution.buy_order_mid_scroll
            elif self.scroll_state == ScrollState.btm:
                scroll_ref = self.resolution.buy_order_bottom_scroll
        else:
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
            # Sometimes the game doesnt seem the register the mouse wheel scroll down and thinks it's on the middle section but the scroll bar is on the top.
            if attempt > 5 and self.scroll_state == ScrollState.mid:
                if self.is_buy_order:
                    top_scroll_ref = self.resolution.buy_order_top_scroll
                    # bottom_scroll_ref = self.resolution.buy_order_bottom_scroll
                else:
                    top_scroll_ref = self.resolution.top_scroll
                    # bottom_scroll_ref = self.resolution.bottom_scroll

                if top_scroll_ref.compare_image_reference():
                    print(f'Game didnt register the scroll down, trying again - {attempt}')
                    self.scroll(retry=True)

                    time.sleep(0.5)
                # elif bottom_scroll_ref.compare_image_reference():
                #     print(f'Scrolled down too far, scrolling back up to top - {attempt}')
                #     mouse.scroll(0, 14)
                #     time.sleep(0.5)

            time.sleep(0.1)
        if self.current_page != self.pages:  # if we're not on the last page, try again
            scrollbar_conf = scroll_ref.compare_image_reference(ret_val='debug')
            logging.error(f'Page load for {self} took too long, trying again. Conf: {round(scrollbar_conf, 2)} Pos: {self.scroll_state}')
            self.load_fail_count += 1

            if self.load_fail_count > 4:
                logging.error(f'Too many page load fails, moving to next section. May have reached the end of section. Failed at {self}')
        elif self.current_page == self.pages:
            if self.scroll_state == ScrollState.top:
                scroll_ref = self.resolution.bottom_scroll
                if scroll_ref.compare_image_reference():
                    # this means we are on the last page and the scrollbar is at the bottom.
                    logging.info(f'Reached last page. Scrollbar is at the bottom')
                    return False
                else:
                    # this means we are on the last page and the scroll bar isnt at the bottom or top. So it likely is not there at all and we can assume the last page is a single page. So return true
                    logging.debug(f'Reached last page. It did not have a scrollbar')
                    return True
        return False

    def wait_for_load(self):
        if self.pages != self.current_page:
            self.check_scrollbar()
        else:
            if self.is_buy_order:
                first_listing = self.resolution.buy_order_first_item_listing_bbox
            else:
                first_listing = self.resolution.first_item_listing_bbox
            img = screenshot_bbox(*first_listing).img_array
            ref_grab = pre_process_listings_image(img)
            pure_black = 112500
            while np.count_nonzero(ref_grab) == pure_black:
                img = screenshot_bbox(*first_listing).img_array
                ref_grab = pre_process_listings_image(img)
            logging.info('Page finished loading')
