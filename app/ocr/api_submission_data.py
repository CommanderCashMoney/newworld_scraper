from typing import DefaultDict, List

from app.api import submit_bad_names, submit_price_data


class APISubmission:
    def __init__(self, price_data: List[dict], bad_name_data: DefaultDict[str, int]) -> None:
        self.price_data = price_data
        self.bad_name_data = bad_name_data

    def submit(self):
        if submit_bad_names(self.bad_name_data):
            self.bad_name_data.clear()
        if submit_price_data(self.price_data):
            self.price_data.clear()

    @property
    def submit_success(self) -> bool:
        return len(self.bad_name_data) == 0 and len(self.price_data) == 0


