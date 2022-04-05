import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


class PriceSectionValidator:
    def __init__(self, listings: List[Dict[str, str]]) -> None:
        self.listings = listings
        self.last_good_price = Decimal("0.01")
        self.last_good_index = None
        self.impossible_tp_value = Decimal("500000.0")

    def item_at_index(self, at_index: int) -> dict:
        if at_index < 0:
            return {}
        return self.listings[at_index]

    def find_previous_price(self, cur_index: int) -> Tuple[int, Optional[Decimal]]:
        index = cur_index - 1
        while index >= 0:
            listing = self.item_at_index(index)
            price = listing.get("validated_price")
            if price is not None:
                return listing, price
            index -= 1
        return None, None

    def find_next_price(self, cur_index: int) -> Tuple[dict, Optional[Decimal]]:
        index = cur_index + 1
        while index < len(self.listings):
            listing = self.item_at_index(index)
            price = listing.get("validated_price")
            if price is not None:
                return listing, price
            index += 1
        return None, None

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
        return num >= Decimal("0.01")

    def test_vs_last_good_price(self, value: Decimal) -> bool:
        return value >= (self.last_good_price or Decimal("0.01"))

    def try_simple_validation(self, listing: dict) -> Optional[Decimal]:
        price = listing.get("price")
        if price is None:
            return None
        if self.check_is_price(price):
            return Decimal(listing["price"])
        original_price_str = listing["price"]
        if original_price_str:
            price_test = f"{original_price_str[:-2]}.{original_price_str[-2:]}".replace("..", ".")

            if self.check_is_price(price_test):
                return Decimal(price_test)
        return None

    def perform_simple_validation(self) -> None:
        """for each listing, simply check if we can assign it a validated value without looking at any other prices"""
        for listing in self.listings:
            price = self.try_simple_validation(listing)
            listing["validated_price"] = price

    def clean_prices_by_confidence_level(self) -> None:
        """
            for each listing, check that it is greater or equal in value than the previous valid listing.
            if not, check that the next price is greater than or equal to the previous price.
            if the previous price is less than or equal to the next price, the current listing is invalid.
            otherwise, consider the previous "valid" listing invalid.
        """
        rows_with_significant_diff = 0
        for idx, listing in enumerate(self.listings):
            cur_validated_price = listing["validated_price"]
            if cur_validated_price is None:
                continue

            confidence = listing["price_confidence"]
            prev_listing, prev_price = self.find_previous_price(idx)

            if prev_price is None:  # this must be the first item in the list with a valid price.
                continue

            more_confident_than_prev = confidence >= prev_listing["price_confidence"]
            is_greater_than_prev = cur_validated_price >= prev_price
            if is_greater_than_prev:
                continue  # looks good

            if more_confident_than_prev:
                prev_index = idx - 1
                comparison_listing = self.listings[prev_index]
                while prev_index >= 0 and comparison_listing.get("price_confidence", 0) < 95:
                    comparison_listing = self.listings[prev_index]
                    listing_validated_price = comparison_listing.get("validated_price") or self.impossible_tp_value
                    if listing_validated_price > cur_validated_price:  # noqa: E501
                        self.listings[prev_index]["validated_price"] = None
                        logging.debug(f"Deleted price on {self.listings[prev_index]['listing_id']}")
                    else:
                        break
                    prev_index -= 1
            else:
                logging.debug(f"NOT more confident than previous price - deleting this one. Listing {prev_listing['listing_id']} vs {listing['listing_id']}")
                listing["validated_price"] = None

    def try_find_close_matches(self) -> None:
        """Now, see if we can fill any None values by comparing neighbours."""
        for idx, listing in enumerate(self.listings):
            cur_validated_price = listing["validated_price"]
            if cur_validated_price is not None:
                continue  # there's just no way to know

            prev_listing, prev_price = self.find_previous_price(idx)
            next_listing, next_price = self.find_next_price(idx)

            if next_price == Decimal("0.01"):
                listing["validated_price"] = Decimal("0.01")

            if prev_price is None or next_price is None:
                continue  # there's just no way to know

            if abs(prev_price - next_price) <= Decimal("0.02"):
                middle = round((prev_price + next_price) / Decimal("2"), 2)
                listing_id = listing["listing_id"]
                logging.debug(f"{listing_id}: was close enough to {prev_price} and {next_price} to guess value as {middle}.")
                return middle

    def check_if_ordered(self) -> None:
        last_price = Decimal("0.01")
        for listing in self.listings:
            # logging.debug(json.dumps(listing, indent=2, default=str))
            price = listing["validated_price"]
            if price is None:
                continue
            if price < last_price:
                logging.debug(f"Still not ordered because of {listing['listing_id']}")
                return False
            last_price = price
        return True

    def validate_all(self) -> Dict[str, str]:
        self.perform_simple_validation()
        while not self.check_if_ordered():
            self.clean_prices_by_confidence_level()
        self.try_find_close_matches()
        validated = sum([1 for listing in self.listings if listing["validated_price"] is not None])
        validated_percent = round(validated / max(1, len(self.listings)) * 100, 1)
        logging.info(f"Price validation in section: {self.listings[0]['section']} = {validated_percent}%")
        return self.listings




