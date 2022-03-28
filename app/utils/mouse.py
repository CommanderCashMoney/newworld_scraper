import time

import pynput

mouse = pynput.mouse.Controller()
screen_center = (1200, 700)  # todo: dynamic


def click(btn, pos=screen_center, hold=0):
    if btn == "left":
        btn = pynput.mouse.Button.left
    else:
        btn = pynput.mouse.Button.right
    mouse.position = pos
    time.sleep(0.1)
    mouse.press(btn)
    time.sleep(hold)
    mouse.release(btn)
