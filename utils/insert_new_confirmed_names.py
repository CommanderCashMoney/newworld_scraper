import json
import psycopg2

conn = psycopg2.connect(dbname="nwmp_prod") # details removed.. need to add in credentials locally
cur = conn.cursor()
cur.execute("SELECT * FROM confirmed_names")
db_data = cur.fetchall()

def do_nothing():
    pass

# open file with json scraped from nwdb. This is run from the newworld_scraper project
with open('D:\\Dev\\PyDev\\newworld_scraper\\utils\\nwdb_9-19-23-ptr.json') as f:
    data = json.load(f)
    nwdb_data = {
        item["nwdb_id"]: item
        for item in data
    }
    faction_item_id_prefixes = ["faction_armaments", "faction_provisions", "faction_armorset", "workorder_"]
    non_tradable_item_classes = ["OutpostRushOnly", "LootContainer", "SiegeWarOnly", "Blueprint", "Source_store", "HeartGem", "Entitlement", "ItemSkin", "Source_leaderboards"]
    items_to_add = []

    for val in nwdb_data.values():
        del_me = False
        for prefix in faction_item_id_prefixes:
            if prefix in val['nwdb_id']:
                # print(f'faction: {val}')
                del_me = True
                break

        for item_class in non_tradable_item_classes:
            if item_class in val['itemClass']:
                # print(f'not tradeable: {val}')
                del_me = True
                break
        if val['name'] == 'MISSING NAME':
            del_me = True
        # dont delete this. Sometimes there are doubled up strings of missing name
        if val['name'] == 'MISSING_NAME':
            del_me = True

        if 'loot_item' in val['nwdb_id']:
            del_me = True
        if '99b_msq' in val['nwdb_id']:
            del_me = True
        if '95_s01' in val['nwdb_id']:
            del_me = True
        if '99c_msq' in val['nwdb_id']:
            del_me = True
        if 'questitem' in val['nwdb_id']:
            del_me = True
        if '02a_side08' in val['nwdb_id']:
            del_me = True
        if 'xp_display' in val['nwdb_id']:
            del_me = True
        if '95a_s02' in val['nwdb_id']:
            del_me = True
        if 'gatherable_research_' in val['nwdb_id']:
            del_me = True
        if '0601_0104_shipsflagb' in val['nwdb_id']:
            del_me = True
        if '1331_0201_ravagerdrop' in val['nwdb_id']:
            del_me = True
        if '0202_0102_brackwaterritebook' in val['nwdb_id']:
            del_me = True
        if 'myrkgardkey' in val['nwdb_id']:
            del_me = True
        if 'Stringy Fungus' in val['name']:
            del_me = True
        if 'Pheromone Lure Ingredient' in val['name']:
            del_me = True
        if 'demeterboonpotiond2_t3' in val['nwdb_id']:
            del_me = True
        if 'demeterboonpotiond3_t4' in val['nwdb_id']:
            del_me = True
        if 'demeterboonpotiond1_t2' in val['nwdb_id']:
            del_me = True
        if 'artemisboonpotiond3_t4' in val['nwdb_id']:
            del_me = True
        if 'artemisboonpotiond2_t3' in val['nwdb_id']:
            del_me = True
        if 'artemisboonpotiond1_t2' in val['nwdb_id']:
            del_me = True


        if val["itemType"] in ["weapon", "armor"]:
            del_me = True

        if not del_me:
            items_to_add.append(val)
        # else:
        #     # print(f'deleted {val["nwdb_id"]}')
        #     query = "delete from confirmed_names where nwdb_id = %s"
        #     cur.execute(query, (val['nwdb_id'],))
        #     conn.commit()

    print(f'after len: {len(items_to_add)}')
    # for count, nwdb_val in enumerate(db_data):
    #     if nwdb_val[2] not in nwdb_data:
    #         print(nwdb_val, ' ', count)
        # else:
        #     print('already here ', nwdb_val[2], ' ', count)

    # reset_query = "SELECT setval('confirmed_names_id_seq', COALESCE((SELECT MAX(id)+1 FROM confirmed_names), 1), false)"
    # cur.execute(reset_query)
    # conn.commit()
    insert_count = 0
    for count, nwdb_val in enumerate(items_to_add):
        if [i for i, v in enumerate(db_data) if v[2] == nwdb_val['nwdb_id']]:
        # for i,v in enumerate(db_data):
        #     if v[2] == nwdb_val['nwdb_id']:
            # print('already have nwdbid-match',nwdb_val, ' ', count)
            #     print(f'already have nwdbid-match {nwdb_val["name"]} to {v[1]} ')
                # if nwdb_val["name"] != v[1]:
                #
                #     print(f'already have nwdbid-match {nwdb_val["name"]} to {v[1]} nwdbif={nwdb_val["nwdb_id"]}')
                #     # cur.execute("UPDATE confirmed_names SET name = %s WHERE nwdb_id = %s", (nwdb_val["name"], nwdb_val["nwdb_id"] ))
                #     # conn.commit()
            do_nothing()
        elif [i for i, v in enumerate(db_data) if v[1] == nwdb_val['name']]:
            do_nothing()
        #     # print('already have name-match', nwdb_val, ' ', count)
        else:
            print('new item ', nwdb_val, ' ', count)
            insert_data = (nwdb_val['name'], nwdb_val['nwdb_id'], json.dumps(nwdb_val['itemClass']), nwdb_val['itemType'], 10000, nwdb_val['type'])
            insert_count += 1
            # print(nwdb_data[nwdb_val])

            cur.execute("INSERT into confirmed_names(name, nwdb_id, item_classes, item_type, max_stack, type_name) VALUES (%s, %s, %s, %s, %s, %s) on conflict (name) do nothing", insert_data)
            conn.commit()
            # print('inserted: ', insert_data)



        # if nwdb_val not in db_data[2]:
        #
        #
        # else:
        #     print('already here ', nwdb_val, ' ' , count)

    print(f'inserted {insert_count} items')
cur.close()
conn.close()
