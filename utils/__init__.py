import os
import sys
from pathlib import Path
from urllib.parse import urljoin

from settings import SETTINGS


def get_endpoint_from_func_name(func: str, target_env: str, is_api: bool = True) -> str:
    func_to_endpoint_map = {
        "price_insert": "scanner_upload/",
        "name_cleanup_insert": "name_cleanup_upload/",
        "confirmed_names_insert": "confirmed_names_upload/",
    }

    if target_env == "dev":
        base_url = SETTINGS.nwmp_dev_api_host
    else:
        base_url = SETTINGS.nwmp_prod_api_host
    if is_api:
        base_url = urljoin(base_url, "api/")
    relative_url = func_to_endpoint_map.get(func, f"{func}/")
    return urljoin(base_url, relative_url)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', Path(os.path.abspath(__file__)).parent.parent)
    return os.path.join(base_path, relative_path)
