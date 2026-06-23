"""Tests for the BJP Label printer backends."""

import asyncio
import importlib.util
from pathlib import Path
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
_PRINTER = _load_module(
    "custom_components.bjp_label.printer",
    _ROOT / "custom_components" / "bjp_label" / "printer.py",
)

PRINTER_BACKEND_XPRINTER_TSPL = _PRINTER.PRINTER_BACKEND_XPRINTER_TSPL
async_print_niimbot = _PRINTER.async_print_niimbot
async_print_xprinter_tspl = _PRINTER.async_print_xprinter_tspl
resolve_print_config = _PRINTER.resolve_print_config
_build_tspl_command = _PRINTER._build_tspl_command


class _Services:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def async_call(self, domain, service, **kwargs):
        self.calls.append((domain, service, kwargs))
        return self.response


class _Hass:
    def __init__(self, response):
        self.services = _Services(response)

    async def async_add_executor_job(self, func):
        return func()


class PrinterBackendTests(unittest.TestCase):
    def test_preview_requests_and_returns_service_response(self):
        hass = _Hass({"image": "data:image/png;base64,TEST"})
        response = asyncio.run(
            async_print_niimbot(
                hass,
                payload=[{"type": "text", "value": "ทดสอบ"}],
                width=640,
                height=384,
                density=3,
                rotate=90,
                preview=True,
                device_id="device-1",
                context="context-1",
                return_response=True,
            )
        )

        self.assertEqual(response, {"image": "data:image/png;base64,TEST"})
        domain, service, kwargs = hass.services.calls[0]
        self.assertEqual((domain, service), ("niimbot", "print"))
        self.assertTrue(kwargs["service_data"]["preview"])
        self.assertTrue(kwargs["return_response"])

    def test_real_print_does_not_request_response(self):
        hass = _Hass(None)
        asyncio.run(
            async_print_niimbot(
                hass,
                payload=[],
                width=640,
                height=384,
                density=3,
                rotate=90,
                preview=False,
                device_id="device-1",
                context=None,
            )
        )

        kwargs = hass.services.calls[0][2]
        self.assertNotIn("preview", kwargs["service_data"])
        self.assertFalse(kwargs["return_response"])

    def test_resolve_print_config_prefers_service_over_settings(self):
        config = resolve_print_config(
            {
                "printer_backend": PRINTER_BACKEND_XPRINTER_TSPL,
                "host": "192.168.1.10",
                "port": 9200,
                "label_size": "100x150",
                "width": 123,
                "rotate": 90,
            },
            {
                "printer_backend": "niimbot",
                "host": "192.168.1.20",
                "port": 9100,
                "label_size": "100x75",
                "width": 640,
            },
        )

        self.assertEqual(config.backend, PRINTER_BACKEND_XPRINTER_TSPL)
        self.assertEqual(config.host, "192.168.1.10")
        self.assertEqual(config.port, 9200)
        self.assertEqual(config.label_size, "100x150")
        self.assertEqual(config.width, 123)
        self.assertEqual(config.rotate, 0)
        self.assertEqual(config.device_id, "")

    def test_resolve_print_config_clears_xprinter_fields_for_niimbot(self):
        config = resolve_print_config(
            {
                "printer_backend": "niimbot",
                "device_id": "device-1",
                "host": "192.168.1.10",
                "label_size": "100x150",
                "rotate": 90,
            },
            {},
        )

        self.assertEqual(config.backend, "niimbot")
        self.assertEqual(config.device_id, "device-1")
        self.assertEqual(config.host, "")
        self.assertEqual(config.label_size, "100x75")
        self.assertEqual(config.rotate, 90)

    def test_xprinter_preview_returns_image_without_network(self):
        hass = _Hass(None)
        parsed = types.SimpleNamespace(
            name="สมชาย ใจดี",
            phone="081-234-5678",
            address="99/9 ถ.สุขใจ\nต.บางรัก อ.เมือง",
            postal_code="10100",
        )
        response = asyncio.run(
            async_print_xprinter_tspl(
                hass,
                parsed=parsed,
                font=_TEST_FONT,
                label_size="100x75",
                host="192.168.1.50",
                port=9100,
                preview=True,
                return_response=True,
            )
        )

        self.assertTrue(response["image"].startswith("data:image/png;base64,"))

    def test_tspl_command_contains_expected_size_and_print(self):
        image = _PRINTER.render_label_image(
            types.SimpleNamespace(
                name="สมหญิง",
                phone="089-000-0000",
                address="1/2 ถ.ทดสอบ\nต.ตัวอย่าง อ.เมือง",
                postal_code="73000",
            ),
            font=_TEST_FONT,
            label_size="100x150",
        )

        command = _build_tspl_command(image, label_size="100x150")

        self.assertIn(b"SIZE 100 mm,150 mm", command)
        self.assertIn(b"BITMAP 0,0,100,1200,0,", command)
        self.assertTrue(command.endswith(b"\r\nPRINT 1,1\r\n"))


if __name__ == "__main__":
    unittest.main()
