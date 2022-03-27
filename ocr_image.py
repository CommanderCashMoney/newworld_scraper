import time
import os
import numpy as np
import cv2
import pytesseract
from datetime import datetime
import threading
import sys
from grabscreen import grab_screen
import requests
import json

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract\\tesseract.exe')


def get_name_swaps(env):
    # env = 'prod'
    if env == 'dev':
        url = 'http://127.0.0.1:8080/nc/'
    else:
        url = 'https://nwmarketprices.com/nc/'
    response = requests.get(url)
    response = response.json()
    l_names = json.loads(response['nc'])
    dict_name_swaps = dict()
    for x in l_names:
        dict_name_swaps[x[0]] = x[1]
    return dict_name_swaps


def text_cleanup(text):
    dict_name_cleaup = ocr.dict_name_cleanup
    for i in dict_name_cleaup:
        if i in text:
            text = text.replace(i, dict_name_cleaup[i])
            return text

    return text


def get_name_ids(env):
    # env = 'prod'
    if env == 'dev':
        url = 'http://127.0.0.1:8080/cn/'
    else:
        url = 'https://nwmarketprices.com/cn/'
    response = requests.get(url)
    response = response.json()
    l_names = json.loads(response['cn'])
    dict_confirmed_names = dict()
    for x in l_names:
        dict_confirmed_names[x[0]] = x[1]
    return dict_confirmed_names


def process_image(img, blur=3):
    scale_percent = 250  # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)


    lower_color = np.array([75, 40, 40])
    upper_color = np.array([255, 255, 255])

    mask = cv2.inRange(img, lower_color, upper_color)
    res = cv2.bitwise_and(img, img, mask=mask)

    res = cv2.cvtColor(res, cv2.COLOR_RGB2GRAY)

    res = cv2.GaussianBlur(res, (blur, blur), cv2.BORDER_ISOLATED)
    res = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    res = np.invert(res)
    # cv2.imshow('win1', res)
    # cv2.moveWindow('win1', 2560, 0)
    # file_name = resource_path('images/processed_image.png')
    # cv2.imwrite(file_name, res)
    return res


def price_check(curr_price, prev_price, s_curr_price):
    if curr_price == prev_price:
        return True, curr_price, 0

    if not curr_price or not prev_price:
        return False, curr_price, 'error'

    # get % different between curr and prev price
    try:
        diff = (abs(curr_price - prev_price) / prev_price * 100)
    except ZeroDivisionError:
        diff = 0

    if curr_price < prev_price:
        return False, curr_price, diff

    price_is_good = True

    if curr_price <= 1:
        if abs(curr_price - prev_price) > 1:
            print('price was low and differed by more than 1')
            ocr.update_overlay('error_output',
                                   'Price was low and differed by more than 1', True)
            price_is_good = False
    if curr_price > 1.00:
        if diff > 101:
            price_is_good = False


    if not price_is_good:

        if '.' not in s_curr_price:
            s_curr_price = s_curr_price[:-2:] + '.' + s_curr_price[-2:]
            s_curr_price = float(s_curr_price)
            try:
                diff2 = (abs(s_curr_price - prev_price) / prev_price * 100)
            except ZeroDivisionError:
                diff2 = 0
            if diff2 < 10 and s_curr_price >= prev_price:
                print(f'Updated price from {curr_price} to {s_curr_price}')
                ocr.update_overlay('log_output',
                                       f'Updated price from {curr_price} to {s_curr_price}', True)
                return True, s_curr_price, diff2


    if price_is_good:
        return True, curr_price, diff
    else:
        return False, curr_price, diff


def ocr_pages():
    aoi = (2233, 287, 140, 32)
    img = grab_screen(aoi)
    img = process_image(img, blur=1)
    custom_config = """--psm 8 -c tessedit_char_whitelist="0123456789of " """
    txt = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)
    pages = txt['text'][-1]
    if pages.isnumeric():

        if int(pages) < 501:
            return int(pages)
        else:
            print('page count greater than 500')
            ocr.update_overlay('error_output',
                                   'Page count greater than 500', True)
            return 1

    else:
        print('page count not numeric')
        ocr.update_overlay('error_output',
                               'Page count not numeric', True)
        return 1



def ocr_items():
    global stop_loop
    if not ocr.get_test():
        time.sleep(5)
    else:
        time.sleep(2)
    ocr.update_overlay('log_output', 'Started extracting text from images', True)
    path = resource_path('temp/')
    while True:
        img_count2 = ocr.get_img_count2()
        img_cap_status = ocr.get_cap_state()

        img_dir = os.listdir(path)
        if len(img_dir) == 0:
            if img_cap_status == 'running':
                print('Waiting for more images')
                ocr.update_overlay('status_bar', 'Waiting for more images.')
                time.sleep(5)
                continue
            else:
                print('queue is empty. stopping loop')
                ocr.update_overlay('error_output', 'Ran out of images to process prematurely', True)
                ocr.set_state('stopped')
                break
        file_name = resource_path(f'temp/img-{img_count2}.png')
        if not os.path.isfile(file_name):

            print(f'couldnt find img_count2 = {img_count2}')
            ocr.update_overlay('error_output', f'Couldnt find the correct image for text extraction. id={img_count2}', True)
            ocr.set_state('stopped')
            break
        else:
            img = cv2.imread(file_name)

        # file_name = 'testimgs/imgtest-{}.png'.format(img_count2)
        # cv2.imwrite(file_name, img)
        # print('img queue len: {}'.format(ocr.get_img_queue_len()))
        ocr.set_state('running')
        img = process_image(img)
        img_copy = img
        ocr.remove_one_img_queue(img_count2)
        custom_config = """--psm 6 -c tessedit_char_whitelist="0123456789,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:- \\"\\'" """
        txt = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)
        f_txt = {}
        i = 0
        # loop through all items found by ocr
        for count, text in enumerate(txt['text']):

            if ((1348 > txt['left'][count]) or (2898 > txt['left'][count] > 2728)) and text != '' and not text.isspace():

                text = text.replace(',' ,'')

                # loop through filtered dict to append text on the same line
                found_match = False
                for y in f_txt:
                    l_data = f_txt[y][2]


                    if txt['top'][count] in range(l_data - 25, l_data + 68):

                        # we found another word in the same row as something earlier
                        # check to see if it's in the Name column and concatenate it with previous text

                        if txt['left'][count] < 893:

                            if text is not None and f_txt[y][0] is not None:
                                f_txt[y][0] += ' ' + text.strip()

                        else:
                        # it's not a name, append it onto the end of the list
                            if text is not None:
                                text.strip()
                            similar_data = [text, txt['left'][count], txt['top'][count]]
                            f_txt[y].extend(similar_data)
                        found_match = True
                        break
                if not found_match:
                    if text is not None:
                        text.strip()
                    f_txt[i] = [text, txt['left'][count], txt['top'][count]]
                    i += 1
        prep_insert(f_txt, ocr.test, img_count2)

        ocr.set_img_count2(img_count2 + 1)


        if stop_loop:
            stop_loop = False
            print('stopped loop')
            ocr.update_overlay('log_output', 'Text extraction finished', True)
            ocr.set_state('finished')
            break


def prep_insert(d_items, testrun, img_count2):
    clean_list = []


    for x in d_items.values():
        good_to_insert = True

        # Loop through items and see if it has an item with a 'left' value in a specific range that should be where the price is
        has_price = False
        for z in range(1, len(x), 3):
            item = x[z]
            if type(item) == int:
                if 1150 > item > 1025:
                    has_price = True
                    item_price = x[z-1]
                    if '.' not in item_price:
                        x[z-1] = item_price[:-2:] + '.' + item_price[-2:]

        if not has_price:
            ocr.add_rejects(x)
            continue

        for y in x:
            if type(y) == str:
                clean_list.append(y)
        while len(clean_list) < 3:
            clean_list.append('')

        # check to see if second value is a float. It should be the price
        if clean_list[1]:
            try:
                s_curr_price = clean_list[1]
                clean_list[1] = float(clean_list[1])
            except ValueError:
                # its not a float
                clean_list[1] = ''
        # try to change the avail into an int
        if clean_list[2]:
            try:
                clean_list[2] = int(clean_list[2])
            except ValueError:
                # its not a float
                clean_list[2] = ''

        if not clean_list[0] or not clean_list[1]:
            # name or price is null. send to reject list
            ocr.add_rejects([clean_list[0], clean_list[1], clean_list[2]])
            good_to_insert = False
        if clean_list[0]:
            clean_list[0].replace('.', '')
            name_test = clean_list[0].replace(' ', '')
            name_test = name_test.replace('.', '')
            try:
                float(name_test)
                name_isfloat = True
            except ValueError:
                name_isfloat = False

            # if name is numeric, reject it
            if name_test.isnumeric() or name_isfloat:
                ocr.add_rejects([clean_list[0], clean_list[1], clean_list[2]])
                good_to_insert = False
        if good_to_insert:


            # check to see if name if on approved list
            # result = [i for i, v in enumerate(ocr.get_confirmed_names()) if v[0] == clean_list[0]]
            cn = ocr.get_confirmed_names()
            if clean_list[0] in cn:
                result = True
                name_id = cn[clean_list[0]]
            else:
                # swap out know mismatches like lron Ore and check again
                clean_list[0] = text_cleanup(clean_list[0])
                if clean_list[0] in cn:
                    result = True
                    name_id = cn[clean_list[0]]
                else:
                    name_id = None
                    result = False
            if not result:
                print(clean_list[0], ' not found in list of approved names')
                ocr.update_overlay('log_output',
                                       f'{clean_list[0]} not found in list of approved names',
                                       True)
                ocr.add_confirms(clean_list[0])
                good_to_insert = False
            old_list = ocr.get_old_list()

            if ocr.get_section_end():
                # reset old list because its a new section
                if img_count2 in ocr.get_section_end():
                    old_list = []
                    ocr.section_end_remove()

            if old_list and good_to_insert:
                passed_price_check, updated_price, price_diff = price_check(clean_list[1], old_list[1], s_curr_price)
                print('price diff of: {}'.format(price_diff))
                if not passed_price_check:
                    print(f'{clean_list[0]} price of {clean_list[1]} varied too much from {old_list[1]} previous price')
                    ocr.update_overlay('error_output',
                                           f'{clean_list[0]} price of {clean_list[1]} varied too much from {old_list[1]} previous price',
                                           True)
                    # confirm_list.append([clean_list[0], clean_list[1], clean_list[2], old_list[1]], )
                    ocr.add_price_fail([clean_list[0], clean_list[1], old_list[1]])
                    good_to_insert = False
                    ocr.increment_price_fail_count()
                else:
                    clean_list[1] = updated_price

        if ocr.get_price_fail_count() > 2:
            ocr.too_many_fails()
            print('ERROR - Too many price fails deleting last and resetting price barrier.')
            ocr.update_overlay('error_output', 'ERROR - Too many price fails deleting last and resetting price barrier.', True)
            good_to_insert = False

        if good_to_insert:
            # add to main list for insert at the end
            p_fail = len(ocr.get_price_fail())
            rejects = len(ocr.get_rejects())
            print(f'{clean_list} p_fails: {p_fail} rejects: {rejects}')
            ocr.update_overlay('log_output', f'Listing to insert: {clean_list}', True)
            ocr.update_overlay('log_output', f'Listing to insert: {clean_list}', True)
            ocr.update_overlay('p_fails', p_fail)
            ocr.update_overlay('rejects', rejects)
            total = ocr.get_total() + 1
            ocr.set_total(total)
            ocr.update_overlay('listings_count', total)
            total_fails = p_fail + rejects
            if total_fails > 0:
                print(f'total fails: {total_fails} and total: {total}')
                acc = total_fails / total
                acc = 100 - (acc * 100)
                acc = "{:.2f}".format(acc)
            else:
                acc = 100
            ocr.update_overlay('accuracy', f'{acc}%')

            dt = datetime.utcnow()
            clean_list.append(dt)
            clean_list.append(name_id)
            if not testrun:

                ocr.add_inserts(clean_list)
                ocr.update_old_list(clean_list)
                ocr.reset_price_fail_count()


        clean_list = []

stop_loop = False
class OCR_Image:

    def __init__(self):
        self.ocr_state = 'ready'
        self.aoi = (927, 430, 1510, 919)
        self.env = 'dev'
        self.confirmed_names = []
        self.insert_list = []
        self.reject_list = []
        self.confirm_list = []
        self.price_fail_list = []
        self.old_list = []
        self.price_fail_count = 0
        self.test = True
        self.dict_name_cleanup = dict()
        self.img_count2 = 1
        self.total = 0
        self.overlay_updates = []
        self.section_end = []
        self.cap_state = 'running'

    def set_section_end(self, section_end):
        self.section_end.append(section_end)

    def section_end_remove(self):
        del self.section_end[0]

    def get_section_end(self):
        return self.section_end

    def get_state(self):
        return self.ocr_state

    def set_state(self, val):
        self.ocr_state = val

    def set_cap_state(self, val):
        self.cap_state = val

    def get_cap_state(self):
        return self.cap_state

    def set_env(self, env):
        self.env = env

    def set_total(self, total):
        self.total = total

    def get_total(self):
        return self.total

    def add_img(self, img, img_count):
        file_name = resource_path(f'temp/img-{img_count}.png')
        cv2.imwrite(file_name, img)

        # self.image_queue[img_count] = img
        # self.image_queue.append((img, pages, section))


    def get_insert_list(self):
        return self.insert_list

    def add_inserts(self, inserts):
        self.insert_list.append(inserts)

    def clean_insert_list(self):
        self.insert_list = []

    def start_OCR(self):
        self.clear()
        ocr_running = False
        self.confirmed_names = get_name_ids(self.env)
        self.dict_name_cleanup = get_name_swaps(self.env)

        self.set_state('running')
        for thread in threading.enumerate():
            if thread.name == "ocr_running":
                ocr_running = True
        if not ocr_running:
            t2 = threading.Thread(target=ocr_items, name='ocr_running')
            t2.start()

    def update_overlay(self, field, val, append=None):
        self.overlay_updates.append((field, val, append))

    def get_overlay_updates(self):
        return self.overlay_updates

    def remove_one_overlayupdate(self):
        del self.overlay_updates[0]

    def stop_OCR(self):
        global stop_loop
        stop_loop = True

    def test_run(self, val):
        self.test = val

    def get_test(self):
        return self.test

    # def get_img_queue(self):
    #     return self.image_queue

    def get_img_queue_len(self):
        path = resource_path('temp/')
        img_dir = os.listdir(path)
        return len(img_dir)

    def remove_one_img_queue(self, img_count):
        file_name = resource_path(f'temp/img-{img_count}.png')
        os.remove(file_name)
        # self.image_queue.pop(img_count)
        # print(f'Removed: {img_count}')
        # if self.image_queue:
        #     del self.image_queue[0]

    def get_page_count(self):
        return ocr_pages()

    def add_rejects(self, rejects):
        self.reject_list.append(rejects)

    def get_rejects(self):
        return self.reject_list

    def add_price_fail(self, price_fail):
        self.price_fail_list.append(price_fail)

    def get_price_fail(self):
        return self.price_fail_list

    def add_confirms(self,confirms):
        self.confirm_list.append(confirms)

    def del_confirms(self):
        del self.confirm_list[:10]

    def get_confirms(self):
        return self.confirm_list

    def get_confirmed_names(self):
        return self.confirmed_names

    def update_old_list(self, old_list):
        self.old_list = old_list

    def get_old_list(self):
        return self.old_list

    def increment_price_fail_count(self):
        self.price_fail_count += 1

    def get_price_fail_count(self):
        return self.price_fail_count

    def reset_price_fail_count(self):
        self.price_fail_count = 0

    def too_many_fails(self):
        self.old_list = []
        del self.insert_list[-1]
        self.price_fail_count = 0

    def set_img_count2(self, val):
        self.img_count2 = val

    def get_img_count2(self):
        return self.img_count2

    def clear(self):
        self.image_queue = []
        self.insert_list = []
        self.reject_list = []
        self.confirm_list = []
        self.old_list = []
        self.price_fail_count = 0
        self.img_count2 = 1
        self.total = 0
        print('All lists cleared')

        dir = resource_path('temp/')
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))


ocr = OCR_Image()

