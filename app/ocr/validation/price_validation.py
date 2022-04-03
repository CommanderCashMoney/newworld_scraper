import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


class PriceSectionValidator:
    def __init__(self, listings: List[Dict[str, str]]) -> None:
        self.listings = listings
        self.last_good_price = Decimal("0.01")
        self.last_good_index = None

    def item_at_index(self, at_index: int) -> dict:
        prev_index = at_index - 1
        if prev_index < 0:
            return {}
        return self.listings[at_index]

    def find_previous_valid_price(self, cur_index: int) -> Tuple[int, Optional[Decimal]]:
        index = cur_index - 1
        while index >= 0:
            listing = self.item_at_index(index)
            price = listing.get("validated_price")
            if price is not None:
                return listing, price
            index -= 1
        return None, None

    def find_next_valid_price(self, cur_index: int) -> Tuple[dict, Optional[Decimal]]:
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
        return num > Decimal("0.01")

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

    def first_pass(self) -> None:
        """for each listing, simply check if we can assign it a validated value without looking at any other prices"""
        for listing in self.listings:
            price = self.try_simple_validation(listing)
            listing["validated_price"] = price

    def second_pass(self) -> None:
        """
            for each listing, check that it is greater or equal in value than the previous valid listing.
            if not, check that the next price is greater than or equal to the previous price.
            if the previous price is less than or equal to the next price, the current listing is invalid.
            otherwise, consider the previous "valid" listing invalid.
        """
        rows_with_significant_diff = 0
        for idx, listing in enumerate(self.listings):
            if listing["listing_id"] == '27a9e9b3-b334-11ec-82dc-e0d4e8754873':
                pass
            cur_validated_price = listing["validated_price"]
            if cur_validated_price is None:
                continue

            prev_listing, prev_price = self.find_previous_valid_price(idx)
            next_listing, next_price = self.find_next_valid_price(idx)

            if prev_price is None:  # this must be the first item in the list with a valid price.
                continue

            big_jump = max(prev_price, cur_validated_price) / min(prev_price, cur_validated_price) > 2

            if prev_price <= cur_validated_price and not big_jump:  # everything looks good!
                continue

            went_down = prev_price > cur_validated_price

            if went_down:
                listing["validated_price"] = None
            elif next_price is None or prev_price <= next_price:
                # if next price doesn't exist, or next price is greater than the previous one - looks like i'm invalid.
                listing["validated_price"] = None
            else:
                # otherwise.. looks like the previous price is invalid.
                prev_listing["validated_price"] = None

    def third_pass(self) -> None:
        """Now, see if we can fill any None values by comparing neighbours."""
        for idx, listing in enumerate(self.listings):
            cur_validated_price = listing["validated_price"]
            if cur_validated_price is not None:
                continue  # there's just no way to know

            prev_listing, prev_price = self.find_previous_valid_price(idx)
            next_listing, next_price = self.find_next_valid_price(idx)

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
        prev_listing = None
        for listing in self.listings:
            # logging.debug(json.dumps(listing, indent=2, default=str))
            price = listing["validated_price"]
            if price is None:
                continue
            if price < last_price:
                return False
            last_price = price
            prev_listing = listing
        return True

    def validate_all(self) -> Dict[str, str]:
        self.first_pass()
        while not self.check_if_ordered():
            self.second_pass()
        self.third_pass()
        self.check_if_ordered()
        validated = sum([1 for listing in self.listings if listing["validated_price"] is not None])
        validated_percent = validated / len(self.listings)
        print(f"percentage of validated listings in section {self.listings[0]['section']} {validated_percent}")

        return self.listings




