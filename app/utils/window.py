import win32gui, win32con
import re


class Window:
    def __init__(self):
        self._hwnd = None

    def BringToTop(self):
        win32gui.BringWindowToTop(self._hwnd)

    def SetAsForegroundWindow(self):
        win32gui.SetForegroundWindow(self._hwnd)

    def Maximize(self):
        win32gui.ShowWindow(self._hwnd, win32con.SW_MAXIMIZE)

    def setActWin(self):
        win32gui.SetActiveWindow(self._hwnd)

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._hwnd = hwnd

    def find_window_wildcard(self, wildcard):
        self._hwnd = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)


def bring_new_world_to_foreground() -> None:
    wildcard = "^New World$"
    cw = Window()
    cw.find_window_wildcard(wildcard)
    cw.BringToTop()
    cw.SetAsForegroundWindow()



def exit_to_desktop() -> None:
    from app.ocr.resolution_settings import get_resolution_obj
    from app.utils.keyboard import press_key
    import pynput
    from app.utils.mouse import click, mouse
    import time
    resolution = get_resolution_obj()
    press_key(pynput.keyboard.Key.esc)
    time.sleep(2)
    press_key(pynput.keyboard.Key.esc)
    time.sleep(2)
    click('left', resolution.menu_loc)
    time.sleep(2)
    click('left', resolution.exit_to_desk_loc)
    time.sleep(2)
    click('left', resolution.yes_button_loc)



