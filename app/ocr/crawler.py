import logging
import time
from enum import Enum
from threading import Thread
from typing import Any, List

import cv2
import numpy as np
from pytesseract import pytesseract

from app.ocr import OCRQueue
from app.ocr.resolution_settings import Resolution, res_1440p
from app.ocr.utils import grab_screen, pre_process_image
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.utils import resource_path
from app.utils.mouse import click, mouse
from app.utils.timer import Timer
from app.utils.window import bring_new_world_to_foreground
from settings import SETTINGS


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
        self.stopped = False

    def __str__(self) -> str:
        return f"{self.section}: Page {self.current_page} / {self.pages}"

    def __repr__(self) -> str:
        return f"<SectionCrawler: {self}>"

    @property
    def resolution(self) -> Resolution:
        return res_1440p

    def crawl(self) -> None:
        bring_new_world_to_foreground()
        if not self.look_for_tp():
            self.parent.stop(reason="trading post could not be found.")
        self.select_section()
        self.pages = self.get_current_screen_page_count()
        success = self.crawl_section()
        if not self.stopped and success:
            self.parent.stop(f"something is wrong - couldn't find any items at all in section {self.section}")

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
            logging.info("Clicked Cancel")
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

        for attempt in range(10):
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
            aoi = (842, 444, 200, 70)
            img = grab_screen(aoi)
            ref_grab = pre_process_image(img)
            while np.count_nonzero(ref_grab) == 112500:  # ?????
                aoi = (842, 444, 200, 70)
                img = grab_screen(aoi)
                ref_grab = pre_process_image(img)
            logging.info('Page finished loading')


class _Crawler:
    def __init__(self) -> None:
        self.section_crawlers = [_SectionCrawler(self, k) for k in res_1440p.sections.keys()]
        self.current_section = 0
        self.crawler_thread = Thread(target=self.crawl, name="OCR Queue", daemon=True)
        self.stopped = False
        self.started = None

    def __str__(self) -> str:
        return f"{self.section_crawlers}: {self.current_section}"

    def crawl(self) -> None:
        logging.info("Started Crawling")
        self.started = time.perf_counter()
        for section_crawler in self.section_crawlers:
            if self.stopped:
                break
            section_crawler.crawl()

    def start(self) -> None:
        self.stopped = False
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str, is_interrupt=False) -> None:
        self.stopped = True
        if is_interrupt:
            for crawler in self.section_crawlers:
                crawler.stopped = True
                while self.crawler_thread.is_alive():
                    time.sleep(0.1)
        logging.warning(f"Stopped crawling because {reason}")
        if not is_interrupt:
            OverlayUpdateHandler.update('status_bar', 'Error while crawling TP')
        else:
            OverlayUpdateHandler.update('status_bar', 'Manually stopped crawl.')
        OverlayUpdateHandler.enable("Run")

    @property
    def running(self) -> bool:
        return not self.stopped and self.crawler_thread.is_alive()
#
#
# def ocr_cycle(pages, app_timer):
#     global SCANNING, img_count, canceled, page_stuck_counter
#
#     for x in range(pages):
#         if look_for_tp():
#             if ocr_image.ocr.get_state() == 'stopped':
#                 overlay.updatetext('error_output', 'Text extraction stopped prematurely due to an error', append=True)
#                 overlay.updatetext('status_bar', 'ERROR')
#                 canceled = True
#                 overlay.read()
#                 return True
#             overlay.updatetext('pages_left', pages-1)
#             img = get_img(pages, 'top')
#             ocr_image.ocr.add_img(img, img_count)
#             overlay.updatetext('key_count', img_count)
#             overlay.updatetext('ocr_count', ocr_image.ocr.get_img_queue_len())
#             overlay.updatetext('status_bar', 'Capturing images')
#             get_updates_from_ocr()
#             overlay.read()
#             # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
#             # cv2.imwrite(file_name, img)
#             img_count += 1
#
#             if pages == 1:
#                 # see if scroll bar exists on last page
#                 reference_aoi = (2438, 418, 34, 34)
#                 reference_image_file = resource_path('app/images/new_world/top_of_scroll.png')
#                 reference_grab = grab_screen(region=reference_aoi)
#                 reference_img = cv2.imread(reference_image_file)
#                 res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
#                 min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#                 if max_val < 0.98:
#                     break
#
#
#             if not SCANNING:
#                 return True
#             mouse.scroll(0, -11)
#
#             img = get_img(pages, 'btm')
#             ocr_image.ocr.add_img(img, img_count)
#             overlay.updatetext('key_count', img_count)
#             # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
#             # cv2.imwrite(file_name, img)
#             img_count += 1
#
#             #scroll to last 2 items
#             if pages == 1:
#                 #confirm we have a full scroll bar
#                 reference_aoi = (2442, 874, 27, 27)
#                 reference_image_file = resource_path('app/images/new_world/btm_of_scroll.png')
#                 reference_grab = grab_screen(region=reference_aoi)
#                 reference_img = cv2.imread(reference_image_file)
#                 res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
#                 min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#                 if max_val < 0.98:
#                     break
#
#             mouse.scroll(0, -2)
#             img = get_img(pages, 'last')
#             ocr_image.ocr.add_img(img, img_count)
#             overlay.updatetext('key_count', img_count)
#             # file_name = 'testimgs/imgcap-{}.png'.format(img_count)
#             # cv2.imwrite(file_name, img)
#             img_count += 1
#
#             if page_stuck_counter > 2:
#                 # got stuck looking for the scrollbars. exit out and skip section
#                 print('page stuck too long. moving to next section')
#                 overlay.updatetext('error_output', 'Page stuck too long. Moving to next section', append=True)
#                 page_stuck_counter = 0
#                 break
#
#             next_page()
#             pages -= 1
#             overlay.updatetext('pages', pages)
#             overlay.updatetext('elapsed', format_seconds(app_timer.elapsed()))
#             overlay.read()
#
#             if not SCANNING:
#                 return True
#         else:
#             print('couldnt find TP marker')
#             overlay.updatetext('error_output', 'Couldnt find Trading Post window', append=True)
#             overlay.updatetext('status_bar', 'ERROR')
#             canceled = True
#             overlay.read()
#             SCANNING = False
#             return True
#     # need to clear the old price list since we are moving to a new section
#     ocr_image.ocr.set_section_end(img_count)
#     print('finished ocr cycle')
#
# def crawl():
#     overlay = None
#     app_timer = None
#     clear_overlay = None
#     ocr_image = None
#     test_run = None
#     get_img = None
#     pages = None
#     auto_scan_sections = None
#     round_timer = None
#     ocr_cycle = None
#
#     app_timer.restart()
#     clear_overlay(overlay)
#     overlay.hide_confirm()
#     overlay.hide('resend')
#     img_count = 1
#     ocr_image.ocr.clean_insert_list()
#     ocr_image.ocr.set_cap_state('running')
#     ocr_image.ocr.start_OCR()
#
#     if test_run:
#         print('Starting TEST run')
#         overlay.updatetext('log_output', 'Test scan started', append=True)
#         overlay.updatetext('status_bar', 'Test scan started')
#         overlay.read()
#         img = get_img(pages, 'top')
#         ocr_image.ocr.add_img(img, 1)
#
#     else:
#         print('Starting REAL run')
#         overlay.updatetext('log_output', 'Real scan started', append=True)
#         overlay.updatetext('status_bar', 'Real scan started')
#         overlay.read()
#         canceled = False
#         if auto_scan_sections:
#             round_timer.restart()
#
#             keypress_exit = False
#             # click resources twice because screen won't have focus
#             click('left', (170, 796))
#             time.sleep(0.2)
#             click('left', (170, 796))
#             time.sleep(1)
#             for key in section_list:
#                 click('left', section_list[key])
#                 time.sleep(1)
#                 mouse.position = (1300, 480)
#                 if section_list[key] != (170, 796):
#                     print(f'Starting new section: {key}')
#                     keypress_exit = ocr_cycle(ocr_image.ocr.get_page_count(), app_timer)
#                     if keypress_exit:
#                         overlay.updatetext('error_output', 'Exit key press', append=True)
#                         overlay.updatetext('error_output', 'Scan Canceled. No data inserted.', append=True)
#                         overlay.updatetext('status_bar', 'Scan cancelled')
#                         overlay.enable('Run')
#                         break
#                     time.sleep(0.5)
#
#                     # check time to see if moving is required to stop idle check
#                     if round_timer.elapsed() > 600:
#                         print('Mid cycle pause: ', str(timedelta(seconds=app_timer.elapsed())))
#                         press_key(pynput.keyboard.Key.esc)
#                         time.sleep(0.5)
#                         rand_time = np.random.uniform(0.10, 0.15)
#                         press_key('w', rand_time)
#                         press_key('s', rand_time)
#                         press_key('e')
#                         time.sleep(1)
#                         round_timer.restart()
#         else:
#             ocr_cycle(pages, app_timer)

    # SCANNING = False
    # ocr_image.ocr.set_cap_state('stopped')
    # overlay.updatetext('log_output', 'Image capture finished', append=True)


Crawler = _Crawler()
