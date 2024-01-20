import PySimpleGUI as sg

def minimized_scan_layout():

    return [[

        sg.Text('TP Scraper', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('|', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('Pages left:', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('__calculating__', key='min_pages_left', background_color='#64778d', text_color='#FFFFFF'),

        sg.Text('Accuracy:', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('__calculating__', key='min_accuracy', background_color='#64778d', text_color='#FFFFFF'),

        sg.Text('Images to parse:', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('     0       ', key='min_ocr_count', background_color='#64778d', text_color='#FFFFFF'),

        sg.Text('Status:', background_color='#64778d', text_color='#FFFFFF'),
        sg.Text('     n/a       ', key='min_status_bar', background_color='#64778d', text_color='#FFFFFF'),

    ]
    ]
