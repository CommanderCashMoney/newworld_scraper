from app.ocr.resolution_settings import res_1440p, res_2160p
from test.utils import get_resource
import cv2

lgreen = (36, 255, 12)
red = (0,0,255)


def draw(img, label, coords, offset='top', shift=0, color=lgreen):
    if len(coords) == 2:
        return draw_point(img, label, coords, offset, shift, color)
    return draw_box(img, label, coords, offset, shift, color)


def draw_point(img, label, coords, offset='top', shift=0, color=lgreen):
    img = cv2.circle(img, coords, radius=1, color=color, thickness=1)
    x, y = coords
    o = y-shift if offset == 'top' else y+shift
    img = cv2.putText(img, label, (x, o), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return img


def draw_box(img, label, coords, offset='top', shift=0, color=lgreen):
    if shift > 0:
        t, l, w, h = coords[0]+shift, coords[1]+shift, coords[2]-shift, coords[3]-shift
    else:
        t, l, w, h = coords
    img = cv2.rectangle(img, (t, l), (t+w, l+h), color, 1)
    o = l-shift if offset == 'top' else l+shift
    img = cv2.putText(img, label, (t, o), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return img


def draw_resolution(res, img):
    for section, coords in res.sections.items():
        img = draw(img, section, coords)

    draw(img, 'trading_post', res.trading_post.screen_bbox)
    draw(img, 'top_scroll', res.top_scroll.screen_bbox)
    draw(img, 'mid_scroll', res.mid_scroll.screen_bbox)
    draw(img, 'bottom_scroll', res.bottom_scroll.screen_bbox)
    draw(img, 'pages', res.pages_bbox)
    print(f"Drawing items {res.items_bbox}")
    draw(img, 'items', res.items_bbox, color=red)
    draw(img, 'items last', res.items_bbox_last)


    # have to draw items WITHIN the 'items' bbox
    def transform_coords(coords):
        #turn l,r into a rect
        sp_x, sp_y, ep_x, ep_y = res.items_bbox
        l_start, l_end = coords
        coords = sp_x+l_start, sp_y, l_end, ep_y
        return coords

    # attempt a row height guess
    l = res.first_item_listing_bbox[0]
    rh = int(res.items_bbox[1]/9)
    t = int(res.items_bbox[1]+rh+(rh/2))
    h = res.tp_row_height
    w = 200 # arbitrary
    draw(img, 'row height', (l, t, w, h))

    draw(img, 'name col', transform_coords(res.tp_name_col_x_coords), 'bottom', shift=3)
    draw(img, 'price col', transform_coords(res.tp_price_col_x_coords), 'bottom', shift=3)
    draw(img, 'avail col', transform_coords(res.tp_avail_col_x_coords), 'bottom', shift=3)
    draw(img, 'tier col', transform_coords(res.tp_tier_col_x_coords), 'bottom', shift=3)
    draw(img, 'gs col', transform_coords(res.tp_gs_col_x_coords), 'bottom', shift=3)
    draw(img, 'gem col', transform_coords(res.tp_gem_col_x_coords), 'bottom', shift=3)
    draw(img, 'perk col', transform_coords(res.tp_perk_col_x_coords), 'bottom', shift=3)
    draw(img, 'rarity col', transform_coords(res.tp_rarity_col_x_coords), 'bottom', shift=3)
    draw(img, 'loc col', transform_coords(res.tp_location_col_x_coords), 'bottom', shift=3)
    #draw_column(img, 'pricex', *res.tp_price_col_x_coords)
    #draw_column(img, 'availx', *res.tp_avail_col_x_coords)

    draw(img, 'items first', res.first_item_listing_bbox)
    draw(img, 'scroll loc', res.mouse_scroll_loc)
    return img


def draw_1440():
    s_path = get_resource('trading_2k.jpg')
    img = cv2.imread(s_path)

    img = draw_resolution(res_1440p, img)

    cv2.imshow('1440', img)


def draw_2160():
    s_path = get_resource('trading_4k-new.jpg')
    img = cv2.imread(s_path)

    img = draw_resolution(res_2160p, img)
    img = cv2.resize(img, (2560, 1440), cv2.INTER_AREA)  # make it viewable

    cv2.imshow('2160', img)


if __name__ == '__main__':
    print("This tool is for visually sanity checking your bounds")
    #draw_1440()
    draw_2160()
    cv2.waitKey(0)
