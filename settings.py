from enum import Enum
from pathlib import Path

from pydantic import BaseSettings


class Environment(Enum):
    prod = "prod"
    dev = "dev"


class Versioning(Enum):
    major = 3
    minor = 2
    patch = 1


class Settings(BaseSettings):
    VERSION = "1.0.8"
    FORCE_UPDATE_ON_VERSION = Versioning.patch

    environment: Environment = Environment.prod

    nwmp_dev_api_host: str = "http://localhost:8080/"
    nwmp_prod_api_host: str = "https://nwmarketprices.com/"
    # user/pass can be set for development purposes in .env to avoid having to type each time
    api_username: str = ""
    api_password: str = ""
    APPDATA: str = None

    def app_data_folder(self, relative_path: str) -> Path:
        if self.APPDATA is None:
            raise ValueError("No appdata folder found. TODO: set a default")
        app_data_base = Path(self.APPDATA)
        app_data_folder = app_data_base / "Cash Money Development" / "Trading Post Scraper" / relative_path
        app_data_folder.mkdir(parents=True, exist_ok=True)
        return app_data_folder

    @property
    def temp_app_data(self) -> Path:
        return self.app_data_folder("temp")

    @property
    def is_dev(self) -> bool:
        return self.environment == Environment.dev

    class Config:
        env_file = ".env"


SETTINGS = Settings()
