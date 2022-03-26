import subprocess
from pathlib import Path
from typing import Optional

import requests

from settings import SETTINGS


def installer_file_path() -> Path:
    installer_path = SETTINGS.app_data_folder("Installer")
    installer_path.mkdir(exist_ok=True)
    downloaded_file_path = installer_path / "Installer.msi"
    return downloaded_file_path


def perform_update_download(download_link: str) -> Optional[Exception]:
    print(f"Downloading {download_link}")
    r = requests.get(download_link)
    downloaded_file_path = installer_file_path()
    try:
        with downloaded_file_path.open("wb") as f:
            f.write(r.content)
    except Exception as e:
        return e

    return None


def install_new_version(path: str) -> bool:
    print("Opening installer subprocess...")
    subprocess.Popen(
        args=["msiexec.exe", "/i", f"{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return True
