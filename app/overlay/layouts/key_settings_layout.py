import PySimpleGUI as sg

from app import events
from app.settings import SETTINGS


def settings_layout():
    return [
        [
            sg.Text('Action Key', auto_size_text=True),
            sg.InputText(key='action_key', size=(2, 1), default_text=SETTINGS.keybindings.action_key)
        ],
        [
            sg.Text('Cancel Scan Key', auto_size_text=True),
            sg.InputText(key='cancel_key', size=(2, 1), default_text=SETTINGS.keybindings.cancel_key)
        ],
        [
            sg.Text('Move Forward', auto_size_text=True),
            sg.InputText(key='forward_key', size=(2, 1), default_text=SETTINGS.keybindings.forward_key)
        ],
        [
            sg.Text('Move Backward', auto_size_text=True),
            sg.InputText(key='backward_key', size=(2, 1), default_text=SETTINGS.keybindings.backward_key)
        ],
        [
            sg.Text('Resolution', auto_size_text=True),
            sg.Combo(["1920x1080", "2560x1080", "2560x1440", "3440x1440", "5120x1440"], key='resolution', default_value=SETTINGS.resolution, readonly=True)
        ],
        [
            sg.Checkbox('Play sound when finished', key='playsound', default=SETTINGS.playsound)
        ],
        [
            sg.Button('Save', enable_events=True, key=events.KEYBINDS_SAVED)
        ]
    ]
