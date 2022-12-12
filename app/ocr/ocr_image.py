import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

from app.ocr.resolution_settings import get_resolution_obj
from app.ocr.utils import (
    EVERYTHING_CONFIG,
    INTEGERS_ONLY_CONFIG,
    NUMBERS_PERIODS_COMMAS_CONFIG,
    TEXT_ONLY_CONFIG,
    DATE_ONLY_CONFIG,
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
        return cv2.imdecode(np.fromfile(str(self.original_path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        # return cv2.imread(str(self.original_path))

    def parse_prices(self) -> defaultdict:
        """Parse prices from images, do no validation yet."""
        if self.section.find('Buy Order -') >= 0:
            columns = {
                "name": {
                    "config": EVERYTHING_CONFIG,
                    "coords": self.resolution.buy_order_tp_name_col_x_coords,
                },
                "price": {
                    "config": NUMBERS_PERIODS_COMMAS_CONFIG,
                    "coords": self.resolution.buy_order_tp_price_col_x_coords,
                },
                "qty": {
                    "config": INTEGERS_ONLY_CONFIG,
                    "coords": self.resolution.buy_order_tp_qty_col_x_coords,
                }
            }
        else:
            columns = {
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
        img_arr = pre_process_listings_image(self.original_image)
        img = Image.fromarray(img_arr)
        results.append([])
        broken_up_images = []
        # break the image up into columns for processing
        for name, values in columns.items():
            x_start, x_end = values["coords"]
            config = values["config"]
            img_cropped = img.crop((x_start * 2.5, 0, x_end * 2.5, img.height))
            broken_up_images.append((name, config, img_cropped))
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

    def parse_sold_item_prices(self) -> defaultdict:
        """Parse prices from images, do no validation yet."""
        columns = {
            "name": {
                "config": EVERYTHING_CONFIG,
                "coords": self.resolution.sold_order_tp_name_col_x_coords,
            },
            "price": {
                "config": NUMBERS_PERIODS_COMMAS_CONFIG,
                "coords": self.resolution.sold_order_tp_price_col_x_coords,
            },
            "qty": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": self.resolution.sold_order_qty_col_x_coords,
            },
            "sold": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": self.resolution.sold_order_sold_qty_col_x_coords,
            },
            "gs": {
                "config": INTEGERS_ONLY_CONFIG,
                "coords": self.resolution.sold_order_tp_gs_col_x_coords,
            },

            "status": {
                "config": TEXT_ONLY_CONFIG,
                "coords": self.resolution.sold_order_tp_status_col_x_coords,
            },
            "completion_time": {
                "config": DATE_ONLY_CONFIG,
                "coords": self.resolution.sold_order_tp_completion_time_col_x_coords,
            }
        }
        img_columns = {  # todo add image capture for these columns
            "gem": {
                "coords": self.resolution.sold_order_tp_gem_col_x_coords,
            },
            "perk": {
                "coords": self.resolution.sold_order_tp_perk_col_x_coords,
            },
        }
        results = []
        img_arr = pre_process_listings_image(self.original_image)
        img = Image.fromarray(img_arr)
        results.append([])
        broken_up_images = []
        # break the image up into columns for processing
        for name, values in columns.items():
            x_start, x_end = values["coords"]
            config = values["config"]
            img_cropped = img.crop((x_start * 2.5, 0, x_end * 2.5, img.height))
            broken_up_images.append((name, config, img_cropped))
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
