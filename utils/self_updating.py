import subprocess
from subprocess import Popen

import requests

from settings import SETTINGS


def perform_update_download(download_link: str):
    print(f"Downloading {download_link}")
    r = requests.get(download_link)
    installer_path = SETTINGS.app_data_folder("Installer")
    installer_path.mkdir(exist_ok=True)
    download_file_path = installer_path / "Installer.msi"
    with download_file_path.open("wb") as f:
        f.write(r.content)
    print("Done!")
    return download_file_path


def install_new_version(path: str) -> bool:
    subprocess.Popen(
        args=["msiexec.exe", "/i", f"{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return True
