import PySimpleGUI as sg

from app import events
from app.overlay.layouts.key_settings_layout import settings_layout
from app.overlay.layouts.login_layout import LOGIN_LAYOUT
from app.overlay.layouts.scan_info_layout import scan_info_layout
from app.settings import SETTINGS
from app.utils import resource_path


class Overlay:
    def __init__(self):
        self.spinner_step = 0  # set to -1 to hide
        self._show_spinner = True
        self.server_version: str = None
        self.download_link: str = None
        layout1 = LOGIN_LAYOUT

        layout3 = scan_info_layout()

        version_update_layout = [
            [sg.Text('', key='download_update_text')],
            [
                sg.Button('Update Now', key=events.BEGIN_DOWNLOAD_UPDATE, enable_events=True),
                sg.Image(size=(30, 30), key='-LOADING-IMAGE-2-', source=resource_path("app/images/spinner/0.png")),
            ],
        ]

        layout = [
            [
                sg.Column(layout1, key='login_window'),
                sg.Column(layout3, visible=False, key='main_window'),
                sg.Column(version_update_layout, visible=False, key='update_window')
            ]
        ]
        # layout = [[sg.Column(layout1, key='login_window'), sg.Column(layout2, visible=False, key='main_window'), sg.Column(layout3, visible=False, key='advanced_window')]]

        # Create the main window
        self.window = sg.Window(
            f'Trade Price Scraper - {SETTINGS.VERSION}',
            layout,
            keep_on_top=False,
            location=(150, 150),
            finalize=True,
            use_default_focus=False,
            background_color='red' if SETTINGS.use_dev_colors else None,
        )

    def read(self):
        event, values = self.window.read(timeout=0)
        return event, values

    def updatetext(self, element, val, size=None, append=None):
        if isinstance(val, list):
            self.window[element].Update(values=val, set_to_index=0)

        else:
            if append:
                val = str(val) + '\n'
                self.window[element].Update(value=val, append=True, autoscroll=True)
            else:
                self.window[element].Update(value=val)

        if isinstance(size, tuple):
            self.window[element].set_size(size=(size, 1))

    def disable(self, element):
        self.window[element].update(disabled=True)

    def enable(self, element):
        self.window[element].update(disabled=False)

    def hide(self, element):
        self.window[element].update(visible=False)

    def unhide(self, element):
        self.window[element].update(visible=True)

    def show_main(self):
        self.window['login_window'].update(visible=False)
        self.window['main_window'].update(visible=True)

    def show_login(self):
        self.window['main_window'].update(visible=False)
        self.window['login_window'].update(visible=True)

    def show_update_window(self):
        # these is no backing out of update window.
        self.window['main_window'].update(visible=False)
        self.window['login_window'].update(visible=False)
        self.window['update_window'].update(visible=True)
        my_version = SETTINGS.VERSION
        self.window['download_update_text'].update(
            f"Your version is out of date.\n\nThe latest version is {self.server_version}, you have {my_version}"
        )

    def add_names(self, element, vals, size=None):
        self.window[element].update(values=vals, set_to_index=1, size=(35, 6))
        if size:
            self.window[element].set_size(size=(size, 6))

    @property
    def spinner(self) -> sg.Image:
        which_spinner = "-LOADING-IMAGE-" if self.window["login_window"].visible else "-LOADING-IMAGE-2-"
        return self.window.find_element(which_spinner)

    def version_check_complete(self, version_info: dict) -> None:
        self.set_spinner_visibility(False)
        version = version_info["version"]
        self.download_link = version_info["download_link"]
        self.server_version = version
        login = self.window.find_element(events.LOGIN_BUTTON)
        login.update("Login", disabled=False)

    def set_spinner_visibility(self, show=True) -> None:
        self._show_spinner = show
        self.spinner.update(visible=show)

    def perform_cycle_updates(self) -> None:
        self.update_spinner()

    def update_spinner(self) -> None:
        if not self._show_spinner:
            return
        real_step = int(self.spinner_step / 10)
        if self.spinner_step % 1 == 0:
            self.spinner.update(resource_path(f"app/images/spinner/{real_step}.png"))
        self.spinner_step += 1
        if self.spinner_step > 470:
            self.spinner_step = 0

    def popup_window(self, layout):
        x, y = self.window.current_location(more_accurate=True)
        width, height = self.window.size
        window = sg.Window(
            "Settings",
            layout,
            use_default_focus=False,
            finalize=True,
            modal=True,
            grab_anywhere=True,
            no_titlebar=True,
            border_depth=2,
        )
        middle_x = int(x + width / 2 - window.size[0] / 2)
        middle_y = int(y + height / 2 - window.size[1] / 2)
        window.move(middle_x, middle_y)
        self.window.set_alpha(0.6)

        event, values = window.read()
        self.window.write_event_value(event, values)
        window.close()

        return values


overlay = Overlay()
