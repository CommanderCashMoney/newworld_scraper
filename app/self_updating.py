import subprocess
import traceback
from pathlib import Path
from typing import Optional

import requests

from app.nwmp_api import version_endpoint
from app.overlay import overlay
from settings import SETTINGS

VERSION_FETCHED_EVENT = "-VERSION FETCHED-"
DOWNLOAD_NEW_VERSION_EVENT = "-DOWNLOAD NEW VERSION-"
INSTALLER_LAUNCHED_EVENT = "-INSTALLING-"


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


def version_update_events(event, values) -> None:
    if event == VERSION_FETCHED_EVENT:
        response = values[VERSION_FETCHED_EVENT]
        if response is not None:
            overlay.version_check_complete(response)
            if not response["compatible_version"]:
                overlay.show_update_window()
            return
        # otherwise, we error out.
        hide = ["un_text", "un", "pw_text", "pw", "login"]
        for element in hide:
            overlay.window[element].update(visible=False)
        endpoint = version_endpoint()
        overlay.window["title"].update(
            f"Version check failed! :(\n\nNo connection to {endpoint}\n\nPlease let us know on discord."
        )
        overlay.set_spinner_visibility(False)
    elif event == "download_update":
        download_func = lambda: perform_update_download(overlay.download_link)  # noqa
        overlay.window.perform_long_operation(download_func, DOWNLOAD_NEW_VERSION_EVENT)
        overlay.window["download_update"].update(text="Downloading...", disabled=True)
        overlay.set_spinner_visibility(True)
    elif event == DOWNLOAD_NEW_VERSION_EVENT:
        if values[DOWNLOAD_NEW_VERSION_EVENT] is not None:
            exc = values[DOWNLOAD_NEW_VERSION_EVENT]
            overlay.window["download_update_text"].update(
                f"Couldn't download file.\n\n"
                f"Please check the installer is not already open.\n\n"
                f"Please close application once you check the error log."
            )
            formatted_exception = "".join(traceback.format_exception(None, exc, exc.__traceback__))
            print(formatted_exception)
            overlay.window["download_update"].update(visible=False)
            overlay.set_spinner_visibility(False)
            return
        install_func = lambda: install_new_version(installer_file_path())  # noqa
        overlay.window.perform_long_operation(install_func, INSTALLER_LAUNCHED_EVENT)