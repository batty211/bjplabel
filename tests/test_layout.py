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
