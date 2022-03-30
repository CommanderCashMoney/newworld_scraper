from typing import Dict, Tuple

import cv2
from pydantic import BaseModel

from app.ocr.utils import grab_screen
from app.utils import resource_path


class ImageReference(BaseModel):
    screen_bbox: Tuple[int, int, int, int]
    file_name: str
    conf: float

    def compare_image_reference(self) -> bool:
        """Return true if the bbox of the img_ref matches the source image within a confidence level"""
        reference_grab = grab_screen(region=self.screen_bbox)
        reference_image_file = resource_path(f"app/images/new_world/{self.file_name}")
        reference_img = cv2.imread(reference_image_file)
        res = cv2.matchTemplate(reference_grab, reference_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val > self.conf

    @property
    def x(self) -> int:
        return self.screen_bbox[0]

    @property
    def max_x(self) -> int:
        return self.x + self.screen_bbox[2]

    @property
    def y(self) -> int:
        return self.screen_bbox[1]

    @property
    def max_y(self) -> int:
        return self.y + self.screen_bbox[3]

    @property
    def center(self) -> Tuple[int, int]:
        x_center = self.x + int(self.screen_bbox[2] / 2)
        y_center = self.y + int(self.screen_bbox[3] / 2)
        return x_center, y_center


class Resolution(BaseModel):
    sections: Dict[str, Tuple[int, int]]
    trading_post: ImageReference
    top_scroll: ImageReference
    mid_scroll: ImageReference
    bottom_scroll: ImageReference
    cancel_button: ImageReference
    refresh_button: ImageReference
    next_page_coords: Tuple[int, int]
    pages_bbox: Tuple[int, int, int, int]
    items_bbox: Tuple[int, int, int, int]
    items_bbox_last: Tuple[int, int, int, int]


res_1440p = Resolution(
    trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", conf=0.92),
    top_scroll=ImageReference(screen_bbox=(2438, 418, 34, 34), file_name="top_of_scroll.png", conf=0.95),
    mid_scroll=ImageReference(screen_bbox=(2442, 1314, 27, 27), file_name="btm_of_scroll.png", conf=0.95),
    bottom_scroll=ImageReference(screen_bbox=(2444, 1378, 25, 25), file_name="btm_of_scroll2.png", conf=0.95),
    cancel_button=ImageReference(screen_bbox=(961, 1032, 90, 30), file_name="cancel_btn.png", conf=0.95),
    refresh_button=ImageReference(screen_bbox=(1543, 900, 170, 40), file_name="refresh_btn.png", conf=0.95),
    next_page_coords=(2400, 300),
    pages_bbox=(2233, 287, 140, 32),
    items_bbox=(927, 430, 1510, 919),
    items_bbox_last=(927, 1198, 1510, 200),
    sections={
           'Resources Reset 0': (170, 796),
           'Raw Resources': (368, 488),
           'Resources Reset 1': (170, 796),
           'Refined Resources': (368, 568),
           'Resources Reset 2': (170, 796),
           'Cooking Ingredients': (368, 632),
           'Resources Reset 3': (170, 796),
           'Craft Mods': (368, 708),
           'Resources Reset 4': (170, 796),
           'Components': (368, 788),
           'Resources Reset 5': (170, 796),
           'Potion Reagents': (368, 855),
           'Resources Reset 6': (170, 796),
           'Dyes': (368, 936),
           'Resources Reset 7': (170, 796),
           'Azoth': (368, 990),
           'Resources Reset 8': (170, 796),
           'Arcana': (368, 1068),
           'Consumables': (165, 900),
           'Ammunition': (165, 985),
           'House Furnishings': (165, 1091)
       },
)
