"""Tests for the internal Niimbot printer backend."""

import asyncio
import importlib.util
from pathlib import Path
import unittest

_PRINTER_PATH = (
    Path(__file__).parents[1] / "custom_components" / "bjp_label" / "printer.py"
)
_SPEC = importlib.util.spec_from_file_location("bjp_label_printer", _PRINTER_PATH)
_PRINTER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PRINTER)
async_print_niimbot = _PRINTER.async_print_niimbot


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


if __name__ == "__main__":
    unittest.main()
