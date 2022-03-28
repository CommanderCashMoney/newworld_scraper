import cv2
import numpy as np
import mss


def grab_screen(region=None):

    left, top, width, height = region
    mon = {"top": top, "left": left, "width": width, "height": height}

    sct = mss.mss()
    g = sct.grab(mon)
    img = np.asarray(g)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

    return img


def adjust_pil_img(pil_img):
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

    return img
