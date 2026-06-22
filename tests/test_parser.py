"""Tests for lightweight Thai customer text extraction."""

import unittest
import importlib.util
from pathlib import Path
import sys

_PARSER_PATH = Path(__file__).parents[1] / "custom_components" / "bjp_label" / "parser.py"
_SPEC = importlib.util.spec_from_file_location("bjp_label_parser", _PARSER_PATH)
_PARSER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PARSER
_SPEC.loader.exec_module(_PARSER)
ParseError = _PARSER.ParseError
parse_customer_text = _PARSER.parse_customer_text


class ParseCustomerTextTests(unittest.TestCase):
    def test_example_name_before_address(self):
        parsed = parse_customer_text(
            """เทพฤทธิ์  ดีเจริญ 0817544374
14/23 ม.4 ต.ธรรมศาลา อ.เมือง จ.นครปฐม 73000"""
        )
        self.assertEqual(parsed.name, "เทพฤทธิ์ ดีเจริญ")
        self.assertEqual(parsed.phone, "081-754-4374")
        self.assertEqual(parsed.postal_code, "73000")
        self.assertEqual(parsed.address, "14/23 ม.4 ต.ธรรมศาลา อ.เมือง\nจ.นครปฐม")
        self.assertLessEqual(len(parsed.address.splitlines()), 3)

    def test_example_organization_stays_in_address(self):
        parsed = parse_customer_text(
            "ส่งมนูญ เบญจพรหม โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านดงกลาง "
            "อ.คอนสาร จ.ชัยภูมิ 0818719257"
        )
        self.assertEqual(parsed.name, "มนูญ เบญจพรหม")
        self.assertEqual(parsed.phone, "081-871-9257")
        self.assertIn("โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านดงกลาง", parsed.address)

    def test_address_can_come_before_name(self):
        parsed = parse_customer_text(
            """99/1 ถนนสุขุมวิท แขวงคลองตัน กรุงเทพฯ 10110
คุณ สมชาย รักดี
โทร 081-234-5678"""
        )
        self.assertEqual(parsed.name, "คุณสมชาย รักดี")
        self.assertEqual(parsed.phone, "081-234-5678")
        self.assertEqual(parsed.postal_code, "10110")
        self.assertIn("99/1 ถนนสุขุมวิท", parsed.address)

    def test_plus_66_phone(self):
        parsed = parse_customer_text(
            "นางสาว สมหญิง ใจดี\n1 ถนนสุขใจ จ.กรุงเทพฯ\n+66 89 123 4567"
        )
        self.assertEqual(parsed.name, "นางสาวสมหญิง ใจดี")
        self.assertEqual(parsed.phone, "089-123-4567")

    def test_missing_phone_is_rejected(self):
        with self.assertRaisesRegex(ParseError, "ไม่พบเบอร์โทรศัพท์"):
            parse_customer_text("สมชาย รักดี\n99 ถนนสุขุมวิท")

    def test_missing_name_is_rejected(self):
        with self.assertRaisesRegex(ParseError, "ไม่พบชื่อและนามสกุล"):
            parse_customer_text("99 ถนนสุขุมวิท จ.กรุงเทพฯ 0812345678")


if __name__ == "__main__":
    unittest.main()
