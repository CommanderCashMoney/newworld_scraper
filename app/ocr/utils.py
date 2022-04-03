import cv2
import mss
import numpy as np
from PIL import Image
from pytesseract import pytesseract

from app.utils import resource_path

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
