import decimal
import logging
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List
from urllib.parse import urljoin

import requests

from app.settings import SETTINGS


class PriceValidator:
    def __init__(self, price_list: List) -> None:
        self.price_list = price_list
        self.bad_indexes = set()
        self.current_index = 0
        self.api_fetched = False
        self.confirmed_names = None
        self.name_swaps = None
        self.bad_names = defaultdict(int)
        self.word_cleanup = None

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

    @staticmethod
    def check_is_price(price_test) -> bool:
        # note, we already know that it is either None or Numeric because of the OCR rules
        if price_test is None or price_test.replace(".", "").lstrip("0") == "":
            return False
        if "." not in price_test:
            return False  # could check if inserting a . makes it sensible
        try:
            Decimal(price_test)
        except:  # noqa
            return False
        return True

    def validate_price(self) -> bool:
        price = self.price_list[self.current_index].get("price")
        if self.check_is_price(price):
            return price
        prev_price = self.prev_item().get("price")
        next_price = self.next_item().get("price")
        if not price and (prev_price is None or next_price is None):
            return False  # not enough to compare to

        # check that the prev and next price are close enough that we can determine the price of this
        if not price:
            try:
                prev_price_dec = Decimal(prev_price)
                next_price_dec = Decimal(next_price)
                if abs(prev_price_dec - next_price_dec) <= Decimal("0.02"):
                    middle = round(prev_price_dec + (prev_price_dec - next_price_dec) / 2, 2)
                    self.price_list[self.current_index]["price"] = str(middle)
                    return True
            except (ValueError, decimal.InvalidOperation):
                pass
            return False

        if len(price) < 3:
            return False

        # try inserting a decimal place and see if we have a match to before/after
        price_test = f"{price[:-2]}.{price[-2:]}"
        prev_price_is_valid = self.current_index - 1 not in self.bad_indexes
        matches_next = lambda: next_price is not None and price_test == next_price  # noqa
        matches_prev = lambda: price_test == prev_price and prev_price_is_valid  # noqa
        # lazy load
        if matches_next() or matches_prev():
            self.price_list[self.current_index]["price"] = price_test
            return True
        # check if the test falls between the two values
        try:
            price_test_float = float(price_test)
            if float(next_price or price_test) >= price_test_float >= float(prev_price or price_test):
                self.price_list[self.current_index]["price"] = price_test
                return True
        except ValueError:
            return False
        # check that the test is sufficiently close to its valid neighbour
        if prev_price_is_valid:
            last_price_float = float(prev_price)
            cur_price_float = price_test_float
            percent_diff = (cur_price_float / last_price_float) - 1
            # eg: 0.02 vs 0.1 is ok, 500% diff is not
            return (
                cur_price_float > last_price_float
                and (cur_price_float - last_price_float < 0.09 or percent_diff < 5)  # 20% diff max
            )

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
            name_invalid = not self.validate_name()
            price_invalid = not self.validate_price()
            qty_invalid = not self.validate_quantity()

            if name_invalid or price_invalid or qty_invalid:
                logging.debug(f"Could not validate {self.price_list[self.current_index]}")
                self.bad_indexes.add(self.current_index)
            self.current_index += 1
