import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict

from pydantic import BaseSettings, root_validator


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
    VERSION = "1.2.1"

    environment: Environment = Environment.prod
    use_dev_colors: bool = False
    console_logging_level: str = "INFO"

    nwmp_dev_api_host: str = "http://localhost:8080/"
    nwmp_prod_api_host: str = "https://nwmarketprices.com/"
    # user/pass can be set for development purposes in .env to avoid having to type each time
    api_username: str = ""
    api_password: str = ""

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
        return 10 * 60

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
            resolution = settings_values.pop("resolution", "")  # future branch compatibility
            keybinds = KeyBindings(**settings_values)
            return Settings(api_username=username, keybindings=keybinds)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return Settings()


SETTINGS = load_settings()


def save(values) -> None:
    from app.overlay import overlay
    with SETTINGS_FILE_LOC.open("w") as f:
        json.dump({
            "un": SETTINGS.api_username,
            **values
        }, f)
        SETTINGS.keybindings = KeyBindings(**values)
    overlay.window.set_alpha(1)


def save_username(username) -> None:
    SETTINGS.api_username = username
    with SETTINGS_FILE_LOC.open("w") as f:
        json.dump({
            "un": username,
            **SETTINGS.keybindings.dict()
        }, f)
