"""Tests for BJP Label layouts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import types
import unittest


def _ensure_package() -> None:
    if "custom_components" not in sys.modules:
        package = types.ModuleType("custom_components")
        package.__path__ = [str(Path(__file__).parents[1] / "custom_components")]
        sys.modules["custom_components"] = package
    if "custom_components.bjp_label" not in sys.modules:
        package = types.ModuleType("custom_components.bjp_label")
        package.__path__ = [str(Path(__file__).parents[1] / "custom_components" / "bjp_label")]
        sys.modules["custom_components.bjp_label"] = package


def _load_module(module_name: str, path: Path):
    _ensure_package()
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ROOT = Path(__file__).parents[1]
_TEST_FONT = str(Path("/System/Library/Fonts/Supplemental/Ayuthaya.ttf"))
_LAYOUT = _load_module(
    "custom_components.bjp_label.label",
    _ROOT / "custom_components" / "bjp_label" / "label.py",
)

build_label_payload = _LAYOUT.build_label_payload
get_label_preset = _LAYOUT.get_label_preset
render_label_image = _LAYOUT.render_label_image


def _black_pixels(image, box):
    return sum(1 for pixel in image.crop(box).getdata() if pixel == 0)


class LabelLayoutTests(unittest.TestCase):
    def test_elements_fit_canvas_and_emphasis_is_balanced(self):
        parsed = SimpleNamespace(
            name="เทพฤทธิ์ ดีเจริญ",
            phone="081-754-4374",
            address="14/23 ม.4 ต.ธรรมศาลา\nอ.เมือง จ.นครปฐม",
            postal_code="73000",
        )

        payload = build_label_payload(parsed, "/config/www/fonts/thai.ttf")

        self.assertEqual(payload[0]["value"], "เทพฤทธิ์ ดีเจริญ")
        self.assertEqual(payload[1]["size"], payload[-1]["size"])
        for element in payload:
            self.assertLess(element["x"], 640)
            self.assertLess(element["y"], 384)
            if "width" in element:
                self.assertLessEqual(element["x"] + element["width"], 640)
            if "height" in element:
                self.assertLessEqual(element["y"] + element["height"], 384)

    def test_niimbot_payload_keeps_existing_positions(self):
        parsed = SimpleNamespace(
            name="ปรีชา จงควีณิต",
            phone="081-370-2515",
            address="362/6 ซอยสุรีย์โชค ถนนตลาดใหม่\nต.ตลาด อ.เมือง\nจ.สุราษฎร์ธานี",
            postal_code="84000",
        )

        payload = build_label_payload(parsed, "/config/www/fonts/thai.ttf")

        self.assertEqual(
            payload,
            [
                {
                    "type": "new_multiline",
                    "value": "ปรีชา จงควีณิต",
                    "font": "/config/www/fonts/thai.ttf",
                    "x": 20,
                    "y": 12,
                    "size": 46,
                    "width": 600,
                    "height": 62,
                    "fit": True,
                },
                {
                    "type": "text",
                    "value": "081-370-2515",
                    "font": "/config/www/fonts/thai.ttf",
                    "x": 20,
                    "y": 82,
                    "size": 38,
                },
                {
                    "type": "new_multiline",
                    "value": "362/6 ซอยสุรีย์โชค ถนนตลาดใหม่\nต.ตลาด อ.เมือง\nจ.สุราษฎร์ธานี",
                    "font": "/config/www/fonts/thai.ttf",
                    "x": 20,
                    "y": 140,
                    "size": 32,
                    "spacing": 36,
                    "width": 600,
                    "height": 140,
                    "fit": True,
                },
                {
                    "type": "text",
                    "value": "84000",
                    "font": "/config/www/fonts/thai.ttf",
                    "x": 20,
                    "y": 315,
                    "size": 38,
                },
            ],
        )

    def test_xprinter_render_uses_expected_canvas_for_100x75(self):
        parsed = SimpleNamespace(
            name="สมศรี ทดสอบยาวมากเพื่อบังคับย่อฟอนต์",
            phone="081-754-4374",
            address="14/23 ม.4 ต.ธรรมศาลา\nอ.เมือง จ.นครปฐม\nใกล้ตลาดเก่า",
            postal_code="73000",
        )

        image = render_label_image(parsed, font=_TEST_FONT, label_size="100x75")
        preset = get_label_preset("100x75")

        self.assertEqual(image.size, (preset.canvas_width, preset.canvas_height))
        self.assertLess(image.getbbox()[2], preset.canvas_width + 1)
        self.assertLess(image.getbbox()[3], preset.canvas_height + 1)

    def test_xprinter_100x75_draws_sample_bordered_layout(self):
        parsed = SimpleNamespace(
            name="ปรีชา จงควีณิต",
            phone="081-370-2515",
            address="362/6 ซอยสุรีย์โชค ถนนตลาดใหม่\nต.ตลาด อ.เมือง\nจ.สุราษฎร์ธานี",
            postal_code="84000",
        )

        image = render_label_image(parsed, font=_TEST_FONT, label_size="100x75")

        self.assertEqual(image.size, (800, 600))
        for point in ((36, 36), (764, 36), (36, 564), (764, 564)):
            self.assertEqual(image.getpixel(point), 0)
        for y in (126, 206, 466):
            self.assertEqual(image.getpixel((400, y)), 0)
        self.assertGreater(_black_pixels(image, (124, 46, 718, 118)), 100)
        self.assertGreater(_black_pixels(image, (124, 134, 554, 196)), 100)
        self.assertGreater(_black_pixels(image, (220, 472, 520, 544)), 100)

    def test_xprinter_render_uses_expected_canvas_for_100x150(self):
        parsed = SimpleNamespace(
            name="สมศรี ทดสอบยาวมากเพื่อบังคับย่อฟอนต์",
            phone="081-754-4374",
            address="14/23 ม.4 ต.ธรรมศาลา\nอ.เมือง จ.นครปฐม\nใกล้ตลาดเก่า",
            postal_code="73000",
        )

        image = render_label_image(parsed, font=_TEST_FONT, label_size="100x150")
        preset = get_label_preset("100x150")

        self.assertEqual(image.size, (preset.canvas_width, preset.canvas_height))
        self.assertLess(image.getbbox()[2], preset.canvas_width + 1)
        self.assertLess(image.getbbox()[3], preset.canvas_height + 1)


if __name__ == "__main__":
    unittest.main()
