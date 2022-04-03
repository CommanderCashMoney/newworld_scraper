import decimal
import json
import logging
from collections import defaultdict
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urljoin

import requests

from app.settings import SETTINGS


class ListingValidator:
    def __init__(self, price_list: List) -> None:
        self.price_list = price_list
        self.bad_indexes = set()
        self.current_index = 0
        self.api_fetched = False
        self.confirmed_names = None
        self.name_swaps = None
        self.bad_names = defaultdict(int)
        self.word_cleanup = None
        self.image_accuracy = defaultdict(lambda: defaultdict(int))  # dict of image file name: image accuracy
        self.last_good_price: Optional[Decimal] = None

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

    def prev_item(self) -> dict:
        prev_index = self.current_index - 1
        if prev_index < 0:
            return {}
        return self.price_list[prev_index]

    def next_item(self) -> dict:
        next_index = self.current_index + 1
        if next_index >= len(self.price_list):
            return {}
        return self.price_list[next_index]

    def check_is_price(self, price_test) -> bool:
        # note, we already know that it is either None or Numeric because of the OCR rules
        if price_test is None or price_test.replace(".", "").lstrip("0") == "":
            return False
        if "." not in price_test:
            return False  # could check if inserting a . makes it sensible
        try:
            num = round(Decimal(price_test), 2)
        except:  # noqa
            return False
        return num >= (self.last_good_price or Decimal("0.01"))

    def validate_price(self) -> bool:
        original_price_str = self.price_list[self.current_index].get("price")
        if self.check_is_price(original_price_str):
            self.last_good_price = Decimal(original_price_str)
            return True
        logging.debug(f"{original_price_str} wasn't a valid price, trying stuff - last good price is {self.last_good_price}...")  # noqa: E501
        prev_price = self.prev_item().get("price")
        next_price = self.next_item().get("price")
        if not original_price_str and (prev_price is None or next_price is None):
            return False  # not enough to compare to

        # check that the prev and next price are close enough that we can determine the price of this
        if not original_price_str:
            try:
                prev_price_dec = Decimal(prev_price)
                next_price_dec = Decimal(next_price)
                if abs(prev_price_dec - next_price_dec) <= Decimal("0.02"):
                    middle = round(prev_price_dec + (prev_price_dec - next_price_dec) / 2, 2)
                    self.price_list[self.current_index]["price"] = str(middle)
                    logging.debug(f"{original_price_str} was close enough to {prev_price_dec} and {next_price_dec} to guess value.")  # noqa: E501
                    return True
            except (ValueError, decimal.InvalidOperation):
                pass
            return False

        if len(original_price_str) < 3:
            return False

        # try inserting a decimal place and see if we have a match to before/after
        price_test = f"{original_price_str[:-2]}.{original_price_str[-2:]}".replace("..", ".")
        prev_price_is_valid = self.current_index - 1 not in self.bad_indexes
        # lazy load
        matches_next = lambda: next_price is not None and price_test == next_price  # noqa
        matches_prev = lambda: price_test == prev_price and prev_price_is_valid  # noqa
        if (matches_next() or matches_prev()) and Decimal(price_test) >= self.last_good_price:
            logging.debug(f"{original_price_str} matches a neighbour - one of: {next_price}, {prev_price}.")
            self.price_list[self.current_index]["price"] = price_test
            self.last_good_price = Decimal(price_test)
            return True
        # check if the test falls between the two values
        try:
            price_test_dec = Decimal(price_test)
            if Decimal(next_price or price_test) >= price_test_dec >= Decimal(prev_price or price_test):
                self.price_list[self.current_index]["price"] = price_test
                price = Decimal(price_test)
                if price >= self.last_good_price:
                    logging.debug(f"{original_price_str} was manipulated to {price_test} and it seems valid.")
                    self.last_good_price = price
                    return True
        except (ValueError, decimal.InvalidOperation):
            return False
        # check that the test is sufficiently close to its valid neighbour
        if self.last_good_price is not None:
            cur_price_dec = price_test_dec
            try:
                percent_diff = (cur_price_dec / self.last_good_price) - 1
            except ZeroDivisionError:
                last_price_json = json.dumps(self.price_list[self.current_index-1], indent=2)
                logging.error(f"Encountered zero division error on prev price: {last_price_json}")
                return False
            # eg: 0.02 vs 0.1 is ok, 500% diff is not
            is_ok = (
                cur_price_dec > self.last_good_price
                and (cur_price_dec - self.last_good_price < 0.09 or percent_diff < 5)  # 20% diff max
            )
            if is_ok:
                self.last_good_price = cur_price_dec
            return is_ok

        return False

    def validate_quantity(self) -> bool:
        qty = self.price_list[self.current_index].get("avail", "1")
        self.price_list[self.current_index]["avail"] = qty
        return qty.isnumeric()

    def validate_name(self) -> bool:
        name = self.price_list[self.current_index].get("name")
        if name is None or name == "":
            return False

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
            logging.debug(f"Swapped name of {name} for {name_swap['name']}")
            self.price_list[self.current_index].update(name_swap)
            return True

        if name in self.confirmed_names:
            self.price_list[self.current_index].update(self.confirmed_names[name])
            return True

        self.bad_names[name] += 1
        return False

    def validate_next_batch(self) -> None:
        self.set_api_info()

        while self.current_index < len(self.price_list):
            current_price = self.price_list[self.current_index]
            name_invalid = not self.validate_name()
            price_invalid = not self.validate_price()
            qty_invalid = not self.validate_quantity()
            filename = current_price["filename"].name
            self.image_accuracy[filename]["processed"] += 1
            invalid = name_invalid or price_invalid or qty_invalid
            current_price["valid"] = not invalid
            if invalid:
                logging.debug(f"Could not validate {json.dumps(current_price, indent=2, default=str)}")
                self.bad_indexes.add(self.current_index)
                self.image_accuracy[filename]["bad_rows"] += 1
            processed = self.image_accuracy[filename]["processed"]
            bad_rows = self.image_accuracy[filename]["bad_rows"]
            self.image_accuracy[filename]["bad_percent"] = bad_rows / processed * 100
            self.current_index += 1
