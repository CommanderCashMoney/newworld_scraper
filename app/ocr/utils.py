import logging
import re
from typing import Any, Tuple, Union
import Levenshtein
import cv2
import mss
import numpy as np
from PIL import Image
from pytesseract import pytesseract

from app.utils import resource_path

pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')
EVERYTHING_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:-/() \\"\\'" """
NUMBERS_PERIODS_COMMAS_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789,.\""""
INTEGERS_ONLY_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789\""""
TEXT_ONLY_CONFIG = """--psm 6 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" """
DATE_ONLY_CONFIG = """--psm 6 -c tessedit_char_whitelist="0123456789,AMP:/ " """


def get_txt_from_im(name: str, config: str, cropped: np.array) -> str:
    data = pytesseract.image_to_data(cropped, output_type=pytesseract.Output.DICT, config=config)
    data["column_name"] = name
    return data


def parse_page_count(txt: str) -> Tuple[int, bool]:
    """Return value: tuple of (pages, validation_success)"""
    pages_str = txt['text'][-1]
    logging.debug(f"Number of pages looks like: {pages_str}")
    if not pages_str:
        logging.error("Could not find ANY page count information. Assuming 1.")
        return 500, False

    pages_str = pages_str.strip()

    if pages_str.isnumeric():
        if int(pages_str) > 500:
            # try see if the o was mistaken for a 0
            try:
                last_zero = pages_str[:-1].rindex("0")
            except ValueError:
                logging.error(f"Captured page count is greater than 500. Setting to max.")
                return 500, False
            pages_str = pages_str[last_zero + 1:]
            if not pages_str.isnumeric() or int(pages_str) > 500:
                logging.error(f"Captured page count is greater than 500. Setting to max.")
                return 500, False
        return int(pages_str), True

    groups = re.search(r"\s?o?f?\s?(\d*)", pages_str).groups()
    last = groups[-1]
    if not last.isnumeric():
        logging.error(f"Captured page count info is not numeric. Original capture: {pages_str}")
        return 500, False

    pages = int(last)
    if pages > 500:
        logging.error('Page count greater than 500 - assuming 1 page.')
        return 500, False

    return pages, True


def parse_current_page(txt: dict) -> Tuple[int, bool]:
    text_list = txt['text']
    # loop through conf scores and remove low scores
    for idx, val in reversed(list(enumerate(txt['conf']))):
        if val == '-1':
            text_list.pop(idx)

    text_string = ''.join(text_list)
    groups = re.search(r"\d+", text_string)
    if groups:
        try:
            int_found = groups[0]
            if int_found[0] == '9' and int(int_found) > 500:
                int_found = int_found[1:]
            if int(int_found) > 500:
                return 500, False
            else:
                return int(int_found)+1, True
        except IndexError:
            return 500, False
    else:
        return 500, False

def parse_server_name(txt: dict) -> str:
    text_list = txt['text']
    # loop through conf scores and remove low scores
    for idx, val in reversed(list(enumerate(txt['conf']))):
        if val == '-1':
            text_list.pop(idx)

    text_string = ''.join(text_list)
    return text_string

def pre_process_listings_image(img, scale=2.5):
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
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


def pre_process_page_count_image(img_arr):
    img = cv2.cvtColor(img_arr, cv2.COLOR_BGRA2RGB)
    width = int(img.shape[1] * 2.5)
    height = int(img.shape[0] * 2.5)
    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_BITS)

    lower_color = np.array([50, 55, 55])
    upper_color = np.array([150, 150, 125])

    mask = cv2.inRange(img, lower_color, upper_color)
    res = cv2.bitwise_and(img, img, mask=mask)
    img_gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    res = cv2.bilateralFilter(img_gray, 5, 50, 100)
    binary_img = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return np.invert(binary_img)

def pre_process_current_page_image(img_arr):
    img = cv2.cvtColor(img_arr, cv2.COLOR_BGRA2RGB)
    width = int(img.shape[1] * 2.5)
    height = int(img.shape[0] * 2.5)
    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_BITS)

    lower_color = np.array([75, 75, 85])
    upper_color = np.array([255, 255, 255])

    mask = cv2.inRange(img, lower_color, upper_color)
    res = cv2.bitwise_and(img, img, mask=mask)
    img_gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    res = cv2.bilateralFilter(img_gray, 5, 50, 100)
    # res = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return np.invert(res)

class Screenshot:
    def __init__(self, np_arr: np.ndarray) -> None:
        self.img_array = np_arr
        self.file_path = None

    def get_image(self, pil_high_quality: bool = False) -> Union[Image.Image, Any]:
        if pil_high_quality:
            return Image.fromarray(self.img_array)
        return self.img_array

    def save_image(self, file_path: str, pil_high_quality: bool = False) -> None:
        if self.file_path:
            return
        self.file_path = file_path
        if pil_high_quality:
            image = self.get_image(pil_high_quality)
            image.save(self.file_path)
        else:
            is_success, im_buf_arr = cv2.imencode(".png", self.img_array)
            im_buf_arr.tofile(file_path)
            # cv2.imwrite(file_path, self.img_array)


def screenshot_bbox(left: int, top: int, width: int, height: int, save_to: str = None) -> Screenshot:
    """Return a bbox as an RGB array. save_to has a high performance cost."""
    with mss.mss() as sct:
        sct_img = sct.grab({
            "top": top,
            "left": left,
            "width": width,
            "height": height
        })

        ss = Screenshot(np.asarray(sct_img))

    if save_to:
        ss.save_image(save_to)
    return ss


def capture_screen(save_to: str = None) -> Screenshot:
    """Return entire screen as an RGB array. save_to has a high performance cost."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]

        sct_img = sct.grab(monitor)
        ss = Screenshot(np.asarray(sct_img))

    if save_to:
        ss.save_image(save_to)

    return ss

def find_closest_match(input_str: str, list_to_compare: list):
    closest_distance = 99
    closest_match = None

    for candidate in list_to_compare:
        lev_distance = Levenshtein.distance(input_str, candidate)
        if lev_distance < closest_distance:
            closest_distance = lev_distance
            closest_match = candidate


    return closest_match, closest_distance

def find_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val['name'] == value:
            return key
    return None
