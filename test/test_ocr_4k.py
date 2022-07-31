from pprint import pprint
from .utils import get_grab

from app.ocr.ocr_image import OCRImage
from app.ocr import resolution_settings
from app.ocr.section_crawler import SectionCrawler

res = resolution_settings.resolutions["2160p"]

'''
relies on a cache i did not make here
def test_resolution_4k_crawler(monkeypatch):
    res = resolution_settings.resolutions["2160p"]
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_4k.jpg'))

        section = SectionCrawler(None, res.sections['Ammunition'])
        pages = section.get_current_screen_page_count()
        assert pages == 500, "did not properly read page count"
'''


def test_resolution_4k_scrolls(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_4k.jpg'))
        scroll_ref = res.top_scroll
        assert scroll_ref.compare_image_reference(), "should know its at top scroll"


def test_resolution_2k_postfind(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_4k-new.jpg'))
        trading_post_ref = res.trading_post
        assert trading_post_ref.compare_image_reference(), "could not find trading post"
