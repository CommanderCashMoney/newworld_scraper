from pathlib import Path
from PIL import Image
import mss
from mss.screenshot import ScreenShot as mssScreenShot


def get_resource(file_name: str) -> str:
    p = Path(__file__, '../resources', file_name)
    if p.exists():
        return str(p.absolute())
    return None


class MockScreenShot(mssScreenShot):
    def __init__(self, img, monitor, size):
        super().__init__(img, monitor, size)
        self.mock = True


def get_grab(image_path):
    image_path = get_resource(image_path)

    def grab(self, monitor):
        img = Image.open(image_path)
        w, h = img.size
        monitor = dict(left=0, top=0, width=w, height=h)
        return MockScreenShot(img, monitor, size=mss.models.Size(w, h))

    return
