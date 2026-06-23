"""Static package contract tests that do not require a Home Assistant install."""

import json
from pathlib import Path
import re
import unittest

_ROOT = Path(__file__).parents[1]
_INTEGRATION = _ROOT / "custom_components" / "bjp_label"


class IntegrationPackageTests(unittest.TestCase):
    def test_frontend_is_bundled_and_auto_registered(self):
        source = (_INTEGRATION / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("async_register_static_paths", source)
        self.assertIn("add_extra_js_url", source)
        self.assertTrue((_INTEGRATION / "frontend" / "bjp-label-card.js").is_file())

    def test_versions_match(self):
        manifest = json.loads(
            (_INTEGRATION / "manifest.json").read_text(encoding="utf-8")
        )
        const_source = (_INTEGRATION / "const.py").read_text(encoding="utf-8")
        card_source = (
            _INTEGRATION / "frontend" / "bjp-label-card.js"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            const_source, rf'VERSION\s*=\s*"{re.escape(manifest["version"])}"'
        )
        self.assertRegex(
            card_source,
            rf'BJP_LABEL_VERSION\s*=\s*"{re.escape(manifest["version"])}"',
        )

    def test_postcode_data_and_license_are_packaged(self):
        data = json.loads(
            (_INTEGRATION / "frontend" / "postcodes.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreater(len(data), 7000)
        self.assertTrue(all(set(row) == {"s", "d", "p", "z"} for row in data))
        self.assertTrue(
            (_INTEGRATION / "frontend" / "THAI_ADDRESS_DATA_LICENSE.txt").is_file()
        )

    def test_printer_backend_keeps_niimbot_behind_integration_service(self):
        integration_source = (_INTEGRATION / "__init__.py").read_text(encoding="utf-8")
        printer_source = (_INTEGRATION / "printer.py").read_text(encoding="utf-8")
        self.assertIn("async_dispatch_print_label", integration_source)
        self.assertIn("SERVICE_GET_SETTINGS", integration_source)
        self.assertIn("async_get_settings", integration_source)
        self.assertIn("_resolve_integration_settings", integration_source)
        self.assertIn("async_print_niimbot", printer_source)
        self.assertIn("async_print_xprinter_tspl", printer_source)
        self.assertIn("SupportsResponse.OPTIONAL", integration_source)
        self.assertIn('"niimbot"', printer_source)
        self.assertIn('"print"', printer_source)


if __name__ == "__main__":
    unittest.main()
