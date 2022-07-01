from pathlib import Path
import cv2
import numpy as np

from app.ocr.utils import Screenshot
from app.ocr.resolution_settings import resolutions

def get_resource(file_name: str) -> str:
    p = Path(__file__, '../resources', file_name)
    if p.exists():
        return str(p.absolute())
    return None


def get_screenshot_bbox(image_path, debug=False):
    image_path = get_resource(image_path)

    def screenshot_bbox(left: int, top: int, width: int, height: int, save_to: str = None) -> Screenshot:
        img = cv2.imread(image_path)
        if(img.shape[1] > 2560):
            img = cv2.resize(img, (2560, 1440), cv2.INTER_AREA) # always to 2k

        if debug:
            cv2.rectangle(img, (left, top), (left + width, top + height), (255, 255, 255), 2)
            cv2.imshow('screenshot_bbox search_area', img)
            cv2.waitKey(0)

        img = img[top:top+height, left:left+width]
        ss = Screenshot(np.asarray(img))

        if save_to:
            ss.file_path = image_path
        return ss
    return screenshot_bbox


def get_capture_screen(image_path):
    image_path = get_resource(image_path)

    def capture_screen(save_to: str = None) -> Screenshot:
        """Return entire screen as an RGB array. save_to has a high performance cost."""
        img = cv2.imread(image_path)
        ss = Screenshot(np.asarray(img))

        if save_to:
            ss.file_path = image_path

        return ss
    return capture_screen
