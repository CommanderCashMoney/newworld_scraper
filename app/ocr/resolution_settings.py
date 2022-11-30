from typing import Dict, Tuple

import cv2
from pydantic import BaseModel

from app.ocr.utils import screenshot_bbox
from app.utils import resource_path
import logging


class ImageReference(BaseModel):
    screen_bbox: Tuple[int, int, int, int]
    file_name: str
    min_conf: float

    def compare_image_reference(self) -> bool:
        from app.settings import SETTINGS
        """Return true if the bbox of the img_ref matches the source image within a confidence level"""
        reference_grab = screenshot_bbox(*self.screen_bbox).img_array
        reference_image_file = resource_path(f"app/images/new_world/{SETTINGS.resolution}/{self.file_name}")
        reference_img = cv2.imread(reference_image_file)
        img_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
        img_grab_gray = cv2.cvtColor(reference_grab, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img_grab_gray, img_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # debug version. Enable this
        # if max_val < self.min_conf:
        #     logging.info(f'{self.file_name} couldnt be matched. Conf score: {max_val}')
        #     bpc = SETTINGS.temp_app_data
        #     cv2.imwrite(f'{bpc}/bad{self.file_name}', reference_grab)
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
    name: str
    sections: Dict[str, Tuple[Tuple[int, int], bool]]
    resources_reset_loc: Tuple[int, int]
    trading_post: ImageReference
    top_scroll: ImageReference
    mid_scroll: ImageReference
    bottom_scroll: ImageReference
    cancel_button: ImageReference
    refresh_button: ImageReference
    next_page_coords: Tuple[int, int]
    mouse_scroll_loc: Tuple[int, int]
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

    def __str__(self) -> str:
        return f"<Resolution: {self.name}>"


res_1440p = Resolution(
    name="1440p",
    trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", min_conf=0.92),
    top_scroll=ImageReference(screen_bbox=(2438, 418, 34, 34), file_name="top_of_scroll.png", min_conf=0.95),
    mid_scroll=ImageReference(screen_bbox=(2442, 1314, 27, 27), file_name="mid_scroll_bottom.png", min_conf=0.95),
    bottom_scroll=ImageReference(screen_bbox=(2443, 915, 25, 38), file_name="bottom_of_scroll_bottom.png", min_conf=0.95),
    cancel_button=ImageReference(screen_bbox=(961, 1032, 90, 30), file_name="cancel_btn.png", min_conf=0.95),
    refresh_button=ImageReference(screen_bbox=(1543, 900, 170, 40), file_name="refresh_btn.png", min_conf=0.95),
    next_page_coords=(2400, 300),
    pages_bbox=(2335, 293, 33, 17),
    items_bbox=(927, 430, 1510, 919),
    items_bbox_last=(927, 1198, 1510, 200),
    tp_row_height=256,
    tp_name_col_x_coords=(0, 380),
    tp_price_col_x_coords=(380, 550),
    tp_avail_col_x_coords=(1320, 1440),
    tp_tier_col_x_coords=(551, 630),
    tp_gs_col_x_coords=(631, 712),  # no longer accurate
    tp_gem_col_x_coords=(712, 802),
    tp_perk_col_x_coords=(0, 0),  # don't actually know
    tp_rarity_col_x_coords=(957, 1079),
    tp_location_col_x_coords=(1342, 1510),
    first_item_listing_bbox=(842, 444, 200, 70),
    mouse_scroll_loc=(2435, 438),
    # False and True indicate if a resource reset is needed before starting this section
    resources_reset_loc=(170, 796),
    sections={
           'Raw Resources': ((368, 488), True),
           'Arcana': ((368, 568), True),
           'Potion Reagents': ((368, 632), True),
           'Cooking Ingredients': ((368, 708), True),
           'Dye Ingredients': ((368, 788), True),
           'Refined Resources': ((368, 855), True),
           'Components': ((368, 936), True),
           'Craft Mods': ((368, 990), True),
           'Azoth': ((368, 1068), True),
           'Runeglass Components': ((368, 1140), True),
           'Consumables': ((165, 900), False),
           'Ammunition': ((165, 985), False),
           'House Furnishings': ((165, 1091), False)
       },
)


res_1080p = Resolution(
    name="1080p",
    trading_post=ImageReference(screen_bbox=(338, 31, 96, 24), file_name="trading_post_label.png", min_conf=0.92),
    top_scroll=ImageReference(screen_bbox=(1833, 314, 18, 19), file_name="top_of_scroll.png", min_conf=0.95),
    mid_scroll=ImageReference(screen_bbox=(1833, 634, 18, 23), file_name="mid_scroll_bottom.png", min_conf=0.95),
    bottom_scroll=ImageReference(screen_bbox=(1835, 1031, 13, 19), file_name="bottom_of_scroll_bottom.png", min_conf=0.95),
    cancel_button=ImageReference(screen_bbox=(720, 772, 63, 17), file_name="cancel_btn.png", min_conf=0.95),
    refresh_button=ImageReference(screen_bbox=(1163, 676, 120, 19), file_name="refresh_btn.png", min_conf=0.95),
    next_page_coords=(1802, 227),
    pages_bbox=(1748, 217, 30, 17),
    items_bbox=(691, 320, 1129, 696),
    items_bbox_last=(691, 896, 1129, 153),
    tp_row_height=79*2.5,
    tp_name_col_x_coords=(0, 275),
    tp_price_col_x_coords=(275, 418),
    tp_avail_col_x_coords=(1000, 1083),
    tp_tier_col_x_coords=(418, 478),
    tp_gs_col_x_coords=(478, 539),
    tp_gem_col_x_coords=(539, 607),
    tp_perk_col_x_coords=(607, 724),
    tp_rarity_col_x_coords=(724, 815),
    tp_location_col_x_coords=(1012, 1125),
    first_item_listing_bbox=(691, 316, 1129, 79),
    mouse_scroll_loc=(1826, 347),
    resources_reset_loc=(125, 602),
    # False and True indicate if a resource reset is needed before starting this section
    sections={

           'Raw Resources': ((249, 365), True),
           'Arcana': ((252, 424), True),
           'Potion Reagents': ((248, 475), True),
           'Cooking Ingredients': ((243, 532), True),
           'Dye Ingredients': ((239, 582), True),
           'Refined Resources': ((241, 638), True),
           'Components': ((252, 697), True),
           'Craft Mods': ((237, 746), True),
           'Azoth': ((239, 803), True),
           'Runeglass Components': ((239, 863), True),
           'Consumables': ((131, 673), False),
           'Ammunition': ((121, 740), False),
           'House Furnishings': ((123, 816), False)
    },
)


resolutions = {
    "1080p": res_1080p,
    "1440p": res_1440p
}


def get_resolution_obj():
    from app.settings import SETTINGS  # circular
    return resolutions[SETTINGS.resolution]
