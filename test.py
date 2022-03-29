# import json
# from pathlib import Path
# from time import perf_counter
#
# from PIL import Image
#
# from app.ocr import ocr_image
#
#
# def parse_page(file):
#     with Image.open(file) as im:
#         pg = ocr_image.get_all_items_from_image(file, im)
#         j = json.dumps({
#             "file": file,
#             "data": [pg[row] for row in pg]
#         }, default=str, indent=2)
#         with open(f"{file}.metadata", "w") as outf:
#             outf.write(j)
#
#
# def read_meta(file):
#     with file.open("r") as f:
#         j = json.load(f)
#         for row in j["data"]:
#             if "name" not in row or "price" not in row or "avail" not in row:
#                 print(j["file"], row)
#
#
# path = Path("temp/")
# p = perf_counter()
# all_data = []
# READ_META = False
# for file in path.iterdir():
#     is_meta = "metadata" in str(file)
#     if READ_META and is_meta:
#         read_meta(file)
#     if not READ_META and not is_meta:
#         parse_page(str(file))
#
#
#
# print(perf_counter() - p)

from app.ocr.crawler import Crawler

c = Crawler()
print(c)
