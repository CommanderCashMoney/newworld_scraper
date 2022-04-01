from copy import deepcopy
from typing import DefaultDict, List

from app import events
from app.api import submit_bad_names, submit_price_data


class APISubmission:
    def __init__(self, price_data: List[dict], bad_name_data: DefaultDict[str, int]) -> None:
        self.price_data = price_data
        self.bad_name_data = bad_name_data
        self.price_data_archive = deepcopy(price_data)

    def submit(self):
        from app.overlay.overlay_updates import OverlayUpdateHandler
        if submit_bad_names(self.bad_name_data):
            self.bad_name_data.clear()
        if submit_price_data(self.price_data):
            self.price_data.clear()
        if not self.submit_success:
            OverlayUpdateHandler.visible(events.RESEND_DATA, visible=True)
        OverlayUpdateHandler.visible("-SCAN-DATA-COLUMN-", visible=True)

    @property
    def submit_success(self) -> bool:
        return len(self.bad_name_data) == 0 and len(self.price_data) == 0


