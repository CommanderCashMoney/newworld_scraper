from typing import Dict, Tuple
import logging
import cv2
from pydantic import BaseModel

from app.ocr.utils import screenshot_bbox
from app.utils import resource_path
import numpy as np


class ImageReference(BaseModel):
    screen_bbox: Tuple[int, int, int, int]
    file_name: str
    min_conf: float

    def compare_image_reference(self, ret_val=bool):
        from app.settings import SETTINGS
        """Return true if the bbox of the img_ref matches the source image within a confidence level"""
        reference_grab = screenshot_bbox(*self.screen_bbox).img_array
        reference_image_file = resource_path(f"app/images/new_world/{SETTINGS.resolution}/{self.file_name}")
        reference_img = cv2.imdecode(np.fromfile(reference_image_file, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        # reference_img = cv2.imread(reference_image_file)
        img_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
        img_grab_gray = cv2.cvtColor(reference_grab, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img_grab_gray, img_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # debug version. Enable this
        # if max_val < self.min_conf:
        #     logging.info(f'{self.file_name} couldnt be matched. Conf score: {max_val}')
        #     bpc = SETTINGS.temp_app_data
        #     cv2.imwrite(f'{bpc}/bad{self.file_name}', reference_grab)
        if ret_val == bool:
            return max_val > self.min_conf
        else:
            return max_val

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
    # trading_post: ImageReference
    my_orders_clip_icon: ImageReference
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
    menu_loc: Tuple[int, int]
    exit_to_desk_loc: Tuple[int, int]
    yes_button_loc: Tuple[int, int]
    resources_reset_loc: Tuple[int, int]
    sort_up_arrow: ImageReference

    #  sold orders
    sold_order_top_scroll: ImageReference
    sold_order_bottom_scroll: ImageReference
    sold_order_items_bbox: Tuple[int, int, int, int]
    sold_order_items_full_bbox: Tuple[int, int, int, int]
    sold_order_tp_name_col_x_coords: Tuple[int, int]
    sold_order_tp_price_col_x_coords: Tuple[int, int]
    sold_order_qty_col_x_coords: Tuple[int, int]
    sold_order_sold_qty_col_x_coords: Tuple[int, int]
    sold_order_tp_gs_col_x_coords: Tuple[int, int]
    sold_order_tp_gem_col_x_coords: Tuple[int, int]
    sold_order_tp_perk_col_x_coords: Tuple[int, int]
    sold_order_tp_status_col_x_coords: Tuple[int, int]
    sold_order_tp_completion_time_col_x_coords: Tuple[int, int]
    sold_order_completed_tab: Tuple[int, int]
    sold_order_sold_items_tab: Tuple[int, int]
    sold_order_mouse_scroll_loc: Tuple[int, int]
    sold_order_price_sort_down: ImageReference

    # buy orders
    sell_tab_coords: Tuple[int, int]
    buy_order_all_items: Tuple[int, int]
    buy_order_top_scroll: ImageReference
    buy_order_mid_scroll: ImageReference
    buy_order_bottom_scroll: ImageReference
    buy_order_cancel_button: ImageReference
    buy_order_refresh_button: ImageReference
    buy_order_next_page_coords: Tuple[int, int]
    buy_order_pages_bbox: Tuple[int, int, int, int]
    buy_order_items_bbox: Tuple[int, int, int, int]
    buy_order_items_bbox_last: Tuple[int, int, int, int]
    buy_order_tp_row_height: int
    buy_order_tp_name_col_x_coords: Tuple[int, int]
    buy_order_tp_price_col_x_coords: Tuple[int, int]
    buy_order_tp_tier_col_x_coords: Tuple[int, int]
    buy_order_tp_gs_col_x_coords: Tuple[int, int]
    buy_order_tp_attri_col_x_coords: Tuple[int, int]
    buy_order_tp_perk_col_x_coords: Tuple[int, int]
    buy_order_tp_gem_col_x_coords: Tuple[int, int]
    buy_order_tp_qty_col_x_coords: Tuple[int, int]
    buy_order_first_item_listing_bbox: Tuple[int, int, int, int]
    buy_order_mouse_scroll_loc: Tuple[int, int]
    buy_order_all_items_tab: Tuple[int, int]
    buy_order_sections: Dict[str, Tuple[Tuple[int, int], bool]]
    buy_order_sort_down_arrow: ImageReference
    def __str__(self) -> str:
        return f"<Resolution: {self.name}>"


res_1440p = Resolution(
    name="1440p",
    # trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", min_conf=0.90),
    my_orders_clip_icon=ImageReference(screen_bbox=(1056, 192, 20, 22), file_name="my_orders_clip_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(2438, 418, 34, 34), file_name="top_of_scroll.png", min_conf=0.90),
    mid_scroll=ImageReference(screen_bbox=(2442, 1314, 27, 27), file_name="mid_scroll_bottom.png", min_conf=0.90),
    bottom_scroll=ImageReference(screen_bbox=(2443, 915, 25, 38), file_name="bottom_of_scroll_bottom.png", min_conf=0.90),
    cancel_button=ImageReference(screen_bbox=(961, 1032, 90, 30), file_name="cancel_btn.png", min_conf=0.90),
    refresh_button=ImageReference(screen_bbox=(1543, 900, 170, 40), file_name="refresh_btn.png", min_conf=0.90),
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
    menu_loc=(2492, 75),
    exit_to_desk_loc=(1765, 884),
    yes_button_loc=(1463, 864),
    resources_reset_loc=(170, 796),
    sort_up_arrow=ImageReference(screen_bbox=(1316, 392, 17, 25), file_name="sort_up_arrow.png", min_conf=0.90),
    # --------Sold Orders ----------------
    sold_order_top_scroll=ImageReference(screen_bbox=(2374, 509, 34, 34), file_name="top_of_scroll.png", min_conf=0.95),
    sold_order_bottom_scroll=ImageReference(screen_bbox=(2380, 1342, 24, 14), file_name="sold_order_bottom_scroll.png", min_conf=0.70),
    sold_order_items_bbox=(757, 523, 1601, 709),
    sold_order_items_full_bbox=(757, 523, 1616, 812),
    sold_order_tp_name_col_x_coords=(0, 316),
    sold_order_tp_price_col_x_coords=(316, 439),
    sold_order_qty_col_x_coords=(439, 563),
    sold_order_sold_qty_col_x_coords=(563, 686),
    sold_order_tp_gs_col_x_coords=(686, 810),
    sold_order_tp_gem_col_x_coords=(810, 933),
    sold_order_tp_perk_col_x_coords=(933, 1057),
    sold_order_tp_status_col_x_coords=(1057, 1238),
    sold_order_tp_completion_time_col_x_coords=(1238, 1428),
    sold_order_completed_tab=(833, 397),
    sold_order_sold_items_tab=(382, 557),
    sold_order_mouse_scroll_loc=(2370, 528),
    sold_order_price_sort_down=ImageReference(screen_bbox=(1076, 483, 17, 25), file_name="sold_order_price_sort_down.png", min_conf=0.70),
    # --------Buy Orders ----------------
    sell_tab_coords=(754, 210),
    buy_order_all_items=(985, 308),
    buy_order_top_scroll=ImageReference(screen_bbox=(2416, 497, 34, 34), file_name="top_of_scroll.png", min_conf=0.90),
    buy_order_mid_scroll=ImageReference(screen_bbox=(2421, 1196, 27, 27), file_name="mid_scroll_bottom.png", min_conf=0.86),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(2421, 987, 25, 38), file_name="bottom_of_scroll_bottom.png", min_conf=0.90),
    buy_order_cancel_button=ImageReference(screen_bbox=(967, 1127, 90, 30), file_name="cancel_btn.png", min_conf=0.90),
    buy_order_refresh_button=ImageReference(screen_bbox=(1558, 946, 170, 40), file_name="refresh_btn.png", min_conf=0.90),
    buy_order_next_page_coords=(2379, 411),
    buy_order_pages_bbox=(2310, 398, 34, 19),
    buy_order_items_bbox=(949, 508, 1468, 714),
    buy_order_items_bbox_last=(949, 786, 1468, 612),
    buy_order_tp_row_height=256,
    buy_order_tp_name_col_x_coords=(0, 336),
    buy_order_tp_price_col_x_coords=(336, 548),
    buy_order_tp_tier_col_x_coords=(548, 665),
    buy_order_tp_gs_col_x_coords=(665, 785),
    buy_order_tp_attri_col_x_coords=(785, 972),
    buy_order_tp_perk_col_x_coords=(972, 1145),
    buy_order_tp_gem_col_x_coords=(1145, 1279),
    buy_order_tp_qty_col_x_coords=(1279, 1413),
    buy_order_first_item_listing_bbox=(870, 516, 200, 70),
    buy_order_mouse_scroll_loc=(2412, 523),
    buy_order_all_items_tab=(1003, 311),
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(1288, 471, 17, 25), file_name="sort_up_arrow.png", min_conf=0.90),


    # ------------------------------------
    # False and True indicate if a resource reset is needed before starting this section
    # buy_order_adjustment=(30, 105),  # add this to the loc of the section below to get the loc for buy orders
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
           'House Furnishings': ((165, 1091), False),
           'Buy Orders': ((754, 210), False),
           'Sold Items': ((1183, 207), False),
       },
    buy_order_sections={
            'Buy Order - Resources': ((200, 901), False),
            'Buy Order - Consumables': ((195, 1005), False),
            'Buy Order - Ammunition': ((195, 1090), False),
            'Buy Order - House Furnishings': ((195, 1196), False),
    },
)


res_1080p = Resolution(
    name="1080p",
    # trading_post=ImageReference(screen_bbox=(338, 31, 96, 24), file_name="trading_post_label.png", min_conf=0.90),
    my_orders_clip_icon=ImageReference(screen_bbox=(792, 144, 15, 17), file_name="my_orders_clip_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(1833, 314, 18, 19), file_name="top_of_scroll.png", min_conf=0.90),
    mid_scroll=ImageReference(screen_bbox=(1833, 634, 18, 23), file_name="mid_scroll_bottom.png", min_conf=0.90),
    bottom_scroll=ImageReference(screen_bbox=(1835, 1031, 13, 19), file_name="bottom_of_scroll_bottom.png", min_conf=0.90),
    cancel_button=ImageReference(screen_bbox=(720, 772, 63, 17), file_name="cancel_btn.png", min_conf=0.90),
    refresh_button=ImageReference(screen_bbox=(1163, 676, 120, 19), file_name="refresh_btn.png", min_conf=0.90),
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
    menu_loc=(1869, 53),
    exit_to_desk_loc=(1325, 664),
    yes_button_loc=(1103, 649),
    sort_up_arrow=ImageReference(screen_bbox=(987, 294, 13, 19), file_name="sort_up_arrow.png", min_conf=0.90),
    # --------Sold Orders ----------------
    sold_order_top_scroll=ImageReference(screen_bbox=(1785, 382, 34, 34), file_name="top_of_scroll.png", min_conf=0.95),
    sold_order_bottom_scroll=ImageReference(screen_bbox=(1785, 1007, 18, 11), file_name="sold_order_bottom_scroll.png",
                                            min_conf=0.70),
    sold_order_items_bbox=(568, 392, 1201, 532),
    sold_order_items_full_bbox=(568, 392, 1201, 609),
    sold_order_tp_name_col_x_coords=(0, 237),
    sold_order_tp_price_col_x_coords=(237, 329),
    sold_order_qty_col_x_coords=(329, 422),
    sold_order_sold_qty_col_x_coords=(422, 515),
    sold_order_tp_gs_col_x_coords=(515, 608),
    sold_order_tp_gem_col_x_coords=(608, 700),
    sold_order_tp_perk_col_x_coords=(700, 793),
    sold_order_tp_status_col_x_coords=(793, 929),
    sold_order_tp_completion_time_col_x_coords=(929, 1071),
    sold_order_completed_tab=(630, 296),
    sold_order_sold_items_tab=(287, 414),
    sold_order_mouse_scroll_loc=(1778, 396),
    sold_order_price_sort_down=ImageReference(screen_bbox=(807, 362, 13, 19), file_name="sold_order_price_sort_down.png", min_conf=0.70),
    # --------Buy Orders ----------------
    sell_tab_coords=(566, 158),
    buy_order_all_items=(739, 231),
    buy_order_top_scroll=ImageReference(screen_bbox=(1817, 373, 18, 19), file_name="top_of_scroll.png", min_conf=0.90),
    buy_order_mid_scroll=ImageReference(screen_bbox=(1817, 600, 18, 23), file_name="mid_scroll_bottom.png",
                                        min_conf=0.86),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(1817, 1034, 13, 19), file_name="buy_order_bottom_of_scroll.png",
                                           min_conf=0.90),
    buy_order_cancel_button=ImageReference(screen_bbox=(723, 842, 63, 17), file_name="cancel_btn.png", min_conf=0.90),
    buy_order_refresh_button=ImageReference(screen_bbox=(1166, 706, 120, 19), file_name="refresh_btn.png",
                                            min_conf=0.90),
    buy_order_next_page_coords=(1784, 308),
    buy_order_pages_bbox=(1733, 299, 26, 14),
    buy_order_items_bbox=(712, 381, 1101, 536),
    buy_order_items_bbox_last=(712, 744, 1101, 305),
    buy_order_tp_row_height=79*2.5,
    buy_order_tp_name_col_x_coords=(0, 252),
    buy_order_tp_price_col_x_coords=(252, 411),
    buy_order_tp_tier_col_x_coords=(411, 499),
    buy_order_tp_gs_col_x_coords=(499, 589),
    buy_order_tp_attri_col_x_coords=(589, 729),
    buy_order_tp_perk_col_x_coords=(729, 862),
    buy_order_tp_gem_col_x_coords=(862, 959),
    buy_order_tp_qty_col_x_coords=(959, 1060),
    buy_order_first_item_listing_bbox=(653, 387, 150, 53),
    buy_order_mouse_scroll_loc=(1809, 392),
    buy_order_all_items_tab=(752, 233),
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(966, 353, 13, 19), file_name="sort_up_arrow.png", min_conf=0.90),

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
           'House Furnishings': ((123, 816), False),
           'Buy Orders': ((566, 156), False),
           'Sold Items': ((885, 152), False)
    },
    buy_order_sections={
        'Buy Order - Resources': ((150, 676), False),
        'Buy Order - Consumables': ((146, 754), False),
        'Buy Order - Ammunition': ((146, 818), False),
        'Buy Order - House Furnishings': ((146, 897), False),
    },
)


resolutions = {
    "1080p": res_1080p,
    "1440p": res_1440p
}


def get_resolution_obj():
    from app.settings import SETTINGS  # circular
    return resolutions[SETTINGS.resolution]
