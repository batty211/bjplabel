from __future__ import annotations

import logging
from textwrap import wrap

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import (
    DEFAULT_DENSITY,
    DEFAULT_FONT,
    DEFAULT_HEIGHT,
    DEFAULT_ROTATE,
    DEFAULT_WIDTH,
    DOMAIN,
    SERVICE_PRINT_CUSTOMER,
    SERVICE_PRINT_LABEL,
    SERVICE_SAVE_CUSTOMER,
    SERVICE_SEARCH_CUSTOMERS,
)

_LOGGER = logging.getLogger(__name__)

PRINT_LABEL_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("phone"): cv.string,
        vol.Required("address"): cv.string,
        vol.Optional("note", default=""): cv.string,
        vol.Optional("font", default=DEFAULT_FONT): cv.string,
        vol.Optional("width", default=DEFAULT_WIDTH): vol.Coerce(int),
        vol.Optional("height", default=DEFAULT_HEIGHT): vol.Coerce(int),
        vol.Optional("density", default=DEFAULT_DENSITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
        vol.Optional("rotate", default=DEFAULT_ROTATE): vol.All(vol.Coerce(int), vol.In([0, 90, 180, 270])),
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
    async def async_print_label(call: ServiceCall) -> None:
        data = call.data
        payload = _build_label_payload(
            name=data["name"],
            phone=data["phone"],
            address=data["address"],
            font=data["font"],
        )
        service_data = {
            "payload": payload,
            "width": data["width"],
            "height": data["height"],
            "density": data["density"],
            "rotate": data["rotate"],
        }
        if data["preview"]:
            service_data["preview"] = True

        target = {"device_id": data["device_id"]} if data.get("device_id") else getattr(call, "target", None)

        await hass.services.async_call(
            "niimbot",
            "print",
            service_data=service_data,
            target=target,
            blocking=True,
            context=call.context,
        )

    async def async_save_customer(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.save_customer is reserved for Phase 2 and does not persist data yet")

    async def async_search_customers(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.search_customers is reserved for Phase 2 and does not search data yet")

    async def async_print_customer(call: ServiceCall) -> None:
        _LOGGER.warning("bjp_label.print_customer is reserved for Phase 2 and does not load customers yet")

    hass.services.async_register(
        DOMAIN,
        SERVICE_PRINT_LABEL,
        async_print_label,
        schema=PRINT_LABEL_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_CUSTOMER,
        async_save_customer,
        schema=SAVE_CUSTOMER_SCHEMA,
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


def _build_label_payload(name: str, phone: str, address: str, font: str) -> list[dict]:
    address_lines = _address_lines(address)
    return [
        {
            "type": "text",
            "value": name.strip(),
            "font": font,
            "x": 24,
            "y": 18,
            "size": 34,
        },
        {
            "type": "text",
            "value": phone.strip(),
            "font": font,
            "x": 24,
            "y": 64,
            "size": 28,
        },
        {
            "type": "text",
            "value": address_lines[0],
            "font": font,
            "x": 24,
            "y": 106,
            "size": 22,
        },
        {
            "type": "text",
            "value": address_lines[1],
            "font": font,
            "x": 24,
            "y": 142,
            "size": 22,
        },
    ]


def _address_lines(address: str) -> list[str]:
    clean_address = " ".join(address.split())
    if not clean_address:
        return ["", ""]

    wrapped = wrap(clean_address, width=34, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) == 1:
        return [wrapped[0], ""]
    return [wrapped[0], " ".join(wrapped[1:])]
