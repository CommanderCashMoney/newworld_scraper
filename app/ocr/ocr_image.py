import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
from PIL import Image

from app.ocr.utils import (
    EVERYTHING_CONFIG,
    INTEGERS_ONLY_CONFIG,
    NUMBERS_PERIODS_COMMAS_CONFIG,
    get_txt_from_im,
    pre_process_image
)


# todo: move this somewhere on initialise
from app.overlay.overlay_updates import OverlayUpdateHandler


class OCRImage:
    def __init__(self, img_src: Path) -> None:
        self.original_path = img_src
        self.original_image = cv2.imread(str(img_src))
        self.price_data: defaultdict = None
        self.errors = 0

    def parse_prices(self) -> defaultdict:
        # todo: move me to resolution
        columns_1440p = {
            "name": {
                "config": EVERYTHING_CONFIG,
                "coords": [0, 380],  # name
            },
            "price": {
                "config": NUMBERS_PERIODS_COMMAS_CONFIG,
                "coords": [380, 550],  # price
            },
            "avail": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": [1080, 1165],  # qty
            }
            # "tier": [551, 630],   # tier - we don't even send this
            # "gs": [631, 712],   # gs - useless right now
            # "gem": [712, 802],   # gem - useless?
            # "perk": [],           # perk.. is image, useless
            # "rarity": [957, 1079],  # rarity - in current state, can't get this as the color gets completely filtered out
            # [1164, 1255], # owned
            # [1254, 1342],  # time
            # "location": [1342, img.width]  # location
        }
        results = []
        cv2_img = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2BGR)
        img_arr = pre_process_image(cv2_img)
        img = Image.fromarray(img_arr)
        # if fn == "temp\img-1022.png":
        #     img.show()
        results.append([])
        broken_up_images = []
        # break the image up into columns for processing
        for name, values in columns_1440p.items():
            x_start, x_end = values["coords"]
            config = values["config"]
            img_cropped = img.crop((x_start * 2.5, 0, x_end * 2.5, img.height * 2.5))
            broken_up_images.append((name, config, img_cropped))
        # concurrently execute pytesseract
        with ThreadPoolExecutor(max_workers=len(columns_1440p)) as executor:
            futures = executor.map(lambda arr: get_txt_from_im(*arr), broken_up_images)
            results[-1] = futures

        # now process the results
        # in 1440p, the row height is roughly 256px
        row_height = 256
        final_data = []
        for result in results:
            row_data = defaultdict(lambda: defaultdict(str))
            for col_data in result:
                column_name = col_data["column_name"]
                for top, conf, text in zip(col_data["top"], col_data["conf"], col_data["text"]):
                    current_row = int(top / row_height)
                    if conf == "-1":
                        continue
                    # if data already exists for this column name, add a space.
                    append = " " if row_data[current_row][column_name] else ""
                    row_data[current_row][column_name] += f"{append}{text}"

            # should do a check here that all the important keys exist
            final_data.extend([values for values in row_data.values()])

        for _, item in row_data.items():
            if "price" not in item or "avail" not in item or "name" not in item or "." not in item["price"]:
                self.errors += 1

        self.price_data = row_data
        return final_data
