import json
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from app import events
from app.ocr.api_submission_data import APISubmission
from app.settings import SETTINGS


class CurrentData(BaseModel):
    """Data that persists throughout the session, does not save between instances"""
    username: str = SETTINGS.api_username
    password: str = SETTINGS.api_password
    pages: int = 1 if SETTINGS.is_dev else 500
    server_id: str = None
    test_run: bool = True
    auto_sections: bool = True  # doesn't do anything atm
    advanced_user: bool = False
    access_token: str = ""
    refresh_token: str = ""

    current_run_id: str = datetime.now().strftime("%Y%m%d-%H%M%S")
    crawler: "Crawler" = None
    pending_submission_data: APISubmission = None
    last_scan_data: APISubmission = None

    class Config:
        arbitrary_types_allowed = True

    def submit_pending_submission_data(self) -> None:
        from app.overlay.overlay_updates import OverlayUpdateHandler
        self.pending_submission_data.submit()
        if self.pending_submission_data.submit_success:
            self.pending_submission_data = None
        OverlayUpdateHandler.visible(events.RESEND_DATA, visible=self.pending_submission_data is None)

    def save_last_scan_data(self, store_in: Path) -> None:
        if self.last_scan_data is None:
            logging.error("Trying to save last scan data, but it's not available")  # should never happen
        store_file_path = store_in / datetime.now().strftime("%Y%m%d_%H%M%S.json")
        with store_file_path.open("w") as out_f:
            json.dump(self.last_scan_data.price_data_archive, out_f, default=str)
        logging.info(f"Data saved to `{store_file_path}`")

    def update_run_id(self) -> None:
        self.current_run_id = datetime.now().strftime("%Y%m%d-%H%M%S")


SESSION_DATA = CurrentData()


def update_pages(value: str) -> None:
    if not value.isnumeric():
        value = 500
    logging.debug(f"Updated setting `pages` to {value}")
    SESSION_DATA.pages = int(value)


def update_username(value: str) -> None:
    SESSION_DATA.username = value
    logging.debug(f"Username updated.")


def update_password(value: str) -> None:
    SESSION_DATA.password = value
    logging.debug(f"Password updated.")


def update_test_run(value: bool) -> None:
    SESSION_DATA.test_run = value
    logging.debug(f"Test run is now {value}.")


def update_auto_sections(value: bool) -> None:
    SESSION_DATA.auto_sections = value
    logging.debug(f"Auto sections is now {value}.")


def update_server_select(value: str) -> None:
    SESSION_DATA.server_id = value
    logging.debug(f"Server is now {value}.")


def save_scan_data(value) -> None:
    SESSION_DATA.save_last_scan_data(Path(value))
