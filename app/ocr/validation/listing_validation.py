import decimal
import json
import logging
from collections import defaultdict
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urljoin

import requests

from app.ocr.validation.price_validation import PriceSectionValidator
from app.settings import SETTINGS


class ListingValidator:
    def __init__(self) -> None:
        self.price_list = []
        self.bad_indexes = set()
        self.current_index = 0
        self.api_fetched = False
        self.confirmed_names = None
        self.name_swaps = None
        self.bad_names = defaultdict(int)
        self.word_cleanup = None
        self.image_accuracy = defaultdict(lambda: defaultdict(int))  # dict of image file name: image accuracy
        self.last_good_price: Optional[Decimal] = None
        self.field_accuracy = defaultdict(int)

    def empty(self):
        self.price_list.clear()
        self.bad_indexes = set()
        self.current_index = 0
        self.bad_names = defaultdict(int)
        self.image_accuracy = defaultdict(lambda: defaultdict(int))  # dict of image file name: image accuracy
        self.last_good_price: Optional[Decimal] = None
        self.field_accuracy = defaultdict(int)

    def percentage_or_none(self, numerator: float, denominator: float) -> Optional[float]:
        try:
            return numerator / denominator
        except ZeroDivisionError:
            pass
        return None

    @property
    def name_accuracy(self) -> float:
        return self.percentage_or_none(self.field_accuracy["name"], len(self.price_list))

    @property
    def price_accuracy(self) -> float:
        return self.percentage_or_none(self.field_accuracy["price"], len(self.price_list))

    @property
    def quantity_accuracy(self) -> float:
        return 1.0

    @property
    def overall_accuracy(self) -> float:
        return self.percentage_or_none(len(self.bad_indexes), len(self.price_list))

    def set_api_info(self) -> None:
        if self.api_fetched:
            return
        url = urljoin(SETTINGS.base_web_url, "api/confirmed_names/")
        self.confirmed_names = requests.get(url).json()
        url = urljoin(SETTINGS.base_web_url, "api/get_mapping_corrections/")
        self.name_swaps = requests.get(url).json()
        url = urljoin(SETTINGS.base_web_url, "api/word-cleanup/")
        self.word_cleanup = requests.get(url).json()
        self.api_fetched = True

    @property
    def current_listing_obj(self) -> dict:
        return self.price_list[self.current_index]

    def get_valid_price(self, psv: PriceSectionValidator, price_index_offset: int) -> Optional[Decimal]:
        return psv.listings[self.current_index - price_index_offset].get("validated_price")

    def validate_quantity(self) -> bool:
        qty = self.price_list[self.current_index].get("avail", "1")
        self.price_list[self.current_index]["avail"] = qty
        if qty.isnumeric():
            if int(qty) > 10000:
                return False

        return qty.isnumeric()

    def validate_name(self) -> bool:
        validated_name_key = "validated_name"
        cur_obj = self.price_list[self.current_index]
        name = cur_obj.get("name")
        if name is None or name == "":
            cur_obj[validated_name_key] = None
            return None

        # replace commonly incorrect words
        name_parts = name.split(" ")
        for idx, word in enumerate(name_parts):
            cleaned_word = self.word_cleanup.get(word)
            if cleaned_word:
                name_parts[idx] = cleaned_word
        name = " ".join(name_parts)

        # first check if there's a name swap
        name_swap = self.name_swaps.get(name)
        if name_swap:
            copy = dict(name_swap)
            swapped_name = copy.pop("name")
            copy[validated_name_key] = swapped_name
            logging.debug(f"Swapped name of {name} for {swapped_name}")
            cur_obj.update(copy)
            return True

        if name in self.confirmed_names:
            copy = dict(self.confirmed_names[name])
            swapped_name = copy.pop("name")
            copy[validated_name_key] = swapped_name
            self.price_list[self.current_index].update(copy)
            return True

        self.bad_names[name] += 1
        return False

    def validate_section(self, price_list: List[dict]) -> None:
        self.set_api_info()
        self.last_good_price = None
        self.price_list.extend(price_list)
        price_index_offset = self.current_index
        psv = PriceSectionValidator(price_list)
        psv.validate_all()

        while self.current_index < len(self.price_list):
            current_price = self.price_list[self.current_index]
            # validations
            validated_price = self.get_valid_price(psv, price_index_offset)
            price_invalid = validated_price is None
            name_invalid = not self.validate_name()
            quantity_invalid = not self.validate_quantity()  # can never be non valid

            current_price["validated_price"] = validated_price
            filename = current_price["filename"].name

            invalid = name_invalid or price_invalid or quantity_invalid
            current_price["valid"] = not invalid
            if invalid:
                # logging.debug(f"Could not validate {json.dumps(current_price, indent=2, default=str)}")
                self.bad_indexes.add(self.current_index)
                self.image_accuracy[filename]["bad_rows"] += 1

            self.current_index += 1

            # accuracy related stuff
            self.field_accuracy["name"] += 0 if name_invalid else 1
            self.field_accuracy["price"] += 0 if price_invalid else 1
            self.image_accuracy[filename]["processed"] += 1
            processed = self.image_accuracy[filename]["processed"]
            bad_rows = self.image_accuracy[filename]["bad_rows"]
            self.image_accuracy[filename]["bad_percent"] = bad_rows / processed * 100
