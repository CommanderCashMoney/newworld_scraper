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

    def compare_image_reference(self, ret_val=False):
        from app.settings import SETTINGS
        from app.session_data import SESSION_DATA
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
        if SESSION_DATA.debug:
            if max_val < self.min_conf:
                logging.info(f'{self.file_name} couldnt be matched. Conf score: {round(max_val, 2)}')
                bpc = SETTINGS.temp_app_data
                cv2.imwrite(f'{bpc}/bad{self.file_name}', reference_grab)
        if not ret_val:
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
    # my_orders_clip_icon: ImageReference
    buy_icon: ImageReference
    top_scroll: ImageReference
    mid_scroll: ImageReference
    bottom_scroll: ImageReference
    cancel_button: ImageReference
    refresh_button: ImageReference
    next_page_coords: Tuple[int, int]
    mouse_scroll_loc: Tuple[int, int]
    pages_bbox: Tuple[int, int, int, int]
    current_page_bbox: Tuple[int, int, int, int]
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
    buy_order_current_page_bbox: Tuple[int, int, int, int]
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

res_4k = Resolution(
    name="3840x2160",
    # trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", min_conf=0.90),
    # my_orders_clip_icon=ImageReference(screen_bbox=(1056, 192, 20, 22), file_name="my_orders_clip_icon.png", min_conf=0.70),
    buy_icon=ImageReference(screen_bbox=(372, 286, 45, 33), file_name="buy_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(3657, 627, 51, 51), file_name="top_of_scroll.png", min_conf=0.80),
    mid_scroll=ImageReference(screen_bbox=(3664, 1971, 39, 39), file_name="mid_scroll_bottom.png", min_conf=0.80),
    bottom_scroll=ImageReference(screen_bbox=(3665, 1372, 37, 57), file_name="bottom_of_scroll_bottom.png", min_conf=0.75),
    cancel_button=ImageReference(screen_bbox=(1444, 1550, 123, 33), file_name="cancel_btn.png", min_conf=0.80),
    refresh_button=ImageReference(screen_bbox=(2330, 1358, 235, 34), file_name="refresh_btn.png", min_conf=0.80),
    next_page_coords=(3600, 450),
    pages_bbox=(3503, 440, 50, 26),
    current_page_bbox=(3332, 438, 161, 32),
    items_bbox=(1391, 645, 2265, 1379),
    items_bbox_last=(1391, 1797, 2265, 300),
    tp_row_height=384,
    tp_name_col_x_coords=(0, 570),
    tp_price_col_x_coords=(570, 825),
    tp_avail_col_x_coords=(1980, 2160),
    tp_tier_col_x_coords=(827, 945),
    tp_gs_col_x_coords=(947, 1068),  # no longer accurate
    tp_gem_col_x_coords=(1068, 1203),
    tp_perk_col_x_coords=(0, 0),  # don't actually know
    tp_rarity_col_x_coords=(1436, 1619),
    tp_location_col_x_coords=(2013, 2265),
    first_item_listing_bbox=(1263, 666, 300, 105),
    mouse_scroll_loc=(3653, 657),
    menu_loc=(3738, 113),
    exit_to_desk_loc=(2648, 1436),
    yes_button_loc=(2195, 1296),
    resources_reset_loc=(255, 1194),
    sort_up_arrow=ImageReference(screen_bbox=(1974, 589, 25, 37), file_name="sort_up_arrow.png", min_conf=0.80),
    # --------Sold Orders ----------------
    sold_order_top_scroll=ImageReference(screen_bbox=(3561, 763, 51, 51), file_name="top_of_scroll.png", min_conf=0.95),
    sold_order_bottom_scroll=ImageReference(screen_bbox=(3570, 2013, 36, 21), file_name="sold_order_bottom_scroll.png", min_conf=0.70),
    sold_order_items_bbox=(1136, 785, 2402, 1064),
    sold_order_items_full_bbox=(1136, 785, 2424, 1218),
    sold_order_tp_name_col_x_coords=(0, 474),
    sold_order_tp_price_col_x_coords=(474, 659),
    sold_order_qty_col_x_coords=(659, 845),
    sold_order_sold_qty_col_x_coords=(845, 1029),
    sold_order_tp_gs_col_x_coords=(1029, 1215),
    sold_order_tp_gem_col_x_coords=(1215, 1400),
    sold_order_tp_perk_col_x_coords=(1400, 1586),
    sold_order_tp_status_col_x_coords=(1586, 1857),
    sold_order_tp_completion_time_col_x_coords=(1857, 2142),
    sold_order_completed_tab=(1250, 596),
    sold_order_sold_items_tab=(573, 836),
    sold_order_mouse_scroll_loc=(3555, 792),
    sold_order_price_sort_down=ImageReference(screen_bbox=(1623, 725, 25, 37), file_name="sold_order_price_sort_down.png", min_conf=0.70),
    # --------Buy Orders ----------------
    sell_tab_coords=(1131, 315),
    buy_order_all_items=(1478, 462),
    buy_order_top_scroll=ImageReference(screen_bbox=(3625, 745, 51, 51), file_name="top_of_scroll.png", min_conf=0.70),
    buy_order_mid_scroll=ImageReference(screen_bbox=(3632, 1792, 39, 39), file_name="mid_scroll_bottom.png", min_conf=0.70),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(3633, 1479, 37, 57), file_name="bottom_of_scroll_bottom.png", min_conf=0.70),
    buy_order_cancel_button=ImageReference(screen_bbox=(1451, 1690, 123, 33), file_name="cancel_btn.png", min_conf=0.70),
    buy_order_refresh_button=ImageReference(screen_bbox=(2336, 1418, 235, 34), file_name="refresh_btn.png", min_conf=0.70),
    buy_order_next_page_coords=(3569, 617),
    buy_order_pages_bbox=(3465, 597, 51, 29),
    buy_order_current_page_bbox=(3296, 597, 161, 32),
    buy_order_items_bbox=(1424, 762, 2202, 1071),
    buy_order_items_bbox_last=(1424, 1179, 2202, 918),
    buy_order_tp_row_height=384,
    buy_order_tp_name_col_x_coords=(0, 504),
    buy_order_tp_price_col_x_coords=(504, 822),
    buy_order_tp_tier_col_x_coords=(822, 998),
    buy_order_tp_gs_col_x_coords=(998, 1178),
    buy_order_tp_attri_col_x_coords=(1178, 1458),
    buy_order_tp_perk_col_x_coords=(1458, 1718),
    buy_order_tp_gem_col_x_coords=(1718, 1919),
    buy_order_tp_qty_col_x_coords=(1919, 2120),
    buy_order_first_item_listing_bbox=(1305, 774, 300, 105),
    buy_order_mouse_scroll_loc=(3618, 785),
    buy_order_all_items_tab=(1505, 467),
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(1974, 589, 25, 37), file_name="sort_up_arrow.png", min_conf=0.80),


    # ------------------------------------
    # False and True indicate if a resource reset is needed before starting this section
    # buy_order_adjustment=(30, 105),  # add this to the loc of the section below to get the loc for buy orders
    sections={
           'Raw Resources': ((552, 732), True),
           'Arcana': ((552, 852), True),
           'Potion Reagents': ((552, 953), True),
           'Cooking Ingredients': ((552, 1062), True),
           'Dye Ingredients': ((552, 1182), True),
           'Refined Resources': ((552, 1283), True),
           'Components': ((552, 1404), True),
           'Craft Mods': ((552, 1484), True),
           'Azoth': ((552, 1602), True),
           'Runeglass Components': ((552, 1710), True),
           'Consumables': ((248, 1350), False),
           'Ammunition': ((248, 1478), False),
           'House Furnishings': ((248, 1637), False),
           'Buy Orders': ((1131, 315), False),
           'Sold Items': ((1775, 311), False),
       },
    buy_order_sections={
            'Buy Order - Resources': ((300, 1352), False),
            'Buy Order - Consumables': ((293, 1508), False),
            'Buy Order - Ammunition': ((293, 1635), False),
            'Buy Order - House Furnishings': ((293, 1794), False),
    },
)

res_2560x1080p = Resolution(
    name="2560x1080",
    # trading_post=ImageReference(screen_bbox=(338, 31, 96, 24), file_name="trading_post_label.png", min_conf=0.80),
    # my_orders_clip_icon=ImageReference(screen_bbox=(792, 144, 15, 17), file_name="my_orders_clip_icon.png", min_conf=0.70),
    buy_icon=ImageReference(screen_bbox=(508, 143, 23, 17), file_name="buy_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(2153, 314, 18, 19), file_name="top_of_scroll.png", min_conf=0.80),
    mid_scroll=ImageReference(screen_bbox=(2153, 634, 18, 23), file_name="mid_scroll_bottom.png", min_conf=0.80),
    bottom_scroll=ImageReference(screen_bbox=(2155, 1031, 13, 19), file_name="bottom_of_scroll_bottom.png",
                                 min_conf=0.75),
    cancel_button=ImageReference(screen_bbox=(1041, 773, 63, 17), file_name="cancel_btn.png", min_conf=0.80),
    refresh_button=ImageReference(screen_bbox=(1483, 677, 120, 19), file_name="refresh_btn.png", min_conf=0.80),
    next_page_coords=(2122, 227),
    pages_bbox=(2068, 217, 30, 17),
    current_page_bbox=(1986, 219, 80, 16),
    items_bbox=(1011, 320, 1129, 696),
    items_bbox_last=(1011, 896, 1129, 153),
    tp_row_height=79 * 2.5,
    tp_name_col_x_coords=(0, 275),
    tp_price_col_x_coords=(275, 418),
    tp_avail_col_x_coords=(1000, 1083),
    tp_tier_col_x_coords=(418, 478),
    tp_gs_col_x_coords=(478, 539),
    tp_gem_col_x_coords=(539, 607),
    tp_perk_col_x_coords=(607, 724),
    tp_rarity_col_x_coords=(724, 815),
    tp_location_col_x_coords=(1012, 1125),
    first_item_listing_bbox=(1011, 316, 1129, 79),
    mouse_scroll_loc=(2146, 347),
    resources_reset_loc=(445, 602),
    menu_loc=(2189, 53),
    exit_to_desk_loc=(1645, 719),
    yes_button_loc=(1423, 649),
    sort_up_arrow=ImageReference(screen_bbox=(1307, 294, 13, 19), file_name="sort_up_arrow.png", min_conf=0.80),
    # --------Sold Orders ----------------
    sold_order_top_scroll=ImageReference(screen_bbox=(2105, 382, 34, 34), file_name="top_of_scroll.png", min_conf=0.95),
    sold_order_bottom_scroll=ImageReference(screen_bbox=(2105, 1007, 18, 11), file_name="sold_order_bottom_scroll.png",
                                            min_conf=0.70),
    sold_order_items_bbox=(888, 392, 1201, 532),
    sold_order_items_full_bbox=(888, 392, 1201, 609),
    sold_order_tp_name_col_x_coords=(0, 237),
    sold_order_tp_price_col_x_coords=(237, 329),
    sold_order_qty_col_x_coords=(329, 422),
    sold_order_sold_qty_col_x_coords=(422, 515),
    sold_order_tp_gs_col_x_coords=(515, 608),
    sold_order_tp_gem_col_x_coords=(608, 700),
    sold_order_tp_perk_col_x_coords=(700, 793),
    sold_order_tp_status_col_x_coords=(793, 929),
    sold_order_tp_completion_time_col_x_coords=(929, 1071),
    sold_order_completed_tab=(950, 296),
    sold_order_sold_items_tab=(607, 414),
    sold_order_mouse_scroll_loc=(2098, 396),
    sold_order_price_sort_down=ImageReference(screen_bbox=(1131, 362, 13, 19),
                                              file_name="sold_order_price_sort_down.png", min_conf=0.70),
    # --------Buy Orders ----------------
    sell_tab_coords=(886, 158),
    buy_order_all_items=(1059, 231),
    buy_order_top_scroll=ImageReference(screen_bbox=(2137, 373, 18, 19), file_name="top_of_scroll.png", min_conf=0.70),
    buy_order_mid_scroll=ImageReference(screen_bbox=(2137, 600, 18, 23), file_name="mid_scroll_bottom.png",
                                        min_conf=0.70),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(2137, 1034, 13, 19), file_name="buy_order_bottom_of_scroll.png",
                                           min_conf=0.70),
    buy_order_cancel_button=ImageReference(screen_bbox=(1044, 843, 63, 17), file_name="cancel_btn.png", min_conf=0.70),
    buy_order_refresh_button=ImageReference(screen_bbox=(1486, 707, 120, 19), file_name="refresh_btn.png",
                                            min_conf=0.70),
    buy_order_next_page_coords=(2104, 308),
    buy_order_pages_bbox=(2053, 299, 26, 14),
    buy_order_current_page_bbox=(1968, 299, 80, 16),
    buy_order_items_bbox=(1032, 381, 1101, 536),
    buy_order_items_bbox_last=(1032, 744, 1101, 305),
    buy_order_tp_row_height=79 * 2.5,
    buy_order_tp_name_col_x_coords=(0, 252),
    buy_order_tp_price_col_x_coords=(252, 411),
    buy_order_tp_tier_col_x_coords=(411, 499),
    buy_order_tp_gs_col_x_coords=(499, 589),
    buy_order_tp_attri_col_x_coords=(589, 729),
    buy_order_tp_perk_col_x_coords=(729, 862),
    buy_order_tp_gem_col_x_coords=(862, 959),
    buy_order_tp_qty_col_x_coords=(959, 1060),
    buy_order_first_item_listing_bbox=(653, 387, 150, 53),
    buy_order_mouse_scroll_loc=(2129, 392),
    buy_order_all_items_tab=(1072, 233),
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(1286, 353, 13, 19), file_name="sort_up_arrow.png",
                                             min_conf=0.80),

    # False and True indicate if a resource reset is needed before starting this section
    sections={

        'Raw Resources': ((569, 365), True),
        'Arcana': ((569, 424), True),
        'Potion Reagents': ((569, 475), True),
        'Cooking Ingredients': ((569, 532), True),
        'Dye Ingredients': ((569, 582), True),
        'Refined Resources': ((569, 638), True),
        'Components': ((569, 697), True),
        'Craft Mods': ((569, 746), True),
        'Azoth': ((569, 803), True),
        'Runeglass Components': ((569, 863), True),
        'Consumables': ((441, 673), False),
        'Ammunition': ((441, 740), False),
        'House Furnishings': ((441, 816), False),
        'Buy Orders': ((886, 156), False),
        'Sold Items': ((1205, 152), False)
    },
    buy_order_sections={
        'Buy Order - Resources': ((466, 676), False),
        'Buy Order - Consumables': ((466, 754), False),
        'Buy Order - Ammunition': ((466, 818), False),
        'Buy Order - House Furnishings': ((466, 897), False),
    },
)

res_1440p = Resolution(
    name="2560x1440",
    # trading_post=ImageReference(screen_bbox=(450, 32, 165, 64), file_name="trading_post_label.png", min_conf=0.80),
    # my_orders_clip_icon=ImageReference(screen_bbox=(1056, 192, 20, 22), file_name="my_orders_clip_icon.png", min_conf=0.70),
    buy_icon=ImageReference(screen_bbox=(249, 191, 30, 22), file_name="buy_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(2438, 418, 34, 34), file_name="top_of_scroll.png", min_conf=0.80),
    mid_scroll=ImageReference(screen_bbox=(2442, 1314, 27, 27), file_name="mid_scroll_bottom.png", min_conf=0.80),
    bottom_scroll=ImageReference(screen_bbox=(2443, 915, 25, 38), file_name="bottom_of_scroll_bottom.png", min_conf=0.75),
    cancel_button=ImageReference(screen_bbox=(961, 1032, 90, 30), file_name="cancel_btn.png", min_conf=0.80),
    refresh_button=ImageReference(screen_bbox=(1543, 900, 170, 40), file_name="refresh_btn.png", min_conf=0.80),
    next_page_coords=(2400, 300),
    pages_bbox=(2335, 293, 54, 17),
    current_page_bbox=(2221, 292, 107, 21),
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
    mouse_scroll_loc=(2431, 438),
    menu_loc=(2492, 75),
    exit_to_desk_loc=(1765, 957),
    yes_button_loc=(1463, 864),
    resources_reset_loc=(170, 796),
    sort_up_arrow=ImageReference(screen_bbox=(1316, 392, 17, 25), file_name="sort_up_arrow.png", min_conf=0.80),
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
    buy_order_top_scroll=ImageReference(screen_bbox=(2416, 497, 34, 34), file_name="top_of_scroll.png", min_conf=0.70),
    buy_order_mid_scroll=ImageReference(screen_bbox=(2421, 1196, 27, 27), file_name="mid_scroll_bottom.png", min_conf=0.70),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(2421, 987, 25, 38), file_name="bottom_of_scroll_bottom.png", min_conf=0.70),
    buy_order_cancel_button=ImageReference(screen_bbox=(967, 1127, 90, 30), file_name="cancel_btn.png", min_conf=0.80),
    buy_order_refresh_button=ImageReference(screen_bbox=(1558, 946, 170, 40), file_name="refresh_btn.png", min_conf=0.80),
    buy_order_next_page_coords=(2379, 411),
    buy_order_pages_bbox=(2310, 398, 34, 19),
    buy_order_current_page_bbox=(2197, 398, 107, 21),
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
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(1288, 471, 17, 25), file_name="sort_up_arrow.png", min_conf=0.80),


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
    name="1920x1080",
    # trading_post=ImageReference(screen_bbox=(338, 31, 96, 24), file_name="trading_post_label.png", min_conf=0.80),
    # my_orders_clip_icon=ImageReference(screen_bbox=(792, 144, 15, 17), file_name="my_orders_clip_icon.png", min_conf=0.70),
    buy_icon=ImageReference(screen_bbox=(187, 143, 23, 17), file_name="buy_icon.png", min_conf=0.70),
    top_scroll=ImageReference(screen_bbox=(1833, 314, 18, 19), file_name="top_of_scroll.png", min_conf=0.70),
    mid_scroll=ImageReference(screen_bbox=(1833, 634, 18, 23), file_name="mid_scroll_bottom.png", min_conf=0.80),
    bottom_scroll=ImageReference(screen_bbox=(1835, 1031, 13, 19), file_name="bottom_of_scroll_bottom.png", min_conf=0.70),
    cancel_button=ImageReference(screen_bbox=(720, 772, 63, 17), file_name="cancel_btn.png", min_conf=0.70),
    refresh_button=ImageReference(screen_bbox=(1163, 676, 120, 19), file_name="refresh_btn.png", min_conf=0.70),
    next_page_coords=(1802, 227),
    pages_bbox=(1748, 217, 30, 17),
    current_page_bbox=(1666, 219, 80, 16),
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
    exit_to_desk_loc=(1325, 719),
    yes_button_loc=(1103, 649),
    sort_up_arrow=ImageReference(screen_bbox=(987, 294, 13, 19), file_name="sort_up_arrow.png", min_conf=0.80),
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
    buy_order_top_scroll=ImageReference(screen_bbox=(1817, 373, 18, 19), file_name="top_of_scroll.png", min_conf=0.70),
    buy_order_mid_scroll=ImageReference(screen_bbox=(1817, 600, 18, 23), file_name="mid_scroll_bottom.png",
                                        min_conf=0.70),
    buy_order_bottom_scroll=ImageReference(screen_bbox=(1817, 1034, 13, 19), file_name="buy_order_bottom_of_scroll.png",
                                           min_conf=0.70),
    buy_order_cancel_button=ImageReference(screen_bbox=(723, 842, 63, 17), file_name="cancel_btn.png", min_conf=0.80),
    buy_order_refresh_button=ImageReference(screen_bbox=(1166, 706, 120, 19), file_name="refresh_btn.png",
                                            min_conf=0.80),
    buy_order_next_page_coords=(1784, 308),
    buy_order_pages_bbox=(1733, 299, 26, 14),
    buy_order_current_page_bbox=(1648, 299, 80, 16),
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
    buy_order_sort_down_arrow=ImageReference(screen_bbox=(966, 353, 13, 19), file_name="sort_up_arrow.png", min_conf=0.80),

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
    "1920x1080": res_1080p,
    "2560x1440": res_1440p,
    "2560x1080": res_2560x1080p,
    "3840x2160": res_4k
}


def get_resolution_obj():
    from app.settings import SETTINGS  # circular
    return resolutions[SETTINGS.resolution]
