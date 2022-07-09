from app.ocr.resolution_settings import res_1440p, res_2160p
from test.utils import get_resource
import cv2

lgreen = (36, 255, 12)


def draw(img, label, coords):
    if len(coords) == 2:
        return draw_point(img, label, coords)
    return draw_box(img, label, coords)


def draw_point(img, label, coords):
    img = cv2.circle(img, coords, radius=1, color=lgreen, thickness=1)
    x, y = coords
    img = cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, lgreen, 1)
    return img


def draw_box(img, label, coords):
    t, l, w, h = coords
    img = cv2.rectangle(img, (t, l), (t+w, l+h), lgreen, 1)
    img = cv2.putText(img, label, (t, l - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, lgreen, 1)
    return img


def draw_resolution(res, img):
    for section, coords in res.sections.items():
        img = draw(img, section, coords)

    draw(img, 'trading_post', res.trading_post.screen_bbox)
    draw(img, 'top_scroll', res.top_scroll.screen_bbox)
    draw(img, 'mid_scroll', res.mid_scroll.screen_bbox)
    draw(img, 'bottom_scroll', res.bottom_scroll.screen_bbox)
    draw(img, 'pages', res.pages_bbox)
    draw(img, 'items', res.items_bbox)
    draw(img, 'items last', res.items_bbox_last)

    draw(img, 'namex', res.tp_name_col_x_coords)
    draw(img, 'pricex', res.tp_price_col_x_coords)
    draw(img, 'availx', res.tp_avail_col_x_coords)

    draw(img, 'items first', res.first_item_listing_bbox)
    draw(img, 'scroll loc', res.mouse_scroll_loc)
    return img


def draw_1440():
    s_path = get_resource('trading_2k.jpg')
    img = cv2.imread(s_path)

    img = draw_resolution(res_1440p, img)

    cv2.imshow('1440', img)
    cv2.waitKey(0)


def draw_2160():
    s_path = get_resource('trading_4k.jpg')
    img = cv2.imread(s_path)

    img = draw_resolution(res_2160p, img)
    img = cv2.resize(img, (2560, 1440), cv2.INTER_AREA)  # make it viewable

    cv2.imshow('2160', img)
    cv2.waitKey(0)


if __name__ == '__main__':
    #draw_1440()
    draw_2160()
