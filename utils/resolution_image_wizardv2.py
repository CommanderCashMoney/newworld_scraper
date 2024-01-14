import PySimpleGUI as sg
import cv2
from app.ocr.utils import screenshot_bbox
from app.utils import resource_path
from app.ocr.resolution_settings import *

# Create a list of resolution options for the dropdown
resolution_options = ['2560x1440', '1920x1080', '3840x2160', '5120x1440', '3440x1440', '2560x1080']

# Default selected resolution
selected_resolution = '2560x1440'
resolution_mapping = {
    '2560x1440': res_1440p,
    '1920x1080': res_1080p,
    '3840x2160': res_4k,
    '5120x1440': res_5120x1440p,
    '3440x1440': res_3440x1440p,
    '2560x1080': res_2560x1080p
}


layout = [
    [


        sg.Column([
            [sg.DropDown(resolution_options, default_value=selected_resolution, key='-RESOLUTION-', enable_events=True, )],
             [sg.Text('Left Offset'), sg.Input('', key='-LEFT_OFFSET-', size=(5, 1))],
             [sg.Text('Top Offset'), sg.Input('', key='-TOP_OFFSET-', size=(5, 1))],
             [sg.Multiline('', key='-OUTPUT-', size=(30, 25), auto_refresh=True, disabled=True)]

        ], key='-COL0-'),

        sg.Column([
            [sg.Button(f"{button[0]} - cap")]
            for button in resolution_mapping[selected_resolution] if isinstance(button[1], ImageReference)

        ], key='-COL1-'),
        sg.Column([
            [sg.Button(f"{button[0]} - verify")]
            for button in resolution_mapping[selected_resolution] if isinstance(button[1], ImageReference)

        ], key='-COL2-'),
        sg.Column([
            [sg.Button(f"{button[0]} - find")]
            for button in resolution_mapping[selected_resolution] if isinstance(button[1], ImageReference)

        ], key='-COL3-')
    ],

]

# Create the window
window = sg.Window('Screenshot Capture',
                   layout,
                   keep_on_top=False,
                   location=(150, 150),
                   finalize=True,
                   use_default_focus=False,
                   grab_anywhere=True
                   )


def output_text(txt):
    val = str(txt) + '\n'
    window['-OUTPUT-'].Update(value=val, append=True, autoscroll=True)



def convert_to_grey_and_compare(reference_img, reference_grab):
    img_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
    img_grab_gray = cv2.cvtColor(reference_grab, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_grab_gray, img_gray, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return round(max_val, 4), max_loc
def apply_offset(bbox):
    left_offset = int(values['-LEFT_OFFSET-']) if values['-LEFT_OFFSET-'] else 0
    top_offset = int(values['-TOP_OFFSET-']) if values['-TOP_OFFSET-'] else 0
    return (bbox[0] + left_offset, bbox[1] + top_offset, bbox[2], bbox[3]), left_offset, top_offset

def verify_button_click(event_name):
    res = resolution_mapping[selected_resolution]
    image_ref = getattr(res, event_name[:-9])
    reference_grab = screenshot_bbox(*apply_offset(image_ref.screen_bbox)[0]).img_array
    reference_image_file = resource_path(
        "app/images/new_world/" + selected_resolution + "/" + image_ref.file_name)
    reference_img = cv2.imread(reference_image_file)
    output_text(f'Looked for {image_ref.file_name} at {apply_offset(image_ref.screen_bbox)}')
    output_text(f'Results: {convert_to_grey_and_compare(reference_img, reference_grab)}')

def cap_button_click(event_name):
    res = resolution_mapping[selected_resolution]
    image_ref = getattr(res, event_name[:-6])
    reference_grab = screenshot_bbox(*apply_offset(image_ref.screen_bbox)[0]).img_array
    img_path = resource_path("app/images/new_world/" + selected_resolution + "/" + image_ref.file_name)
    cv2.imwrite(img_path, reference_grab)
    output_text(f'Image captured to {img_path}')

def find_button_click(event_name):
    res = resolution_mapping[selected_resolution]
    image_ref = getattr(res, event_name[:-7])
    reference_grab = screenshot_bbox(0, 0, 5120, 1440).img_array
    reference_image_file = resource_path(
        "app/images/new_world/" + selected_resolution + "/" + image_ref.file_name)
    reference_img = cv2.imread(reference_image_file)
    output_text(convert_to_grey_and_compare(reference_img, reference_grab))


while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED or event == 'Exit':
        break
    elif event == '-RESOLUTION-':
        selected_resolution = values['-RESOLUTION-']
        window['-RESOLUTION-'].update(selected_resolution)
    else:
        if "verify" in event:
            verify_button_click(event)
        elif "cap" in event:
            cap_button_click(event)

        elif "find" in event:
            find_button_click(event)


