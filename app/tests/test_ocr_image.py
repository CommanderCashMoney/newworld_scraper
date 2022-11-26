import os

import pytest
import cv2
import numpy as np

from app.ocr import ocr_image
from app.ocr import resolution_settings

expected_results = [
    [
        "1920x1080_1.png",
        [
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
        ],
    ],
    [
        "1920x1080_2.png",
        [
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "100"},
            {"name": "Light Meal", "price": "0.01", "avail": "77"},
            {"name": "Travel Ration", "price": "0.01", "avail": "3"},
        ],
    ],
        [
        "3840x2160_1.png",
        [
            {'name': 'Energizing Light Meal', 'price': '0.01', 'avail': '100'},
            {'name': 'Energizing Light Meal', 'price': '0.01', 'avail': '47'},
            {'name': 'Nightcrawler Bait', 'price': '0.01', 'avail': '296'},
            {'name': 'Light Meal', 'price': '0.01', 'avail': '100'},
            {'name': 'Light Meal', 'price': '0.01', 'avail': '100'},
            {'name': 'Light Meal', 'price': '0.01', 'avail': '58'},
            {'name': 'Energizing Satisfying Meal', 'price': '0.01', 'avail': '31'},
            {'name': 'Powerful Focus Potion', 'price': '0.01', 'avail': '34'},
            {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '82'},
        ],
    ],
        [
            "5120x1440_2.png",
            [
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '42'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '344'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '62'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '134'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '1142'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '108'},
                {'name': 'Morning Chores Guitar Sheet Music Page 3/3', 'price': '0.01', 'avail': '24'},
                {'name': 'Woodlouse Bait', 'price': '0.01', 'avail': '873'},
                {'name': 'Nightcrawler Bait', 'price': '0.01', 'avail': '96'},
            ],
        ],
]


@pytest.fixture
def mock_ocr_image(request, tmp_path):
    image_path = os.path.join("app", "tests", "test_data", "images", request.param)
    screenshot = cv2.imread(image_path)
    box = np.array(resolution_settings.res_1080p.items_bbox)
    resolution = request.param.split("_")[0].split("x")
    width, height = int(resolution[0]), int(resolution[1])
    scale = height / 1080
    box = box * scale + np.array([(width - scale*1920) / 2, 0, 0, 0])
    print(resolution_settings.res_1080p.items_bbox)
    print(box)
    box_left, box_top, box_width, box_height = tuple(box.astype(int))
    print(type(box_left))
    cropped_screenshot = screenshot[box_top : box_top + box_height, box_left :box_left + box_width]
    cropped_screenshot = cv2.resize(cropped_screenshot, resolution_settings.res_1080p.items_bbox[2:], interpolation=cv2.INTER_LINEAR)
    cropped_path = tmp_path / request.param
    cv2.imwrite(str(cropped_path), cropped_screenshot)
    image = ocr_image.OCRImage(img_src=cropped_path, section="test")
    return image


@pytest.mark.parametrize("mock_ocr_image,expected_result", expected_results, indirect=["mock_ocr_image"])
def test_ocr(mock_ocr_image, expected_result):
    data = mock_ocr_image.parse_prices()
    result = []
    for record in data:
        clean_record = {field: record[field] for field in ["name", "price", "avail"]}
        print(f"{clean_record},")
        result.append(clean_record)
    assert result == expected_result
