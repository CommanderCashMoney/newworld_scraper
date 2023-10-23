import logging
import time
from copy import deepcopy
from threading import Thread
from typing import Optional

import numpy as np
import pynput
from win32gui import GetForegroundWindow, GetWindowText

from app import events
from app.ocr.ocr_queue import OCRQueue
from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.section_crawler import SectionCrawler
from app.overlay.overlay_updates import OverlayUpdateHandler
from app.session_data import SESSION_DATA, update_server_select
from app.settings import SETTINGS
from app.utils import format_seconds
from app.utils.keyboard import press_key
from app.utils.window import bring_new_world_to_foreground, exit_to_desktop, bring_scanner_to_foreground, play_sound
from app.utils.mouse import click
from app.overlay import overlay

class Crawler:
    def __init__(self, ocr_queue: OCRQueue, run_id: str) -> None:
        self.run_id = run_id
        self.ocr_queue = ocr_queue
        self.ocr_queue.crawler = self
        self.resolution = get_resolution_obj()
        self.section_crawlers = [SectionCrawler(self, k) for k in self.resolution.sections.keys() if SESSION_DATA.scan_sections[k]]
        self.buy_order_section_crawlers = [SectionCrawler(self, k) for k in self.resolution.buy_order_sections.keys()]
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
            return

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

        if SETTINGS.ignore_sections:
            logging.info(f"Crawling only the current page")
            pages_to_parse = 1
            self.section_crawlers = self.section_crawlers[:1]

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
            if not SETTINGS.disable_moving:
                self.check_move()
            if self.stopped:
                break
            self.current_section += 1
            if section_crawler.section == 'Sold Items':
                section_crawler.crawl_sold_items()
            elif section_crawler.section == 'Buy Orders':
                self.crawl_buy_orders()
            else:
                sorted_arrow = self.resolution.sort_up_arrow
                for x in range(3):
                    if not sorted_arrow.compare_image_reference():
                        click('left', sorted_arrow.center)
                        time.sleep(3)
                    else:
                        break
                section_crawler.crawl(pages_to_parse)

        if self.stopped:
            logging.info(f"Stopped crawling because {self.stop_reason}.")
            self.ocr_queue.stop()
            return
        else:
            # tell the ocr thread to stop processing once it has completed all its current tasks
            self.ocr_queue.complete_current_work_and_die()
            logging.info("Crawl complete.")

        if SESSION_DATA.close_nw:
            exit_to_desktop()
        bring_scanner_to_foreground()
        self.wait_for_parse()
        if SETTINGS.playsound:
            play_sound()


        logging.info("Parsing results complete.")
        OverlayUpdateHandler.update('status_bar', 'Run successfully completed.')
        self.stop(reason="run completed.", wait_for_death=False)

    def crawl_buy_orders(self):
        pages_to_parse = SESSION_DATA.pages
        for section_crawler in self.buy_order_section_crawlers:
            self.check_move()
            click('left', self.resolution.sell_tab_coords)
            time.sleep(2)
            # choose sold order tab
            click('left', self.resolution.buy_order_all_items)
            time.sleep(2)
            sorted_arrow = self.resolution.buy_order_sort_down_arrow
            for x in range(3):
                if not sorted_arrow.compare_image_reference():
                    click('left', sorted_arrow.center)
                    time.sleep(3)
                else:
                    break
            if self.stopped:
                break
            self.current_section += 1
            section_crawler.crawl(pages_to_parse, is_buy_order=True)

    def wait_for_parse(self) -> None:
        if self.ocr_queue.thread_is_alive:
            msg = "Waiting for image parsing."
            logging.info(msg)
            OverlayUpdateHandler.update("status_bar", msg)
            while self.ocr_queue.thread_is_alive:
                logging.debug("Waiting for OCR Queue to finish...")
                time.sleep(1)

        if SESSION_DATA.pending_submission_data:
            # put this wait in here because I was getting a rare bug where it wouldnt submit the last section. This might be not needed.
            time.sleep(5)
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
        event, values = overlay.window.read(timeout=0)
        if values['-SERVER-SELECT-'] == '(Auto-Detect)':
            if not self.get_server_name():
                self.stop(reason="Could not detect server name.", is_error=True, wait_for_death=False)
                logging.error(f'Could not auto detect Server name')
                return
        OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", False)
        self.started = time.perf_counter()
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str, is_interrupt=False, is_error=False, wait_for_death=True) -> None:
        self._stop_reason = reason
        self._cancelled = True
        while wait_for_death and self.crawler_thread.is_alive():
            logging.info(f"Stopping crawler - {reason} - waiting to die.")
            time.sleep(1)

        if is_error:
            OverlayUpdateHandler.update('status_bar', 'Error while crawling TP')
        elif is_interrupt:
            OverlayUpdateHandler.update('status_bar', 'Manually stopped crawl.')
        self.reset_ui_state()

    def get_server_name(self):

        from app.utils.keyboard import press_key
        from app.utils.mouse import click
        import time
        from app.ocr.utils import screenshot_bbox, pre_process_listings_image, find_closest_match, parse_server_name, find_key_by_value
        from pytesseract import pytesseract

        try:
            bring_new_world_to_foreground()
        except:  # noqa
            # self.stop(reason="New World doesn't seem to be open.", is_error=True, wait_for_death=False)
            bring_scanner_to_foreground()
            return None
        time.sleep(1)
        buy_icon_img = self.resolution.buy_icon
        if not buy_icon_img.compare_image_reference():
            logging.error("Couldn't find TP, please make sure the Trading Post is open")
            bring_scanner_to_foreground()
            return None


        resolution = get_resolution_obj()
        time.sleep(1)
        press_key(pynput.keyboard.Key.esc)
        time.sleep(1)
        press_key(pynput.keyboard.Key.esc)
        time.sleep(1)
        click('left', resolution.menu_loc)
        time.sleep(1)

        server_name_bbox = self.resolution.server_name_bbox
        screenshot = screenshot_bbox(*server_name_bbox)
        res = pre_process_listings_image(screenshot.img_array)
        TEXT_ONLY_CONFIG = """--psm 6 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" """
        txt = pytesseract.image_to_data(res, output_type=pytesseract.Output.DICT, config=TEXT_ONLY_CONFIG)
        parsed_server_name = parse_server_name(txt)
        server_names =  [value['name'] for value in SESSION_DATA.server_list.values()]
        if parsed_server_name is None or '' or len(parsed_server_name) < 3:
            logging.warning(f'Could not parse server name from image: {parsed_server_name}')
            bring_scanner_to_foreground()
            return None

        if parsed_server_name in server_names:
            logging.info(f'Found an exact match for server: {parsed_server_name}')
            server_id = find_key_by_value(SESSION_DATA.server_list, parsed_server_name)
            update_server_select(f'{server_id}-{parsed_server_name}')
            return parsed_server_name
        else:
            matched_server_name, distance = find_closest_match(parsed_server_name, server_names)
            logging.info(f'Matched server name to: {matched_server_name}')
            server_id = find_key_by_value(SESSION_DATA.server_list, matched_server_name)
            update_server_select(f'{server_id}-{matched_server_name}')
            if distance > 2:
                logging.warning(f'Could not find a close match for server name: {parsed_server_name}')
                bring_scanner_to_foreground()
                return None
            return matched_server_name


    def reset_ui_state(self) -> None:
        # OverlayUpdateHandler.visible("advanced", visible=SESSION_DATA.advanced_user)
        # OverlayUpdateHandler.visible(events.TEST_RUN_TOGGLE, visible=True)
        # OverlayUpdateHandler.visible(events.CLOSE_NW_TOGGLE, visible=True)
        OverlayUpdateHandler.enable(events.RUN_BUTTON)
        OverlayUpdateHandler.fire_event(events.OCR_COMPLETE)
        OverlayUpdateHandler.visible(events.SECTION_TOGGLE, visible=True)

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
