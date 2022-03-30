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
                logging.info(f'{clean_list[0]} not found in list of approved names')
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
                    logging.error(f'{clean_list[0]} price of {clean_list[1]} varied too much from {old_list[1]} previous price')
                    # confirm_list.append([clean_list[0], clean_list[1], clean_list[2], old_list[1]], )
                    ocr.add_price_fail([clean_list[0], clean_list[1], old_list[1]])
                    good_to_insert = False
                    ocr.increment_price_fail_count()
                else:
                    clean_list[1] = updated_price

        if ocr.get_price_fail_count() > 2:
            ocr.too_many_fails()
            logging.error('Too many price fails deleting last and resetting price barrier.')
            good_to_insert = False

        if good_to_insert:
            # add to main list for insert at the end
            p_fail = len(ocr.get_price_fail())
            rejects = len(ocr.get_rejects())
            print(f'{clean_list} p_fails: {p_fail} rejects: {rejects}')
            logging.info(f'Listing to insert: {clean_list}')
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

            dt = datetime.now()

            clean_list.append(dt)
            clean_list.append(name_id)
            if not testrun:
                ocr.add_inserts(clean_list)
                ocr.update_old_list(clean_list)
                ocr.reset_price_fail_count()


        clean_list = []



def next_confirm_page():
    global current_page
    current_page += 1
    for x in range(10):
        OverlayUpdateHandler.update(f'bad_name_{x}', '', size=10)
        OverlayUpdateHandler.update(f'good_name_{x}', '', size=10)

    if len(ocr_image.ocr.get_confirms()) >= 10:
        ocr_image.ocr.del_confirms()
    populate_confirm_form()



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
            logging.error('Price was low and differed by more than 1')
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
                logging.info(f'Updated price from {curr_price} to {s_curr_price}')
                return True, s_curr_price, diff2


    if price_is_good:
        return True, curr_price, diff
    else:
        return False, curr_price, diff


def add_single_item(clean_list, env, func):
    global user_name, access_groups
    # add timestamp
    now = datetime.now()
    dt_string = now.strftime('%Y-%m-%dT%X')
    clean_list.append(dt_string)
    json_data = ''
    if func == 'name_cleanup_insert':
        json_data = '{"bad_word":' + json.dumps(clean_list[0]) + ', "good_word":' + json.dumps(clean_list[1]) + ', "timestamp": "' + clean_list[2] + '", '

    elif func == 'confirmed_names_insert':

        json_data = '{"name":' + json.dumps(clean_list[0]) + ', "timestamp": "' + clean_list[2] + '", '

    if 'scanner_user' in access_groups:
        json_data = json_data + '"approved": "True", '
    else:
        json_data = json_data + '"approved": "False", '
    json_data = json_data + f'"username": "{user_name}"' + '}'

    api_insert(json_data, env, 1, 0, func)


def populate_confirm_form():
    cn = ocr_image.ocr.get_confirmed_names()
    cn_list = list(cn.keys())
    confirm_list = ocr_image.ocr.get_confirms()
    for count, value in enumerate(confirm_list):
        if count >= 10:
            break
        OverlayUpdateHandler.update(f'bad_name_{count}', value, size=len(value))
        close_matches = difflib.get_close_matches(value, cn_list, n=5, cutoff=0.6)
        close_matches.insert(0, 'Add New')
        s = max(close_matches, key=len)
        overlay.add_names(f'good_name_{count}', close_matches, size=s)

        overlay.enable('add{}'.format(count))


