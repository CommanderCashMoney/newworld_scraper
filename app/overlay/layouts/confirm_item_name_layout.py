import PySimpleGUI as sg

good_bad_names = [
    [
        sg.InputText('', key=f'bad-name-{idx}', size=(35, 1), disabled=True),
        sg.Combo(['Add new'], key=f'good-name-{idx}', readonly=True),
        sg.Button('Add', key=f'add-confirmed-name-{idx}', enable_events=True)
    ] for idx in range(10)
]


CONFIRM_ITEM_NAMES_LAYOUT = [
    sg.Frame(title='Confirm Item Names', key='confirm', visible=False, layout=[
        *good_bad_names,
        [sg.Button('Load next set', key='next_btn')]
    ])
]
