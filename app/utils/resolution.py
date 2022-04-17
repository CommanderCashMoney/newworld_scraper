import logging
from typing import Optional, Tuple


def get_resolution() -> Optional[Tuple[int, int]]:
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except:  # noqa
        pass
    return None, None


def get_default_resolution_key():
    from app.ocr.resolution_settings import resolutions
    width, height = get_resolution()
    res_str = f"{height}p"
    if res_str in resolutions:
        return res_str
    logging.warning(f"Your resolution was detected as {width}x{height}, but this is not supported.")
    return "1440p"
