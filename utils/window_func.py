import win32gui, win32con
import re, traceback
from time import sleep

class cWindow:
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
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) != None:
            self._hwnd = hwnd


    def find_window_wildcard(self, wildcard):
        self._hwnd = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)


# def main():
#     sleep(2)
#
#     wildcard = "^New World$"
#     cW = cWindow()
#     cW.find_window_wildcard(wildcard)
#     # cW.Maximize()
#     cW.BringToTop()
#     cW.SetAsForegroundWindow()
#
# main()