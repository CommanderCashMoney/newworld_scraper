import os
import sys
from pathlib import Path
from typing import Union


def resource_path(relative_path: Path, as_path=False) -> Union[str, Path]:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', Path(os.path.abspath(__file__)).parent.parent.parent)
    path_obj = Path(base_path) / relative_path
    if as_path:
        return path_obj
    return str(path_obj)


def format_seconds(s):
    hours, rem = divmod(s, 3600)
    minutes, seconds = divmod(rem, 60)
    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
