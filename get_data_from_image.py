import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from PIL.Image import Image
from PIL.PngImagePlugin import PngImageFile
from pytesseract import pytesseract

from ocr_image import process_image as pre_process_image


def get_txt_from_im(name: str, cropped: np.array) -> str:
    custom_config = """--psm 6 -c tessedit_char_whitelist="0123456789,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:- \\"\\'" """
    data = pytesseract.image_to_data(cropped, output_type=pytesseract.Output.DICT, config=custom_config)
    data["column_name"] = name
    return data


def get_all_items_from_image(img: PngImageFile):
    columns_1440p = {
        "name": [0, 360],     # name
        "price": [361, 550],   # price
        # "tier": [551, 630],   # tier - we don't even send this
        # "gs": [631, 712],   # gs - useless right now
        # "gem": [712, 802],   # gem - useless?
        # "perk": [],           # perk.. is image, useless
        # "rarity": [957, 1079],  # rarity - in current state, can't get this as the color gets completely filtered out
        "avail": [1080, 1165],  # qty
        # [1164, 1255], # owned
        # [1254, 1342],  # time
        # "location": [1342, img.width]  # location
    }
    results = []
    cv2_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img_arr = pre_process_image(cv2_img)
    img = Image.fromarray(img_arr)
    results.append([])
    broken_up_images = []
    # break the image up into columns for processing
    for name, (x_start, x_end) in columns_1440p.items():
        img_cropped = img.crop((x_start*2.5, 0, x_end*2.5, img.height * 2.5))
        broken_up_images.append((name, img_cropped))
    # concurrently execute pytesseract
    with ThreadPoolExecutor(max_workers=len(columns_1440p)) as executor:
        futures = executor.map(lambda arr: get_txt_from_im(*arr), broken_up_images)
        results[-1] = futures

    # now process the results
    # in 1440p, the row height is roughly 256px
    row_height = 256
    for result in results:
        final_data = []
        row_data = defaultdict(lambda: defaultdict(str))
        for col_data in result:
            column_name = col_data["column_name"]
            for top, conf, text in zip(col_data["top"], col_data["conf"], col_data["text"]):
                if conf == "-1":
                    continue
                current_row = int(top / row_height)
                # if data already exists for this column name, add a space.
                append = " " if row_data[current_row][column_name] else ""
                row_data[current_row][column_name] += f"{append}{text}"

        # should do a check here that all the important keys exist
        final_data.append(row_data)

    print(json.dumps(row_data, indent=2))

    return row_data
