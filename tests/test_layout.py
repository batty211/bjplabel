"""Tests for the pre-rotation Niimbot label layout."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

_LAYOUT_PATH = Path(__file__).parents[1] / "custom_components" / "bjp_label" / "label.py"
_SPEC = importlib.util.spec_from_file_location("bjp_label_layout", _LAYOUT_PATH)
_LAYOUT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_LAYOUT)
build_label_payload = _LAYOUT.build_label_payload


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


if __name__ == "__main__":
    unittest.main()
