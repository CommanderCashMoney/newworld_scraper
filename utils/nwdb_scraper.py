import cloudscraper
import json
import time

def get_page(page_id: int):
    url = f"https://ptr.nwdb.info/db/items/page/{page_id}.json?sort=gs_desc"
    scrape = cloudscraper.create_scraper()
    items = scrape.get(url)
    items_json = items.json()
    return {
        "page_count": items_json["pageCount"],
        "data": [{
            "nwdb_id": data["id"],
            "name": data["name"],
            "itemType": data["itemType"],
            "type": data["type"],
            "itemClass": data["itemClass"],
            "not_obtainable": data.get("notObtainable"),
            "type_name": data.get("typeName"),
            "bop": data.get("bindOnPickup")


        } for data in items_json["data"]]
    }


def get_all_items() -> None:
    all_data = []
    pg1 = get_page(1)
    pages = pg1["page_count"]
    # all_data = pg1["data"]
    for i in range(1, pages+1):
        pg = get_page(i)
        all_data.extend(pg["data"])
        time.sleep(1)
        print(f'scanning page: {i}')
    with open("nwdb_9-19-23-ptr.json", "w") as outf:
        json.dump(all_data, outf, indent=2)


if __name__ == '__main__':
    get_all_items()