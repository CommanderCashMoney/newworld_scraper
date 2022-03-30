import PySimpleGUI as sg
from os import path
from settings import SETTINGS
from utils import resource_path
import json


class Overlay():
    SETTINGS_FILE = path.join(path.dirname(__file__), r'settings_file.cfg')
    DEFAULT_SETTINGS = {'un': '', 'action_key': 'e', 'forward_key': 'w', 'backward_key': 's'}

    def __init__(self):
        self.spinner_step = 0  # set to -1 to hide
        self._show_spinner = True
        self.server_version: str = None
        self.download_link: str = None
        is_dev = SETTINGS.is_dev
        saved_settings = self.load_settings()

        layout1 = [
            [
                sg.Text('Trade Scraper', key="title"), sg.Text('Env?', visible=is_dev),
                sg.Radio('Prod', group_id='4', key='prod', default=not is_dev, visible=is_dev),
                sg.Radio('Dev', group_id='4', key='dev', default=is_dev, visible=is_dev)
            ],
            [
                sg.Text('User Name: ', key="un_text"),
                sg.InputText(key='un', size=(25, 1), default_text=SETTINGS.api_username)
            ],
            [
                sg.Text('Password:   ', key="pw_text"),
                sg.InputText(key='pw', size=(25, 1), password_char='*', default_text=SETTINGS.api_password)
            ],
            [
                sg.Button('Checking Version', key='login', size=(15, 1), bind_return_key=True, disabled=True),
                sg.Text('', key='login_status'),
                sg.Image(size=(30, 30), key='-LOADING-IMAGE-', source=resource_path("images/spinner/0.png")),
            ],
        ]

        layout3 = [[
            sg.Text('Trade Scraper')],
            [sg.Button('Start Scan',  size=(15, 1), key='Run'), sg.Text('Test Run?'),
             sg.Radio('Y', group_id='1', key='test_t', default=True), sg.Radio('N', group_id='1', key='test_f')],
            [sg.Text('_' * 60)],
            [sg.Frame(title='Advanced', key='advanced', layout=[[
                sg.Text('Pages'), sg.InputText(key='pages', size=(4, 1)),
                sg.Text('Sections?'),
                sg.Radio('Auto', group_id='2', key='sections_auto', default=True),
                sg.Radio('Manual', group_id='2', key='sections_manual'),
                sg.Text('Server: '),
                sg.Combo([0], size=(2, 1), key='server_select', enable_events=True,
                         readonly=True)

            ]], visible=False)],
            [sg.Text('Status: '), sg.Text('Ready', key='status_bar', auto_size_text=True)],
            [sg.Text('Elapsed Time: '), sg.Text('', key='elapsed', auto_size_text=True), sg.Text('Pages left in section: '), sg.Text('', key='pages_left', auto_size_text=True)],
            [sg.Text('Images captured: '), sg.Text('0', key='key_count', auto_size_text=True), sg.Text('Images left to parse: '), sg.Text('0', key='ocr_count', auto_size_text=True)],
            [sg.Text('Accuracy: '), sg.Text('0%', key='accuracy', auto_size_text=True), sg.Text('Listings processed: '), sg.Text('0', key='listings_count', auto_size_text=True)],
            [sg.Text('Price fails: '), sg.Text('0', key='p_fails', auto_size_text=True), sg.Text('Data Rejects: '), sg.Text('0', key='rejects', auto_size_text=True)],

            [sg.Text('_' * 60)],
            [sg.Text('Logs:')],
            [sg.Multiline(key='log_output', size=(60,10), auto_refresh=True)],
            [sg.Text('Errors:')],
            [sg.Multiline(key='error_output', size=(60,5), auto_refresh=True)],
            [sg.Button('Resend data', key='resend', visible=False), sg.In(size=(25,1), enable_events=True ,key='-FOLDER-', visible=False), sg.FolderBrowse(button_text='Download Data'), sg.Button('Change key binds', key='keybinds')],
            [sg.Frame(title='Confirm item names', key='confirm', visible=False, layout=[
                [sg.InputText('', key='bad_name_0', size=(35, 1)), sg.Combo(['Add new'], key='good_name_0', enable_events=True, readonly=True), sg.Button('Add', key='add0', disabled=True)],
                [sg.InputText('', key='bad_name_1', size=(35, 1)), sg.Combo(['Add new'], key='good_name_1', enable_events=True, readonly=True), sg.Button('Add', key='add1', disabled=True)],
                [sg.InputText('', key='bad_name_2', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_2', enable_events=True, readonly=True),
                 sg.Button('Add', key='add2', disabled=True)],
                [sg.InputText('', key='bad_name_3', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_3', enable_events=True, readonly=True),
                 sg.Button('Add', key='add3', disabled=True)],
                [sg.InputText('', key='bad_name_4', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_4', enable_events=True, readonly=True),
                 sg.Button('Add', key='add4', disabled=True)],
                [sg.InputText('', key='bad_name_5', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_5', enable_events=True, readonly=True),
                 sg.Button('Add', key='add5', disabled=True)],
                [sg.InputText('', key='bad_name_6', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_6', enable_events=True, readonly=True),
                 sg.Button('Add', key='add6', disabled=True)],
                [sg.InputText('', key='bad_name_7', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_7', enable_events=True, readonly=True),
                 sg.Button('Add', key='add7', disabled=True)],
                [sg.InputText('', key='bad_name_8', size=(35, 1)),
                 sg.Combo(['Add new'], key='good_name_8', enable_events=True, readonly=True),
                 sg.Button('Add', key='add8', disabled=True)],
                [sg.InputText('', key='bad_name_9', size=(35, 1)), sg.Combo(['Add new'], key='good_name_9', enable_events=True, readonly=True), sg.Button('Add', key='add9', disabled=True)],
                [sg.Button('Load next set', key='next_btn')]

            ])]
        ]

        version_update_layout = [
            [sg.Text('', key='download_update_text')],
            [
                sg.Button('Update Now', key='download_update'),
                sg.Image(size=(30, 30), key='-LOADING-IMAGE-2-', source=resource_path("images/spinner/0.png")),
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
            location=(0, 0),
            finalize=True,
            use_default_focus=False
        )
        for key in saved_settings:
            if key in self.window.AllKeysDict:
                self.window[key].update(value=saved_settings[key])


    def save_settings(self, new_settings: dict):
        saved_settings = self.load_settings()
        saved_settings.update(new_settings)

        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(saved_settings, f)

    def load_settings(self) -> dict:
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                saved_settings = json.load(f)
                # if settings['action_key'] == '':
                #     settings['action_key'] = 'e'
        except FileNotFoundError as e:
            print(f'Overlay settings not found. Using defaults - {e}')
            saved_settings = self.DEFAULT_SETTINGS
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(saved_settings, f)
        return saved_settings

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

        if size:
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

    def show_advanced(self):
        self.window['advanced'].update(visible=True)

    def show_confirm(self):
        self.window['confirm'].update(visible=True)

    def hide_confirm(self):
        self.window['confirm'].update(visible=False)

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
        login = self.window.find_element("login")
        login.update("Login", disabled=False)

    def set_spinner_visibility(self, show=True) -> None:
        self._show_spinner = show
        self.spinner.update(visible=show)

    def update_spinner(self) -> None:
        if not self._show_spinner:
            return
        real_step = int(self.spinner_step / 10)
        if self.spinner_step % 1 == 0:
            self.spinner.update(resource_path(f"images/spinner/{real_step}.png"))
        self.spinner_step += 1
        if self.spinner_step > 470:
            self.spinner_step = 0

    def popup_keybinds(self, saved_settings):
        keybinds_layout = [
            [

                [sg.Text('Action Key', auto_size_text=True), sg.InputText(key='action_key', size=(2, 1))],
                [sg.Text('Move Forward', auto_size_text=True), sg.InputText(key='forward_key', size=(2, 1))],
                [sg.Text('Move Backward', auto_size_text=True), sg.InputText(key='backward_key', size=(2, 1))],
                [sg.Button('Save')]

            ],

        ]

        popup_loc = tuple(map(sum, zip(self.window.CurrentLocation(), (300, 650))))
        window = sg.Window("Change key bindings", keybinds_layout, use_default_focus=False, finalize=True, modal=True, location=popup_loc)


        for key in saved_settings:
            if key in window.AllKeysDict:
                window[key].update(value=saved_settings[key])
        event, values = window.read()
        window.close()

        return values

overlay = Overlay()

