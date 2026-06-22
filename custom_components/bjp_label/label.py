"""Niimbot payload layout for BJP Label."""

from __future__ import annotations

from typing import Protocol


class LabelData(Protocol):
    """Data required to render one customer label."""

    name: str
    phone: str
    address: str
    postal_code: str


def build_label_payload(parsed: LabelData, font: str) -> list[dict]:
    """Build a compact 640 x 384 payload before 90-degree rotation."""
    payload = [
        {
            "type": "new_multiline",
            "value": parsed.name,
            "font": font,
            "x": 20,
            "y": 12,
            "size": 46,
            "width": 600,
            "height": 62,
            "fit": True,
        },
        {
            "type": "text",
            "value": parsed.phone,
            "font": font,
            "x": 20,
            "y": 82,
            "size": 38,
        },
    ]
    if parsed.address:
        payload.append(
            {
                "type": "new_multiline",
                "value": parsed.address,
                "font": font,
                "x": 20,
                "y": 140,
                "size": 32,
                "spacing": 36,
                "width": 600,
                "height": 140 if parsed.postal_code else 220,
                "fit": True,
            }
        )
    if parsed.postal_code:
        payload.append(
            {
                "type": "text",
                "value": parsed.postal_code,
                "font": font,
                "x": 20,
                "y": 315,
                "size": 38,
            }
        )
    return payload
