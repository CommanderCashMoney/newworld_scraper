import logging
from pathlib import Path

from app.ocr.ocr_queue import OCRQueue

logging.basicConfig(
     level=logging.DEBUG,
     format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
     datefmt='%H:%M:%S'
 )


test_image_path = Path("app/images/test_images")

oq = OCRQueue()
oq.start()

cant_afford = test_image_path / "cant-afford-prices"
can_afford = test_image_path / "can-afford-prices"

tot_files = len(list(cant_afford.iterdir()))
for img in cant_afford.iterdir():
    oq.add_to_queue(img)

q_size = oq.queue.qsize
last_q_size = q_size()
while last_q_size > 0:
    new_q_size = q_size()
    if new_q_size != last_q_size:
        print(f"{new_q_size} left of {tot_files}")
    last_q_size = new_q_size
