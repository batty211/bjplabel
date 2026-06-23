"""Static checks for the BJP Label config flow source."""

from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_CONFIG_FLOW = _ROOT / "custom_components" / "bjp_label" / "config_flow.py"
_STRINGS = _ROOT / "custom_components" / "bjp_label" / "strings.json"


class ConfigFlowSourceTests(unittest.TestCase):
    def test_config_flow_supports_backend_specific_steps_and_options(self):
        source = _CONFIG_FLOW.read_text(encoding="utf-8")
        self.assertIn("async_get_options_flow", source)
        self.assertIn("class BjpLabelOptionsFlow", source)
        self.assertIn("async_step_niimbot", source)
        self.assertIn("async_step_xprinter", source)
        self.assertIn("DeviceSelector", source)
        self.assertIn("CONF_HOST", source)

    def test_strings_include_setup_and_option_steps(self):
        source = _STRINGS.read_text(encoding="utf-8")
        self.assertIn('"niimbot"', source)
        self.assertIn('"xprinter"', source)
        self.assertIn('"option"', source)
        self.assertIn("แก้ไขการตั้งค่า BJP Label", source)


if __name__ == "__main__":
    unittest.main()
