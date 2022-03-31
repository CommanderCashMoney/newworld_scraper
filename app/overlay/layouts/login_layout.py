import PySimpleGUI as sg

from app import events
from app.utils import resource_path
from app.settings import SETTINGS

is_dev = SETTINGS.is_dev
LOGIN_LAYOUT = [
    [
        sg.Text('Trade Scraper', key="title"), sg.Text('Env?', visible=is_dev),
        sg.Radio('Prod', group_id='4', key='prod', default=not is_dev, visible=is_dev),
        sg.Radio('Dev', group_id='4', key='dev', default=is_dev, visible=is_dev)
    ],
    [
        sg.Text('User Name: ', key="un_text"),
        sg.InputText(key=events.USERNAME_INPUT, size=(25, 1), default_text=SETTINGS.api_username,
                     enable_events=True)
    ],
    [
        sg.Text('Password:   ', key="pw_text"),
        sg.InputText(
            key=events.PASSWORD_INPUT,
            size=(25, 1),
            password_char='*',
            default_text=SETTINGS.api_password,
            enable_events=True
        )
    ],
    [
        sg.Button('Checking Version', key=events.LOGIN_BUTTON, size=(15, 1), bind_return_key=True,
                  disabled=True),
        sg.Text('', key='login_status'),
        sg.Image(size=(30, 30), key='-LOADING-IMAGE-', source=resource_path("app/images/spinner/0.png")),
    ],
]