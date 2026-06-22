"""BJP Label integration."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE_ID,
    CONF_FONT,
    DEFAULT_DENSITY,
    DEFAULT_FONT,
    DEFAULT_HEIGHT,
    DEFAULT_ROTATE,
    DEFAULT_WIDTH,
    DOMAIN,
    FRONTEND_URL,
    SERVICE_PRINT_CUSTOMER,
    SERVICE_PRINT_LABEL,
    SERVICE_SAVE_CUSTOMER,
    SERVICE_SEARCH_CUSTOMERS,
    VERSION,
)
from .label import build_label_payload
from .parser import ParseError, ParsedLabel, format_address_lines, parse_customer_text
from .printer import async_print_niimbot

_LOGGER = logging.getLogger(__name__)
_FRONTEND_PATH = Path(__file__).parent / "frontend"

PRINT_LABEL_SCHEMA = vol.Schema(
    {
        vol.Optional("text"): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional("phone"): cv.string,
        vol.Optional("address", default=""): cv.string,
        vol.Optional("note", default=""): cv.string,
        vol.Optional("postal_code", default=""): cv.string,
        vol.Optional("font"): cv.string,
        vol.Optional("width", default=DEFAULT_WIDTH): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=1600)
        ),
        vol.Optional("height", default=DEFAULT_HEIGHT): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=1600)
        ),
        vol.Optional("density", default=DEFAULT_DENSITY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=5)
        ),
        vol.Optional("rotate", default=DEFAULT_ROTATE): vol.All(
            vol.Coerce(int), vol.In([0, 90, 180, 270])
        ),
        vol.Optional("preview", default=False): cv.boolean,
        vol.Optional("device_id"): cv.string,
    }
)

SAVE_CUSTOMER_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("phone"): cv.string,
        vol.Required("address"): cv.string,
        vol.Optional("note", default=""): cv.string,
    }
)
SEARCH_CUSTOMERS_SCHEMA = vol.Schema({vol.Required("query"): cv.string})
PRINT_CUSTOMER_SCHEMA = vol.Schema({vol.Required("customer_id"): vol.Coerce(int)})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initialize shared integration data and register services."""
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(_FRONTEND_PATH), True)]
    )
    add_extra_js_url(
        hass, f"{FRONTEND_URL}/bjp-label-card.js?v={VERSION}"
    )

    async def async_print_label(call: ServiceCall) -> None:
        data = call.data
        parsed = _parse_service_data(data)
        settings = next(iter(hass.data[DOMAIN].values()), {})
        font = data.get("font") or settings.get(CONF_FONT, DEFAULT_FONT)
        if not os.path.isabs(font):
            www_font = hass.config.path("www", "fonts", font)
            if os.path.isfile(www_font):
                font = www_font
        call_target = getattr(call, "target", None) or {}
        target_device = call_target.get("device_id") if isinstance(call_target, dict) else None
        if isinstance(target_device, list):
            target_device = target_device[0] if target_device else None
        device_id = (
            data.get("device_id") or target_device or settings.get(CONF_DEVICE_ID)
        )
        if not device_id:
            raise ServiceValidationError("ยังไม่ได้ตั้งค่าเครื่องพิมพ์ Niimbot")

        await async_print_niimbot(
            hass,
            payload=build_label_payload(parsed, font),
            width=data["width"],
            height=data["height"],
            density=data["density"],
            rotate=data["rotate"],
            preview=data["preview"],
            device_id=device_id,
            context=call.context,
        )

    async def async_save_customer(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.save_customer is reserved for Phase 2")

    async def async_search_customers(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.search_customers is reserved for Phase 2")

    async def async_print_customer(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.print_customer is reserved for Phase 2")

    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_LABEL, async_print_label, schema=PRINT_LABEL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SAVE_CUSTOMER, async_save_customer, schema=SAVE_CUSTOMER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_CUSTOMERS,
        async_search_customers,
        schema=SEARCH_CUSTOMERS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PRINT_CUSTOMER,
        async_print_customer,
        schema=PRINT_CUSTOMER_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Store the printer settings selected in the config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = dict(entry.data)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BJP Label printer settings."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


def _parse_service_data(data: dict) -> ParsedLabel:
    if data.get("text", "").strip():
        try:
            return parse_customer_text(data["text"])
        except ParseError as err:
            raise ServiceValidationError(str(err)) from err

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    if not name or not phone:
        raise ServiceValidationError("กรุณาระบุ text หรือ name และ phone")
    return ParsedLabel(
        name=name,
        phone=phone,
        address=format_address_lines(data.get("address", "").strip().splitlines()),
        postal_code=data.get("postal_code", "").strip(),
    )
