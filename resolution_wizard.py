from typing import Any, Tuple

import cv2
import mss
import numpy as np
import pynput
from PIL import Image

from app.utils.mouse import mouse


def grab_screen(region=None):
    left, top, width, height = region
    mon = {"top": top, "left": left, "width": width, "height": height}

    sct = mss.mss()
    g = sct.grab(mon)
    image = np.asarray(g)
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    return Image.fromarray(image)


IS_WAITING_FOR_PRESS = False
PRESSED = False


def key_pressed(key):
    global IS_WAITING_FOR_PRESS
    code = getattr(key, 'vk', None)
    if not code:
        return
    if IS_WAITING_FOR_PRESS and code == 109:  # numpad -
        global PRESSED
        PRESSED = True


listener = pynput.keyboard.Listener(on_press=key_pressed)
listener.start()


def ask(for_pos: str) -> Tuple[int, int]:
    global IS_WAITING_FOR_PRESS, PRESSED
    IS_WAITING_FOR_PRESS = True
    print(f"please move the mouse to {for_pos} and press -")
    while not PRESSED:
        continue
    pos = mouse.position
    IS_WAITING_FOR_PRESS = False
    PRESSED = False
    return pos


def ask_for_area(for_area: str, capture=True) -> Tuple[Tuple[int, int, int, int], Any]:
    pos1 = ask(f"top left of {for_area}")
    pos2 = ask(f"bottom right of {for_area}")
    region = pos1[0], pos1[1], pos2[0] - pos1[0], pos2[1] - pos1[1]
    if capture:
        return region, grab_screen(region)
    return region, None

base = "app/images/new_world/1080p"
# img = grab_screen((694, 316-50, 1138, 694+50))
# img.save(f"{base}/tp_img.png")

# trading_post_label = ask_for_area("trading_post_label.png")
# trading_post_label[1].save(f"{base}/trading_post_label.png")
# print(f"trading_post_label - {trading_post_label[0]}")
#
# top_of_scroll = ask_for_area("top_of_scroll.png")
# top_of_scroll[1].save(f"{base}/top_of_scroll.png")
# print(f"top_of_scroll - {top_of_scroll[0]}")
#
# btm_of_scroll = ask_for_area("btm_of_scroll.png")
# btm_of_scroll[1].save(f"{base}/btm_of_scroll.png")
# print(f"btm_of_scroll - {btm_of_scroll[0]}")
#
# btm_of_scroll2 = ask_for_area("btm_of_scroll2.png")
# btm_of_scroll2[1].save(f"{base}/btm_of_scroll2.png")
# print(f"btm_of_scroll2 - {btm_of_scroll2[0]}")
#
# cancel_btn = ask_for_area("cancel_btn.png")
# cancel_btn[1].save(f"{base}/cancel_btn.png")
# print(f"cancel_btn - {cancel_btn[0]}")

# refresh_btn = ask_for_area("refresh_btn.png")
# refresh_btn[1].save(f"{base}/refresh_btn.png")
# print(f"refresh_btn - {refresh_btn[0]}")

# trading_post_label - (341, 29, 103, 28)
# top_of_scroll - (1833, 651, 19, 29)
# btm_of_scroll - (1833, 973, 19, 38)
# btm_of_scroll2 - (1833, 681, 16, 33)
# cancel_btn - (556, 745, 390, 72)


# next_page_coords = ask("next_page_coords")
# print(next_page_coords)
# pages_bbox = ask_for_area('pages_bbox', capture=False)
# print(pages_bbox)
# items_bbox = ask_for_area('items_bbox (large)', capture=False)
# print(items_bbox)
# items_bbox_last = ask_for_area('items_bbox (small)', capture=False)
# print(items_bbox_last)
# first_item_listing_bbox = ask_for_area('first_item_listing_bbox', capture=False)
# print(first_item_listing_bbox)
#
while True:
    first_item_listing_bbox = ask('x')
    print(first_item_listing_bbox)
