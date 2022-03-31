import PySimpleGUI as sg

from app import events

SCAN_INFO_LAYOUT = [
    [sg.Text('Trade Scraper')],
    [
        sg.Button('Start Scan', size=(15, 1), key=events.RUN_BUTTON),
        sg.Checkbox('Test Run', key=events.TEST_RUN_TOGGLE, default=True, enable_events=True),
    ],
    [sg.Text('_' * 60)],
    [
        sg.Frame(title='Advanced', key='advanced', visible=False, layout=[
            [
                sg.Text('Pages'), sg.InputText(key=events.PAGE_INPUT, size=(4, 1), enable_events=True),
                sg.Checkbox('Automatic Sections', key=events.AUTO_SECTIONS_TOGGLE, default=True, enable_events=True),
                sg.Text('Server: '),
                sg.Combo([0], size=(2, 1), key=events.SERVER_SELECT, enable_events=True, readonly=True)
            ]
        ])
    ],
    [
        sg.Text('Status: '),
        sg.Text('Ready', key='status_bar', auto_size_text=True)
    ],
    [
        sg.Text('Elapsed Time: '),
        sg.Text('-', key='elapsed', auto_size_text=True),
        sg.Text('Pages left in section: '),
        sg.Text('-', key='pages_left', auto_size_text=True)
    ],
    [
        sg.Text('Images captured: '),
        sg.Text('0', key='key_count', auto_size_text=True),
        sg.Text('Images left to parse: '),
        sg.Text('0', key='ocr_count', auto_size_text=True)
    ],
    [
        sg.Text('Accuracy: '),
        sg.Text('0%', key='accuracy', auto_size_text=True),
        sg.Text('Listings processed: '),
        sg.Text('0', key='listings_count', auto_size_text=True)
    ],
    [
        sg.Text('Price fails: '),
        sg.Text('0', key='p_fails', auto_size_text=True),
        sg.Text('Data Rejects: '),
        sg.Text('0', key='rejects', auto_size_text=True)
    ],
    [sg.Text('_' * 60)],
    [sg.Text('Logs:')],
    [sg.Multiline(key='log_output', size=(60, 10), auto_refresh=True, disabled=True)],
    [sg.Text('Errors:')],
    [sg.Multiline(key='error_output', size=(60, 5), auto_refresh=True, disabled=True)],
    [
        sg.Button('Resend data', key='resend', visible=False),
        sg.In(size=(25, 1), enable_events=True, key='-FOLDER-', visible=False),
        sg.FolderBrowse(button_text='Download Data')
    ]
]
