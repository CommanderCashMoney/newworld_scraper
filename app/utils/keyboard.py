import time

import pynput


def press_key(key, hold=0.0):
    kb = pynput.keyboard.Controller()
    kb.press(key)
    time.sleep(hold)
    kb.release(key)
