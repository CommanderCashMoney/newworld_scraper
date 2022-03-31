import PySimpleGUI as sg

CONFIRM_ITEM_NAMES_LAYOUT = [
    sg.Frame(title='Confirm item names', key='confirm', visible=False, layout=[
        [
            sg.InputText('', key='bad_name_0', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_0', enable_events=True, readonly=True),
            sg.Button('Add', key='add0', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_1', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_1', enable_events=True, readonly=True),
            sg.Button('Add', key='add1', disabled=True)],
        [
            sg.InputText('', key='bad_name_2', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_2', enable_events=True, readonly=True),
            sg.Button('Add', key='add2', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_3', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_3', enable_events=True, readonly=True),
            sg.Button('Add', key='add3', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_4', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_4', enable_events=True, readonly=True),
            sg.Button('Add', key='add4', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_5', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_5', enable_events=True, readonly=True),
            sg.Button('Add', key='add5', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_6', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_6', enable_events=True, readonly=True),
            sg.Button('Add', key='add6', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_7', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_7', enable_events=True, readonly=True),
            sg.Button('Add', key='add7', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_8', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_8', enable_events=True, readonly=True),
            sg.Button('Add', key='add8', disabled=True)
        ],
        [
            sg.InputText('', key='bad_name_9', size=(35, 1)),
            sg.Combo(['Add new'], key='good_name_9', enable_events=True, readonly=True),
            sg.Button('Add', key='add9', disabled=True)
        ],
        [sg.Button('Load next set', key='next_btn')]
    ])
]