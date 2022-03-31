import difflib
import time
from typing import List

import cv2
import mss
import numpy as np
from pytesseract import pytesseract

from app.overlay.overlay_updates import OverlayUpdateHandler
from app.utils import resource_path
from app.utils.mouse import click, mouse
from app.utils.window import bring_new_world_to_foreground

pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')
EVERYTHING_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:- \\"\\'" """
NUMBERS_PERIODS_COMMAS_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789,.\""""
INTEGERS_ONLY_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789\""""


def get_txt_from_im(name: str, config: str, cropped: np.array) -> str:
    data = pytesseract.image_to_data(cropped, output_type=pytesseract.Output.DICT, config=config)
    data["column_name"] = name
    return data


def pre_process_image(img, scale=2.5):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_BITS)

    lower_color = np.array([75, 40, 40])
    upper_color = np.array([255, 255, 255])

    mask = cv2.inRange(img, lower_color, upper_color)
    res = cv2.bitwise_and(img, img, mask=mask)

    res = cv2.cvtColor(res, cv2.COLOR_RGB2GRAY)

    res = cv2.bilateralFilter(res, 5, 50, 100)
    res = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    res = np.invert(res)
    return res


def grab_screen(region=None):
    left, top, width, height = region
    mon = {"top": top, "left": left, "width": width, "height": height}

    sct = mss.mss()
    g = sct.grab(mon)
    img = np.asarray(g)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    return img


def populate_confirm_form(bad_names: List[str], confirmed_names: List[str]):
    for count, value in enumerate(bad_names):
        if count >= 10:
            break
        OverlayUpdateHandler.update(f'bad-name-{count}', value, size=len(value))
        close_matches = difflib.get_close_matches(value, confirmed_names, n=5, cutoff=0.6)
        close_matches.insert(0, 'Add New')
        size = max(close_matches, key=len)
        OverlayUpdateHandler.visible("logging", False)
        OverlayUpdateHandler.update(f'good-name-{count}', close_matches, size=size)
        OverlayUpdateHandler.enable('add-confirmed-name-{}'.format(count))
        OverlayUpdateHandler.visible("confirm")

