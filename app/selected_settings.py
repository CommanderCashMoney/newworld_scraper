import logging

from pydantic import BaseModel

from app.settings import SETTINGS


class SelectedSettings(BaseModel):
    username: str = SETTINGS.api_username
    password: str = SETTINGS.api_password
    pages: int = 500
    server_id: str = None
    test_run: bool = True
    auto_sections: bool = True  # doesn't do anything atm
    access_token: str = ""
    refresh_token: str = ""


SELECTED_SETTINGS = SelectedSettings()


def update_pages(value: str) -> None:
    if not value.isnumeric():
        value = 500
    logging.info(f"Updated setting `pages` to {value}")
    SELECTED_SETTINGS.pages = int(value)


def update_username(value: str) -> None:
    SELECTED_SETTINGS.username = value
    logging.info(f"Username updated.")


def update_password(value: str) -> None:
    SELECTED_SETTINGS.password = value
    logging.info(f"Password updated.")


def update_test_run(value: bool) -> None:
    SELECTED_SETTINGS.test_run = value
    logging.info(f"Test run is now {value}.")


def update_auto_sections(value: bool) -> None:
    SELECTED_SETTINGS.auto_sections = value
    logging.info(f"Auto sections is now {value}.")


def update_server_select(value: str) -> None:
    SELECTED_SETTINGS.server_id = value
    logging.info(f"Server is now {value}.")
