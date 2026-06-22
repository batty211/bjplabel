"""Label layout helpers for BJP Label."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import io
from typing import Protocol

from PIL import Image, ImageDraw, ImageFont

from .const import LABEL_SIZE_100X150, LABEL_SIZE_100X75


class LabelData(Protocol):
    """Data required to render one customer label."""

    name: str
    phone: str
    address: str
    postal_code: str


@dataclass(frozen=True)
class LabelPreset:
    """Canvas and layout settings for one label size."""

    width_mm: int
    height_mm: int
    canvas_width: int
    canvas_height: int
    name_box: tuple[int, int, int, int]
    phone_box: tuple[int, int, int, int]
    address_box: tuple[int, int, int, int]
    postal_box: tuple[int, int, int, int]
    name_size: int
    phone_size: int
    address_size: int
    postal_size: int
    address_spacing: int


LABEL_PRESETS: dict[str, LabelPreset] = {
    LABEL_SIZE_100X75: LabelPreset(
        width_mm=100,
        height_mm=75,
        canvas_width=800,
        canvas_height=600,
        name_box=(36, 26, 728, 94),
        phone_box=(36, 136, 728, 62),
        address_box=(36, 222, 728, 248),
        postal_box=(36, 500, 280, 56),
        name_size=66,
        phone_size=48,
        address_size=38,
        postal_size=50,
        address_spacing=12,
    ),
    LABEL_SIZE_100X150: LabelPreset(
        width_mm=100,
        height_mm=150,
        canvas_width=800,
        canvas_height=1200,
        name_box=(48, 40, 704, 118),
        phone_box=(48, 190, 704, 74),
        address_box=(48, 304, 704, 612),
        postal_box=(48, 970, 320, 72),
        name_size=78,
        phone_size=56,
        address_size=46,
        postal_size=58,
        address_spacing=16,
    ),
}


def get_label_preset(label_size: str) -> LabelPreset:
    """Return the render preset for one supported label size."""
    try:
        return LABEL_PRESETS[label_size]
    except KeyError as err:
        raise ValueError(f"ไม่รองรับขนาดฉลาก {label_size}") from err


def build_label_payload(parsed: LabelData, font: str) -> list[dict]:
    """Build the compact 640 x 384 Niimbot payload before rotation."""
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


def render_label_image(
    parsed: LabelData,
    *,
    font: str,
    label_size: str,
) -> Image.Image:
    """Render the label to a white monochrome-ready bitmap."""
    preset = get_label_preset(label_size)
    image = Image.new("L", (preset.canvas_width, preset.canvas_height), 255)
    draw = ImageDraw.Draw(image)

    _draw_single_line(
        draw,
        parsed.name,
        font,
        preset.name_box,
        preset.name_size,
        min_size=28,
    )
    _draw_single_line(
        draw,
        parsed.phone,
        font,
        preset.phone_box,
        preset.phone_size,
        min_size=24,
    )
    if parsed.address:
        _draw_multiline(
            draw,
            parsed.address,
            font,
            preset.address_box,
            preset.address_size,
            min_size=22,
            spacing=preset.address_spacing,
        )
    if parsed.postal_code:
        _draw_single_line(
            draw,
            parsed.postal_code,
            font,
            preset.postal_box,
            preset.postal_size,
            min_size=24,
        )

    return image


def render_label_png_data_url(
    parsed: LabelData,
    *,
    font: str,
    label_size: str,
) -> str:
    """Render the label to a PNG data URL for preview."""
    image = render_label_image(parsed, font=font, label_size=label_size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _draw_single_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    box: tuple[int, int, int, int],
    size: int,
    *,
    min_size: int,
) -> None:
    if not text:
        return

    x, y, width, height = box
    font = _fit_font(draw, text, font_path, width, height, size, min_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    top = y + max((height - (bbox[3] - bbox[1])) // 2, 0)
    draw.text((x, top), text, font=font, fill=0)


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    box: tuple[int, int, int, int],
    size: int,
    *,
    min_size: int,
    spacing: int,
) -> None:
    if not text:
        return

    x, y, width, height = box
    font, final_spacing = _fit_multiline_font(
        draw,
        text,
        font_path,
        width,
        height,
        size,
        min_size,
        spacing,
    )
    draw.multiline_text((x, y), text, font=font, fill=0, spacing=final_spacing)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    width: int,
    height: int,
    start_size: int,
    min_size: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= width and (bbox[3] - bbox[1]) <= height:
            return font
    return _load_font(font_path, min_size)


def _fit_multiline_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    width: int,
    height: int,
    start_size: int,
    min_size: int,
    spacing: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, int]:
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(font_path, size)
        line_spacing = max(int(spacing * size / max(start_size, 1)), 4)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=line_spacing)
        if (bbox[2] - bbox[0]) <= width and (bbox[3] - bbox[1]) <= height:
            return font, line_spacing
    return _load_font(font_path, min_size), max(int(spacing * min_size / max(start_size, 1)), 4)


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(font_path, size=size)
    except OSError as err:
        raise ValueError(f"ไม่พบฟอนต์ภาษาไทย {font_path}") from err
