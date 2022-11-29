import PySimpleGUI as sg
from app import events
from app.ocr.resolution_settings import res_1440p


def sections_layout():
    section_checkboxes = [[sg.Text('Choose the sections to scan')], [sg.HorizontalSeparator()]]
    sections = res_1440p.sections
    for s in sections:
        section_checkboxes.append([sg.Checkbox(f'{s}', key=f'{s}', default=True, enable_events=False)])
    section_checkboxes.append([sg.Button('Save', enable_events=True, key=events.SECTIONS_SAVED)])
    return section_checkboxes

