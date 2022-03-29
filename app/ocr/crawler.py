# import time
# from datetime import timedelta
# from enum import Enum
#
# import cv2
# import numpy as np
#
# import ocr_image
# from app.ocr.utils import grab_screen
# from app.overlay import overlay
# from app.utils import format_seconds, mouse, resource_path
# from app.utils.keyboard import press_key
# from app.utils.mouse import click
import time
from datetime import timedelta
from threading import Thread
from typing import Tuple

import cv2
import numpy as np
import pynput

from app.ocr.utils import grab_screen, look_for_cancel_or_refresh, look_for_tp, pre_process_image
from app.utils import resource_path
from app.utils.keyboard import press_key
from app.utils.mouse import click, mouse
from my_timer import Timer

section_list = {
    'Raw Resources': (368, 488),
    'Resources Reset 1': (170, 796),
    'Refined Resources': (368, 568),
    'Resources Reset 2': (170, 796),
    'Cooking Ingredients': (368, 632),
    'Resources Reset 3': (170, 796),
    'Craft Mods': (368, 708),
    'Resources Reset 4': (170, 796),
    'Components': (368, 788),
    'Resources Reset 5': (170, 796),
    'Potion Reagents': (368, 855),
    'Resources Reset 6': (170, 796),
    'Dyes': (368, 936),
    'Resources Reset 7': (170, 796),
    'Azoth': (368, 990),
    'Resources Reset 8': (170, 796),
    'Arcana': (368, 1068),
    'Consumables': (165, 900),
    'Ammunition': (165, 985),
    'House Furnishings': (165, 1091)
}


# class CrawlerState(Enum):
#     confirming_tp = 0
#     scrolling = 1
#     snapping = 2
#


def update_overlay(key: str, value: str):
    overlay = None
    overlay.updatetext(key, value)
    overlay.read()  # this is here to unstick the ui


class _SectionCrawler:
    def __init__(self, parent: "Crawler", section: str) -> None:
        self.parent = parent
        self.section = section
        self.coordinates = section_list[section]
        self.loading_timer = Timer('load')

    def __str__(self) -> str:
        return f"{self.section}: {self.coordinates}"

    def __repr__(self) -> str:
        return f"<SectionCrawler: {self}>"

    def crawl(self) -> None:
        if not look_for_tp():
            self.parent.stop(reason="Couldn't find trading post")
        else:
            print("Found trading post.")

    @staticmethod
    def next_page():
        click('left', (2400, 300))
        # time.sleep(0.1)
        mouse.position = (1300, 480)
        time.sleep(0.1)

    def look_for_scroll(self, section):
        loading_timer = self.loading_timer
        look_for_cancel_or_refresh()
        # look for scrollbar
        if section == 'top':
            reference_aoi = (2438, 418, 34, 34)
            reference_image_file = resource_path('app/images/new_world/top_of_scroll.png')
        elif section == 'btm':
            reference_aoi = (2442, 1314, 27, 27)
            reference_image_file = resource_path('app/images/new_world/btm_of_scroll.png')
        elif section == 'last':
            reference_aoi = (2444, 1378, 25, 25)
            reference_image_file = resource_path('app/images/new_world/btm_of_scroll2.png')

        loading_timer.restart()
        while True:
            reference_grab = grab_screen(region=reference_aoi)
            reference_img = cv2.imread(reference_image_file)
            res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val > 0.98:
                return True

            print(f'loading_scroll {section}')
            update_overlay('status_bar', 'Loading page')
            time.sleep(0.1)
            if loading_timer.elapsed() > 3:
                # we have been loading too long. Somthing is wrong. Skip it.
                print('loading too long. skip it')
                update_overlay(f'error_output', f'Took too long waiting for page to load {self}', append=True)
                # overlay.read()
                return True

    def wait_for_load(self, pages, section):
        if pages > 1:
            self.look_for_scroll(section)
        else:
            aoi = (842, 444, 200, 70)
            img = grab_screen(aoi)
            ref_grab = pre_process_image(img)
            while np.count_nonzero(ref_grab) == 112500:  # ?????
                aoi = (842, 444, 200, 70)
                img = grab_screen(aoi)
                ref_grab = pre_process_image(img)
                print('loading on last page')
            time.sleep(0.3)

    def get_img(self, pages, section):
        self.wait_for_load(pages, section)
        if section == 'last':
            aoi = (927, 1198, 1510, 200)
        else:
            aoi = (927, 430, 1510, 919)
        # todo: what is this?
        img = grab_screen(region=aoi)
        return img

    def get_updates_from_ocr(self):
        # ocr_updates = ocr_image.ocr.get_overlay_updates()
        # for x in ocr_updates:
        #     overlay.updatetext(x[0], x[1], append=x[2])
        #     ocr_image.ocr.remove_one_overlayupdate()
        pass


class _Crawler:
    def __init__(self) -> None:
        self.section_crawlers = [_SectionCrawler(k) for k in section_list.keys()]
        self.current_section = 0
        self.crawler_thread = Thread(target=self.crawl, name="OCR Queue", daemon=True)
        self.stopped = False

    def __str__(self) -> str:
        return f"{self.section_crawlers}: {self.current_section}"

    def crawl(self) -> None:
        print("Started Crawling")
        for section_crawler in self.section_crawlers:
            section_crawler.crawl()

    def start(self) -> None:
        self.stopped = False
        if not self.crawler_thread.is_alive():
            self.crawler_thread.start()

    def stop(self, reason: str) -> None:
        print(f"Stopped crawling because {reason}")
        self.stopped = True



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
def crawl():
    overlay = None
    app_timer = None
    clear_overlay = None
    ocr_image = None
    test_run = None
    get_img = None
    pages = None
    auto_scan_sections = None
    round_timer = None
    ocr_cycle = None

    app_timer.restart()
    clear_overlay(overlay)
    overlay.hide_confirm()
    overlay.hide('resend')
    img_count = 1
    ocr_image.ocr.clean_insert_list()
    ocr_image.ocr.set_cap_state('running')
    ocr_image.ocr.start_OCR()

    if test_run:
        print('Starting TEST run')
        overlay.updatetext('log_output', 'Test scan started', append=True)
        overlay.updatetext('status_bar', 'Test scan started')
        overlay.read()
        img = get_img(pages, 'top')
        ocr_image.ocr.add_img(img, 1)

    else:
        print('Starting REAL run')
        overlay.updatetext('log_output', 'Real scan started', append=True)
        overlay.updatetext('status_bar', 'Real scan started')
        overlay.read()
        canceled = False
        if auto_scan_sections:
            round_timer.restart()

            keypress_exit = False
            # click resources twice because screen won't have focus
            click('left', (170, 796))
            time.sleep(0.2)
            click('left', (170, 796))
            time.sleep(1)
            for key in section_list:
                click('left', section_list[key])
                time.sleep(1)
                mouse.position = (1300, 480)
                if section_list[key] != (170, 796):
                    print(f'Starting new section: {key}')
                    keypress_exit = ocr_cycle(ocr_image.ocr.get_page_count(), app_timer)
                    if keypress_exit:
                        overlay.updatetext('error_output', 'Exit key press', append=True)
                        overlay.updatetext('error_output', 'Scan Canceled. No data inserted.', append=True)
                        overlay.updatetext('status_bar', 'Scan cancelled')
                        overlay.enable('Run')
                        break
                    time.sleep(0.5)

                    # check time to see if moving is required to stop idle check
                    if round_timer.elapsed() > 600:
                        print('Mid cycle pause: ', str(timedelta(seconds=app_timer.elapsed())))
                        press_key(pynput.keyboard.Key.esc)
                        time.sleep(0.5)
                        rand_time = np.random.uniform(0.10, 0.15)
                        press_key('w', rand_time)
                        press_key('s', rand_time)
                        press_key('e')
                        time.sleep(1)
                        round_timer.restart()
        else:
            ocr_cycle(pages, app_timer)

    # SCANNING = False
    # ocr_image.ocr.set_cap_state('stopped')
    # overlay.updatetext('log_output', 'Image capture finished', append=True)


Crawler = _Crawler()
