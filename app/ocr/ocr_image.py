import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.utils import (
    EVERYTHING_CONFIG,
    INTEGERS_ONLY_CONFIG,
    NUMBERS_PERIODS_COMMAS_CONFIG,
    get_txt_from_im,
    pre_process_listings_image
)


class OCRImage:
    def __init__(self, img_src: Path, section: str) -> None:
        self.original_path = img_src
        self.section = section
        path = Path(img_src)
        self.original_path_obj = path
        self.captured = datetime.fromtimestamp(path.stat().st_mtime)
        self.resolution = get_resolution_obj()

    @property
    def original_image(self):
        im = cv2.imread(str(self.original_path))
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    def parse_prices(self) -> defaultdict:
        """Parse prices from images, do no validation yet."""
        columns = {
            "name": {
                "config": EVERYTHING_CONFIG,
                "coords": self.resolution.tp_name_col_x_coords,
                "masks": [
                    [[110, 110, 110], [255, 255, 255]],
                ]
            },
            "price": {
                "config": NUMBERS_PERIODS_COMMAS_CONFIG,
                "coords": self.resolution.tp_price_col_x_coords,
                "masks": [
                    [[90, 45, 45], [255, 150, 150]],  # red
                ]
            },
            "avail": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": self.resolution.tp_avail_col_x_coords,
                "masks": [
                    [[25, 25, 30], [150, 150, 150]],
                ]
            }
        }
        results = []
        img = Image.fromarray(self.original_image)
        # img_arr = pre_process_listings_image(self.original_image)
        # img = Image.fromarray(img_arr)
        results.append([])
        broken_up_images = []
        # break the image up into columns for processing
        for name, values in columns.items():
            x_start, x_end = values["coords"]
            config = values["config"]
            masks = values["masks"]
            img_cropped = img.crop((x_start, 0, x_end, img.height))
            broken_up_images.append((name, config, np.array(img_cropped), masks))
        # concurrently execute pytesseract
        with ThreadPoolExecutor(max_workers=len(columns)) as executor:
            futures = executor.map(lambda arr: get_txt_from_im(*arr), broken_up_images)
            results[-1] = futures

        # now process the results
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
                        row_data[current_row][f"price_confidence"] = float(conf)
                    # if data already exists for this column name, add a space.
                    append = " " if row_data[current_row][column_name] else ""
                    row_data[current_row][column_name] += f"{append}{text}"

            # should do a check here that all the important keys exist
            final_data.extend([{**values, **{
                "listing_id": f"{self.original_path_obj.name} (idx: {index})",
                "timestamp": self.captured,
                "filename": self.original_path_obj,
                "valid": None,
                "section": self.section
            }} for index, values in enumerate(row_data.values())])

        return final_data
