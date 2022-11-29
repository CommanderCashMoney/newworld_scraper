import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Dict

from pydantic import BaseSettings, Field, root_validator

from app.utils.resolution import get_default_resolution_key

APP_DATA_FOLDER = Path(os.getenv("APPDATA")) / "Cash Money Development" / "Trading Post Scraper"
SETTINGS_FILE_LOC = APP_DATA_FOLDER / "keybind_settings.json"


class Environment(Enum):
    prod = "prod"
    dev = "dev"


class KeyBindings(BaseSettings):
    action_key: str = "e"
    forward_key: str = "w"
    backward_key: str = "s"
    cancel_key: str = "/"


class Settings(BaseSettings):
    VERSION = "1.3.5"

    environment: Environment = Environment.prod
    use_dev_colors: bool = False
    console_logging_level: str = "INFO"

    nwmp_dev_api_host: str = "http://localhost:8080/"
    nwmp_prod_api_host: str = "https://nwmarketprices.com/"
    # user/pass can be set for development purposes in .env to avoid having to type each time
    api_username: str = ""
    api_password: str = ""
    resolution: str = Field(default_factory=get_default_resolution_key)
    disable_afk_timer = False

    log_file: str = "logging.txt"

    keybindings: KeyBindings

    def app_data_sub_path(self, relative_path: str, is_dir=True) -> Path:
        folder = APP_DATA_FOLDER / relative_path
        if is_dir:
            folder.mkdir(parents=True, exist_ok=True)
        return folder

    @property
    def temp_app_data(self) -> Path:
        return self.app_data_sub_path("temp")

    @property
    def is_dev(self) -> bool:
        return self.environment == Environment.dev

    @property
    def afk_timer(self) -> int:
        if self.disable_afk_timer:
            return None
        return 7 * 60

    @property
    def base_web_url(self) -> str:
        return self.nwmp_dev_api_host if self.is_dev else self.nwmp_prod_api_host

    @root_validator(pre=True)
    def validate(cls, values) -> Dict:  # noqa
        APP_DATA_FOLDER.mkdir(exist_ok=True)
        if "keybindings" not in values:
            values["keybindings"] = KeyBindings()
        return values

    class Config:
        env_file = ".env"


def load_settings() -> Settings:
    try:
        with SETTINGS_FILE_LOC.open() as f:
            settings_values = json.load(f)
            username = settings_values.pop("un", "")
            resolution = settings_values.pop("resolution", get_default_resolution_key())
            keybinds = KeyBindings(**settings_values)
            return Settings(api_username=username, resolution=resolution, keybindings=keybinds)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return Settings()


SETTINGS = load_settings()


def save(values) -> None:
    from app.overlay import overlay
    resolution = values.pop("resolution", SETTINGS.resolution)
    with SETTINGS_FILE_LOC.open("w") as f:
        json.dump({
            "un": SETTINGS.api_username,
            "resolution": resolution,
            **values
        }, f)
        SETTINGS.keybindings = KeyBindings(**values)
        SETTINGS.resolution = resolution
    overlay.window.set_alpha(1)


def save_sections(sections) -> None:
    from app.overlay import overlay
    from app.session_data import SESSION_DATA
    overlay.window.set_alpha(1)
    SESSION_DATA.scan_sections = sections
    logging.debug(f'Scan set for: {sections}')


def save_username(username) -> None:
    SETTINGS.api_username = username
    with SETTINGS_FILE_LOC.open("w") as f:
        json.dump({
            "un": username,
            "resolution": SETTINGS.resolution,
            **SETTINGS.keybindings.dict()
        }, f)
