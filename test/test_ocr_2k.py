from pprint import pprint
from .utils import get_grab

from app.ocr.ocr_image import OCRImage
from app.ocr import resolution_settings
from app.ocr.section_crawler import SectionCrawler



def test_resolution_2k_crawler(monkeypatch):
    res = resolution_settings.resolutions["1440p"]
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_2k-all_items.jpg'))

        section = SectionCrawler(None, res.sections['Ammunition'])
        pages = section.get_current_screen_page_count()
        assert pages == 500, "did not properly read page count"

def test_resolution_2k_scrolls(monkeypatch):
    res = resolution_settings.resolutions["1440p"]
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_2k-all_items.jpg'))
        scroll_ref = res.top_scroll
        assert scroll_ref.compare_image_reference(), "should know its at top scroll"

    ''' need a valid screenshot here 
    with monkeypatch.context() as m:
        m.setattr('app.ocr.resolution_settings.screenshot_bbox', get_screenshot_bbox('trading_2k-mid_scroll.jpg'))
        m.setattr('app.ocr.resolution_settings.capture_screen', get_capture_screen('trading_2k-mid_scroll.jpg'))
        scroll_ref = res.mid_scroll
        assert scroll_ref.compare_image_reference(), "should know its at mid scroll"
    '''

    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_2k-low_scroll.jpg'))
        scroll_ref = res.bottom_scroll
        assert scroll_ref.compare_image_reference(), "should know its at bottom scroll"

def test_resolution_2k_postfind(monkeypatch):
    res = resolution_settings.resolutions["1440p"]
    with monkeypatch.context() as m:
        m.setattr('mss.base.MSSBase.grab', get_grab('trading_2k-all_items.jpg'))
        trading_post_ref = res.trading_post
        assert trading_post_ref.compare_image_reference(), "could not find trading post"


