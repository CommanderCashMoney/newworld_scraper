from typing import Any, Callable, Tuple

import pynput
import time

from app.ocr.utils import capture_screen, screenshot_bbox
from app.utils.mouse import mouse
from app.utils.resolution import get_resolution

IS_WAITING_FOR_PRESS = False
PRESSED = False
RESOLUTION = None


def key_pressed(key):
    global IS_WAITING_FOR_PRESS
    code = getattr(key, 'vk', None)
    if not code:
        return
    if IS_WAITING_FOR_PRESS and code == 109:  # numpad -
        global PRESSED
        PRESSED = True


listener = pynput.keyboard.Listener(on_press=key_pressed)
listener.start()
width, height = get_resolution()


def wait_for_key_press() -> None:
    global IS_WAITING_FOR_PRESS, PRESSED
    IS_WAITING_FOR_PRESS = True
    while not PRESSED:
        continue
    IS_WAITING_FOR_PRESS = False
    PRESSED = False


def ask_with_callback(callback: Callable, description: str, *callback_args, **callback_kwargs) -> Any:
    print(description)
    wait_for_key_press()
    return callback(*callback_args, **callback_kwargs)


def get_mouse_pos() -> Tuple[int, int]:
    return mouse.position


def ask_for_area(for_area: str, capture=True) -> Tuple[Tuple[int, int, int, int], Any]:
    pos1 = ask_with_callback(get_mouse_pos, f"Please hover top left of {for_area} and press Numpad -")
    pos2 = ask_with_callback(get_mouse_pos, f"Please hover bottom right of {for_area} and press Numpad -")
    # left, top, width, height
    print(f"one {pos1} two {pos2}")
    region = pos1[0], pos1[1], pos2[0] - pos1[0], pos2[1] - pos1[1]

    # top, left
    # (2233, 287, 140, 32)
    if capture:
        return region, screenshot_bbox(*region)
    return region, None


def request_crop_of(file_name: str, descriptor: str = None, move_and_wait=False, capture=True) -> Tuple[int, int, int, int]:
    if descriptor is None:
        descriptor = file_name

    base = f"app/images/new_world/{RESOLUTION}"

    area, screenshot = ask_for_area(descriptor, capture=capture)
    if move_and_wait:
        #print("Please move your mouse away from the area so nothing is highlighted, then press -")
        old_pos = get_mouse_pos()
        #wait_for_key_press()
        mouse.position = (width-1, height-1)
        time.sleep(0.1)
        screenshot = screenshot_bbox(*area)
        mouse.position = old_pos
    image = screenshot.get_image(pil_high_quality=True)

    if capture:
        image.show()
        image.save(f"{base}/{file_name}")
    return area


def ask_for_location(descriptor: str) -> Tuple[int, int]:
    pos = ask_with_callback(get_mouse_pos, f"Please move your mouse to {descriptor}")
    return pos


def get_absolute_left_and_right_column_coords(descriptor: str, pg_bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
    point1 = ask_for_location(f"Please move your mouse to the left of the {descriptor} column")
    point2 = ask_for_location(f"Please move your mouse to the right of the {descriptor} column")
    return max(point1[0], pg_bbox[0]), min(point2[0], pg_bbox[0])

RESOLUTION = "2160p"# input("Enter resolution to be captured: ")


trading_post = request_crop_of("trading_post_label.png", "Trading Post Label")
top_scroll = request_crop_of("top_of_scroll.png", "Top of Scroll", move_and_wait=True)
mid_scroll = request_crop_of("mid_scroll_bottom.png", "Mid Scroll Bottom", move_and_wait=True)
bottom_scroll = request_crop_of("bottom_of_scroll_bottom.png", "Bottom Scroll Bottom", move_and_wait=True)
cancel_button = request_crop_of("cancel_btn.png", "Cancel Button", move_and_wait=True)
refresh_button = request_crop_of("refresh_btn.png", "Refresh Button", move_and_wait=True)
next_page_coords = ask_for_location("Next page coordinates")
mouse_scroll_loc = ask_for_location("An area where you can scroll but are not highlighting the scroll bar")


pages_bbox, _ = ask_for_area("The bounding box of the number of pages", capture=False)

items_bbox, _ = ask_for_area("The bounding box of a full page of listings", capture=False)
items_bbox = (items_bbox[0], pages_bbox[1], items_bbox[2], pages_bbox[3])
items_bbox_last, _ = ask_for_area("The bounding box of the last 2 listings", capture=False)
items_bbox_last = (items_bbox[0], pages_bbox[1], items_bbox[2], pages_bbox[3])
first_item_listing_bbox, _ = ask_for_area("The bounding box of the FIRST listing", capture=False)
items_bbox_last = (items_bbox[0], pages_bbox[1], items_bbox[2], pages_bbox[3])

template = "The start and end of the {} column.".format

# region = left, top, width, height
tp_name_col_x_coords = get_absolute_left_and_right_column_coords("name", pages_bbox)
tp_price_col_x_coords = get_absolute_left_and_right_column_coords("price", pages_bbox)
tp_avail_col_x_coords = get_absolute_left_and_right_column_coords("avail", pages_bbox)
tp_tier_col_x_coords = get_absolute_left_and_right_column_coords("tier", pages_bbox)
tp_gs_col_x_coords = get_absolute_left_and_right_column_coords("gs", pages_bbox)
tp_gem_col_x_coords = get_absolute_left_and_right_column_coords("gem", pages_bbox)
tp_perk_col_x_coords = get_absolute_left_and_right_column_coords("perk", pages_bbox)
tp_rarity_col_x_coords = get_absolute_left_and_right_column_coords("rarity", pages_bbox)
tp_location_col_x_coords = get_absolute_left_and_right_column_coords("location", pages_bbox)

resources = ask_for_location("resources")
raw_resources = ask_for_location("raw_resources")
refined_resources = ask_for_location("refined_resources")
cooking_ingredients = ask_for_location("cooking_ingredients")
craft_mods = ask_for_location("craft_mods")
components = ask_for_location("components")
potion_reagents = ask_for_location("potion_reagents")
dyes = ask_for_location("dyes")
azoth = ask_for_location("azoth")
arcana = ask_for_location("arcana")
consumables = ask_for_location("consumables")
ammo = ask_for_location("ammo")
house_furnishings = ask_for_location("house_furnishings")


print(f"""
res_{RESOLUTION} = Resolution(
    name="{RESOLUTION}",
    trading_post=ImageReference(screen_bbox={trading_post}, file_name="trading_post_label.png", min_conf=0.92),
    top_scroll=ImageReference(screen_bbox={top_scroll}, file_name="top_of_scroll.png", min_conf=0.95),
    mid_scroll=ImageReference(screen_bbox={mid_scroll}, file_name="mid_scroll_bottom.png", min_conf=0.95),
    bottom_scroll=ImageReference(screen_bbox={bottom_scroll}, file_name="bottom_of_scroll_bottom.png", min_conf=0.95),
    cancel_button=ImageReference(screen_bbox={cancel_button}, file_name="cancel_btn.png", min_conf=0.95),
    refresh_button=ImageReference(screen_bbox={refresh_button}, file_name="refresh_btn.png", min_conf=0.95),
    next_page_coords={next_page_coords},
    pages_bbox={pages_bbox},
    items_bbox={items_bbox},
    items_bbox_last={items_bbox_last},
    tp_row_height=manuallychangeme,
    tp_name_col_x_coords={tp_name_col_x_coords},
    tp_price_col_x_coords={tp_price_col_x_coords},
    tp_avail_col_x_coords={tp_avail_col_x_coords},
    tp_tier_col_x_coords={tp_tier_col_x_coords},
    tp_gs_col_x_coords={tp_gs_col_x_coords},
    tp_gem_col_x_coords={tp_gem_col_x_coords},
    tp_perk_col_x_coords={tp_perk_col_x_coords},
    tp_rarity_col_x_coords={tp_rarity_col_x_coords},
    tp_location_col_x_coords={tp_location_col_x_coords},
    first_item_listing_bbox={first_item_listing_bbox},
    mouse_scroll_loc={mouse_scroll_loc},
    sections={{
           'Resources Reset 0': {resources},
           'Raw Resources': {raw_resources},
           'Resources Reset 1': {resources},
           'Refined Resources': {refined_resources},
           'Resources Reset 2': {resources},
           'Cooking Ingredients': {cooking_ingredients},
           'Resources Reset 3': {resources},
           'Craft Mods': {craft_mods},
           'Resources Reset 4': {resources},
           'Components': {components},
           'Resources Reset 5': {resources},
           'Potion Reagents': {potion_reagents},
           'Resources Reset 6': {resources},
           'Dyes': {dyes},
           'Resources Reset 7': {resources},
           'Azoth': {azoth},
           'Resources Reset 8': {resources},
           'Arcana': {arcana},
           'Consumables': {consumables},
           'Ammunition': {ammo},
           'House Furnishings': {house_furnishings}
    }}
)
""")
