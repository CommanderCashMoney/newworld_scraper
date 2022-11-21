import logging
from copy import deepcopy
from decimal import Decimal
from typing import DefaultDict, List

from app import events
from app import api


class APISubmission:
    def __init__(self, price_data: List[dict], bad_name_data: DefaultDict[str, int], resolution: str, price_accuracy: Decimal, name_accuracy: Decimal) -> None:
        self.price_data = price_data
        self.bad_name_data = bad_name_data
        self.price_data_archive = deepcopy(price_data)
        self.resolution = resolution
        self.price_accuracy = price_accuracy
        self.name_accuracy = name_accuracy

    def submit(self):
        from app.overlay.overlay_updates import OverlayUpdateHandler
        OverlayUpdateHandler.update('status_bar', "Submitting data to API")
        if api.submit_bad_names(self.bad_name_data):
            self.bad_name_data.clear()
        try:
            api.submit_price_data(self.price_data, self.resolution, self.price_accuracy, self.name_accuracy):
            self.price_data.clear()
        except api.APISubmitError as error:
            logging.exception(error)
            OverlayUpdateHandler.update(
                "status_bar",
                "Price submission error. Please wait a few minutes and check #scan_notifications",
            )
        OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", visible=True)
        OverlayUpdateHandler.visible(events.CHANGE_KEY_BINDS, visible=True)

    @property
    def submit_success(self) -> bool:
        return len(self.bad_name_data) == 0 and len(self.price_data) == 0


