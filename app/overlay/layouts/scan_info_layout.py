import PySimpleGUI as sg

from app import events

def scan_info_layout():
    from app.session_data import SESSION_DATA
    return [
        [sg.Text('Trade Scraper')],
        [
            sg.Button('Start Scan', size=(15, 1), key=events.RUN_BUTTON),
            sg.Checkbox('Test Run', key=events.TEST_RUN_TOGGLE, default=True, enable_events=True),
        ],
        [sg.Text('_' * 60)],
        [
            sg.pin(sg.Frame(title='Advanced', key='advanced', visible=False, layout=[
                [
                    sg.Text('Pages'),
                    sg.InputText(key=events.PAGE_INPUT, size=(4, 1), enable_events=True, default_text=SESSION_DATA.pages),
                    sg.Checkbox('Automatic Sections', key=events.AUTO_SECTIONS_TOGGLE, default=True, enable_events=True),
                    sg.Text('Server: '),
                    sg.Combo([0], size=(2, 1), key=events.SERVER_SELECT, enable_events=True, readonly=True)
                ]
            ]))
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
            sg.Text('-', key='accuracy', auto_size_text=True),
            sg.Text('Listings processed: '),
            sg.Text('-', key='listings_count', auto_size_text=True)
        ],
        [
            sg.Text('Validation Fails: '),
            sg.Text('0', key='validate_fails', auto_size_text=True),
        ],
        [sg.Text('_' * 60)],
        [
            sg.pin(
                sg.Column(key='logging', visible=True, layout=[
                    [sg.Text('Logs:')],
                    [sg.Multiline(key='log_output', size=(60, 10), auto_refresh=True, disabled=True)],
                    [sg.Text('Errors:')],
                    [sg.Multiline(key='error_output', size=(60, 5), auto_refresh=True, disabled=True)],
                ])
            )],
        [
            # sg.Button('Resend data', key=events.RESEND_DATA, visible=False),
            sg.pin(
                sg.Column(
                    key="-SCAN-DATA-COLUMN-",
                    visible=False,
                    layout=[
                    [
                        sg.In(size=(25, 1), visible=False, enable_events=True, key=events.DOWNLOAD_SCAN_DATA),
                        sg.FolderBrowse(button_text='Download Data')
                    ]
                ])
            ),
            sg.pin(sg.Button('Settings', key=events.CHANGE_KEY_BINDS))
        ]
    ]

