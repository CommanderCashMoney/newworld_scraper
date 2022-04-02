from typing import Dict, Tuple

import cv2
from pydantic import BaseModel

from app.ocr.utils import grab_screen
from app.settings import SETTINGS
from app.utils import resource_path


class ImageReference(BaseModel):
    screen_bbox: Tuple[int, int, int, int]
    file_name: str
    min_conf: float

    def compare_image_reference(self) -> bool:
        """Return true if the bbox of the img_ref matches the source image within a confidence level"""
        reference_grab = grab_screen(region=self.screen_bbox)
        reference_image_file = resource_path(f"app/images/new_world/{SETTINGS.resolution}/{self.file_name}")
        reference_img = cv2.imread(reference_image_file)
        img_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
        img_grab_gray = cv2.cvtColor(reference_grab, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img_grab_gray, img_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val > self.min_conf

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
    first_item_listing_bbox: Tuple[int, int, int, int]

    # column start/end. didn't include owned/time
    tp_row_height: int
    tp_name_col_x_coords: Tuple[int, int]
    tp_price_col_x_coords: Tuple[int, int]
    tp_avail_col_x_coords: Tuple[int, int]
    tp_tier_col_x_coords: Tuple[int, int]
    tp_gs_col_x_coords: Tuple[int, int]
    tp_gem_col_x_coords: Tuple[int, int]
    tp_perk_col_x_coords: Tuple[int, int]
    tp_rarity_col_x_coords: Tuple[int, int]
    tp_location_col_x_coords: Tuple[int, int]


res_1440p = Resolution(
    trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", min_conf=0.92),
    top_scroll=ImageReference(screen_bbox=(2438, 418, 34, 34), file_name="top_of_scroll.png", min_conf=0.95),
    mid_scroll=ImageReference(screen_bbox=(2442, 1314, 27, 27), file_name="btm_of_scroll.png", min_conf=0.95),
    bottom_scroll=ImageReference(screen_bbox=(2444, 1378, 25, 25), file_name="btm_of_scroll2.png", min_conf=0.95),
    cancel_button=ImageReference(screen_bbox=(961, 1032, 90, 30), file_name="cancel_btn.png", min_conf=0.95),
    refresh_button=ImageReference(screen_bbox=(1543, 900, 170, 40), file_name="refresh_btn.png", min_conf=0.95),
    next_page_coords=(2400, 300),
    pages_bbox=(2233, 287, 140, 32),
    items_bbox=(927, 430, 1510, 919),
    items_bbox_last=(927, 1198, 1510, 200),
    tp_row_height=256,
    tp_name_col_x_coords=(0, 380),
    tp_price_col_x_coords=(380, 550),
    tp_avail_col_x_coords=(1080, 1165),
    tp_tier_col_x_coords=(551, 630),
    tp_gs_col_x_coords=(631, 712),
    tp_gem_col_x_coords=(712, 802),
    tp_perk_col_x_coords=(0, 0),  # don't actually know
    tp_rarity_col_x_coords=(957, 1079),
    tp_location_col_x_coords=(1342, 1510),
    first_item_listing_bbox=(842, 444, 200, 70),
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


res_1080p = Resolution(
    trading_post=ImageReference(screen_bbox=(341, 29, 103, 28), file_name="trading_post_label.png", min_conf=0.92),
    top_scroll=ImageReference(screen_bbox=(1833, 651, 19, 29), file_name="top_of_scroll.png", min_conf=0.95),
    mid_scroll=ImageReference(screen_bbox=(1833, 973, 19, 38), file_name="btm_of_scroll.png", min_conf=0.95),
    bottom_scroll=ImageReference(screen_bbox=(1833, 681, 16, 33), file_name="btm_of_scroll2.png", min_conf=0.95),
    cancel_button=ImageReference(screen_bbox=(721, 775, 63, 17), file_name="cancel_btn.png", min_conf=0.95),
    refresh_button=ImageReference(screen_bbox=(1165, 678, 118, 22), file_name="refresh_btn.png", min_conf=0.95),
    next_page_coords=(1801, 226),
    pages_bbox=(1665, 214, 114, 22),
    items_bbox=(694, 316, 1138, 694),
    items_bbox_last=(692, 896, 1139, 152),
    tp_row_height=72*2.5,
    tp_name_col_x_coords=(0, 273),
    tp_price_col_x_coords=(273, 416),
    tp_avail_col_x_coords=(813, 876),
    tp_tier_col_x_coords=(416, 475),
    tp_gs_col_x_coords=(475, 537),
    tp_gem_col_x_coords=(537, 604),
    tp_perk_col_x_coords=(604, 721),
    tp_rarity_col_x_coords=(721, 813),
    tp_location_col_x_coords=(1010, 1122),
    first_item_listing_bbox=(620, 319, 261, 71),

    sections={
           'Resources Reset 0': (122, 597),
           'Raw Resources': (230, 370),
           'Resources Reset 1': (122, 597),
           'Refined Resources': (243, 421),
           'Resources Reset 2': (122, 597),
           'Cooking Ingredients': (283, 476),
           'Resources Reset 3': (122, 597),
           'Craft Mods': (233, 526),
           'Resources Reset 4': (122, 597),
           'Components': (234, 586),
           'Resources Reset 5': (122, 597),
           'Potion Reagents': (248, 637),
           'Resources Reset 6': (122, 597),
           'Dyes': (209, 690),
           'Resources Reset 7': (122, 597),
           'Azoth': (204, 746),
           'Resources Reset 8': (122, 597),
           'Arcana': (221, 796),
           'Consumables': (125, 670),
           'Ammunition': (121, 740),
           'House Furnishings': (122, 818)
       },
)


def get_resolution_obj():
    if SETTINGS.resolution == "1440p":
        return res_1440p
    elif SETTINGS.resolution == "1080p":
        return res_1080p
    return res_1440p  # don't think this will ever happen, but safer than assuming
