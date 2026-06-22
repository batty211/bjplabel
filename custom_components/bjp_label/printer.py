"""Printer backend boundary for BJP Label."""

from __future__ import annotations

from typing import Any


async def async_print_niimbot(
    hass: Any,
    *,
    payload: list[dict],
    width: int,
    height: int,
    density: int,
    rotate: int,
    preview: bool,
    device_id: str,
    context: Any,
    return_response: bool = False,
) -> dict | None:
    """Send a rendered label through the existing hass-niimbot service."""
    service_data = {
        "payload": payload,
        "width": width,
        "height": height,
        "density": density,
        "rotate": rotate,
    }
    if preview:
        service_data["preview"] = True

    return await hass.services.async_call(
        "niimbot",
        "print",
        service_data=service_data,
        target={"device_id": device_id},
        blocking=True,
        context=context,
        return_response=return_response,
    )
