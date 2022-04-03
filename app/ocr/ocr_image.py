from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import cv2
from PIL import Image

from app.ocr.resolution_settings import res_1440p
from app.ocr.utils import (
    EVERYTHING_CONFIG,
    INTEGERS_ONLY_CONFIG,
    NUMBERS_PERIODS_COMMAS_CONFIG,
    get_txt_from_im,
    pre_process_image
)


class OCRImage:
    def __init__(self, img_src: Path) -> None:
        self.original_path = img_src
        path = Path(img_src)
        self.original_path_obj = path
        self.captured = datetime.fromtimestamp(path.stat().st_mtime)
        self.resolution = res_1440p

    @property
    def original_image(self):
        return cv2.imread(str(self.original_path))

    def parse_prices(self) -> defaultdict:
        """Parse prices from images, do no validation yet."""
        columns_1440p = {
            "name": {
                "config": EVERYTHING_CONFIG,
                "coords": self.resolution.tp_name_col_x_coords,
            },
            "price": {
                "config": NUMBERS_PERIODS_COMMAS_CONFIG,
                "coords": self.resolution.tp_price_col_x_coords,
            },
            "avail": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": self.resolution.tp_avail_col_x_coords,
            }
        }
        results = []
        # cv2_img = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2BGR)
        img_arr = pre_process_image(self.original_image)
        img = Image.fromarray(img_arr)
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
        final_data = []
        for result in results:
            row_data = defaultdict(lambda: defaultdict(str))
            for col_data in result:
                column_name = col_data["column_name"]
                for top, conf, text in zip(col_data["top"], col_data["conf"], col_data["text"]):
                    current_row = int(top / self.resolution.tp_row_height)
                    if conf == "-1":
                        continue
                    if column_name == "price":
                        text = text.replace(",", "").strip()
                    # if data already exists for this column name, add a space.
                    append = " " if row_data[current_row][column_name] else ""
                    row_data[current_row][column_name] += f"{append}{text}"

            # should do a check here that all the important keys exist
            final_data.extend([{**values, **{
                "timestamp": self.captured,
                "filename": self.original_path_obj,
            }} for values in row_data.values()])

        return final_data
