import time

import cv2
import mss
import numpy as np
from pytesseract import pytesseract

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


def look_for_cancel_or_refresh():
    reference_aoi = (961, 1032, 90, 30)
    reference_grab = grab_screen(region=reference_aoi)
    reference_image_file = resource_path('app/images/new_world/cancel_btn.png')
    reference_img = cv2.imread(reference_image_file)
    res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.95:
        loc = (max_loc[0] + 961), (max_loc[1] + 1032)
        print('clicked cancel')
        click('left', loc)
        time.sleep(0.5)

    reference_aoi = (1543, 900, 170, 40)
    reference_grab = grab_screen(region=reference_aoi)
    reference_image_file = resource_path('app/images/new_world/refresh_btn.png')
    reference_img = cv2.imread(reference_image_file)
    res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val > 0.95:
        loc = (max_loc[0] + 961), (max_loc[1] + 1032)
        click('left', loc)
        time.sleep(0.1)


def look_for_tp() -> bool:
    for x in range(2):
        bring_new_world_to_foreground()
        mouse.position = (1300, 480)
        time.sleep(0.1)
        look_for_cancel_or_refresh()
        reference_aoi = (450, 32, 165, 64)
        reference_grab = grab_screen(region=reference_aoi)
        reference_image_file = resource_path('app/images/new_world/trading_post_label.png')
        reference_img = cv2.imread(reference_image_file)
        res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.92:
            return True
        else:
            time.sleep(1)

    return False
