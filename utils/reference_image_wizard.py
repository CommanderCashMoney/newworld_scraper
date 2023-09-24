import PySimpleGUI as sg
import cv2
from app.ocr.utils import screenshot_bbox
from app.utils import resource_path
from app.ocr.resolution_settings import res_1440p
from app.ocr.resolution_settings import res_1080p
from app.ocr.resolution_settings import res_4k
from app.ocr.resolution_settings import res_5120x1440p

# Create a list of resolution options for the dropdown
resolution_options = ['1440p', '1080p', '3840x2160', '5120x1440']

# Default selected resolution
selected_resolution = '1440p'

# Create a dictionary to map resolution options to their corresponding resolution settings
resolution_mapping = {
    '1440p': 'res_1440p',
    '1080p': 'res_1080p',
    '3840x2160': 'res_4k',
    '5120x1440': 'res_5120x1440p'
}

# Create the layout for the window
layout = [
    [
        sg.DropDown(resolution_options, default_value=selected_resolution, key='-RESOLUTION-', enable_events=True, ),
        sg.Column([
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).mid_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' Sold Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' Buy Order')]
        ], key='-COL1-'),
        sg.Column([
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' find')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).mid_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' sold verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(
                eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).refresh_button.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).cancel_button.file_name + ' verify')],

        ], key='-COL2-')
    ],
    [sg.Button('Exit')]
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


def convert_to_grey_and_compare(reference_img, reference_grab):
    img_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
    img_grab_gray = cv2.cvtColor(reference_grab, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_grab_gray, img_gray, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val, max_loc


while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED or event == 'Exit':
        break
    elif event == '-RESOLUTION-':
        selected_resolution = values['-RESOLUTION-']
        window['-RESOLUTION-'].update(selected_resolution)
        window['-COL1-'].update([
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).mid_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' Sold Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name)],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' Buy Order')]
        ])
        window['-COL2-'].update([
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' find')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).mid_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' sold verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(
                eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' verify - Buy Order')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).refresh_button.file_name + ' verify')],
            [sg.Button(eval(resolution_mapping[selected_resolution]).cancel_button.file_name + ' verify')],
        ])
    # elif event in [button.file_name for button in resolution_mapping[selected_resolution].buttons]:
    elif event == eval(resolution_mapping[selected_resolution]).top_scroll.file_name:
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).top_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).top_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).mid_scroll.file_name:
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).mid_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).mid_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name:
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).bottom_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' Sold Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name:
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name, reference_grab)
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.screen_bbox).img_array
        cv2.imwrite(eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name, reference_grab)

    elif event == eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).top_scroll.screen_bbox).img_array
        reference_image_file = resource_path("app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).top_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).top_scroll.file_name + ' find':
        reference_grab = screenshot_bbox(0, 0, 5120,1440).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(
                resolution_mapping[selected_resolution]).top_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))


    elif event == eval(resolution_mapping[selected_resolution]).mid_scroll.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).mid_scroll.screen_bbox).img_array
        reference_image_file = resource_path("app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).mid_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).bottom_scroll.screen_bbox).img_array
        reference_image_file = resource_path("app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).bottom_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name + ' sold verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.screen_bbox).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).sold_order_top_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.screen_bbox).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).sold_order_bottom_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name + ' verify - Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.screen_bbox).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).buy_order_top_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name + ' verify - Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.screen_bbox).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).buy_order_mid_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name + ' verify - Buy Order':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.screen_bbox).img_array
        reference_image_file = resource_path(
            "app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).buy_order_bottom_scroll.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).refresh_button.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).refresh_button.screen_bbox).img_array
        reference_image_file = resource_path("app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).refresh_button.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))
    elif event == eval(resolution_mapping[selected_resolution]).cancel_button.file_name + ' verify':
        reference_grab = screenshot_bbox(*eval(resolution_mapping[selected_resolution]).cancel_button.screen_bbox).img_array
        reference_image_file = resource_path("app/images/new_world/" + eval(resolution_mapping[selected_resolution]).name + "/" + eval(resolution_mapping[selected_resolution]).cancel_button.file_name)
        reference_img = cv2.imread(reference_image_file)
        print(convert_to_grey_and_compare(reference_img, reference_grab))

window.close()
