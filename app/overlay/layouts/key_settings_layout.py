import PySimpleGUI as sg

KEY_SETTINGS_LAYOUT = [
    [sg.Text('Action Key', auto_size_text=True), sg.InputText(key='action_key', size=(2, 1))],
    [sg.Text('Move Forward', auto_size_text=True), sg.InputText(key='forward_key', size=(2, 1))],
    [sg.Text('Move Backward', auto_size_text=True), sg.InputText(key='backward_key', size=(2, 1))],
    [sg.Button('Save')]
]
