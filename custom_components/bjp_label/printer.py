"""Printer backend boundary for BJP Label."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from functools import partial
from typing import Any

from PIL import Image

from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_LABEL_SIZE,
    CONF_PORT,
    CONF_PRINTER_BACKEND,
    DEFAULT_DENSITY,
    DEFAULT_HEIGHT,
    DEFAULT_LABEL_SIZE,
    DEFAULT_PORT,
    DEFAULT_PRINTER_BACKEND,
    DEFAULT_ROTATE,
    DEFAULT_WIDTH,
    PRINTER_BACKEND_NIIMBOT,
    PRINTER_BACKEND_XPRINTER_TSPL,
)
from .label import build_label_payload, get_label_preset, render_label_image


@dataclass(frozen=True)
class PrintConfig:
    """Resolved printer settings for one print request."""

    backend: str
    device_id: str
    host: str
    port: int
    label_size: str
    width: int
    height: int
    density: int
    rotate: int


def resolve_print_config(data: dict[str, Any], settings: dict[str, Any]) -> PrintConfig:
    """Resolve service overrides against integration defaults."""
    backend = str(
        data.get(CONF_PRINTER_BACKEND)
        or settings.get(CONF_PRINTER_BACKEND)
        or DEFAULT_PRINTER_BACKEND
    )
    config = PrintConfig(
        backend=backend,
        device_id=str(data.get(CONF_DEVICE_ID) or settings.get(CONF_DEVICE_ID) or ""),
        host=str(data.get(CONF_HOST) or settings.get(CONF_HOST) or ""),
        port=int(data.get(CONF_PORT) or settings.get(CONF_PORT) or DEFAULT_PORT),
        label_size=str(
            data.get(CONF_LABEL_SIZE) or settings.get(CONF_LABEL_SIZE) or DEFAULT_LABEL_SIZE
        ),
        width=int(data.get("width", settings.get("width", DEFAULT_WIDTH))),
        height=int(data.get("height", settings.get("height", DEFAULT_HEIGHT))),
        density=int(data.get("density", settings.get("density", DEFAULT_DENSITY))),
        rotate=int(data.get("rotate", settings.get("rotate", DEFAULT_ROTATE))),
    )
    if backend == PRINTER_BACKEND_XPRINTER_TSPL:
        return PrintConfig(
            backend=config.backend,
            device_id="",
            host=config.host,
            port=config.port,
            label_size=config.label_size,
            width=config.width,
            height=config.height,
            density=config.density,
            rotate=0,
        )
    return PrintConfig(
        backend=config.backend,
        device_id=config.device_id,
        host="",
        port=config.port,
        label_size=DEFAULT_LABEL_SIZE,
        width=config.width,
        height=config.height,
        density=config.density,
        rotate=config.rotate,
    )


async def async_print_label(
    hass: Any,
    *,
    parsed: Any,
    font: str,
    config: PrintConfig,
    preview: bool,
    context: Any,
    return_response: bool = False,
) -> dict | None:
    """Dispatch the print request to the configured backend."""
    if config.backend == PRINTER_BACKEND_NIIMBOT:
        if not config.device_id:
            raise ValueError("ยังไม่ได้ตั้งค่าเครื่องพิมพ์ Niimbot")
        return await async_print_niimbot(
            hass,
            payload=build_label_payload(parsed, font),
            width=config.width,
            height=config.height,
            density=config.density,
            rotate=config.rotate,
            preview=preview,
            device_id=config.device_id,
            context=context,
            return_response=return_response,
        )

    if config.backend == PRINTER_BACKEND_XPRINTER_TSPL:
        if not config.host:
            raise ValueError("ยังไม่ได้ตั้งค่า IP หรือโฮสต์ของ Xprinter")
        return await async_print_xprinter_tspl(
            hass,
            parsed=parsed,
            font=font,
            label_size=config.label_size,
            host=config.host,
            port=config.port,
            preview=preview,
            return_response=return_response,
        )

    raise ValueError(f"ไม่รองรับเครื่องพิมพ์แบบ {config.backend}")


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


async def async_print_xprinter_tspl(
    hass: Any,
    *,
    parsed: Any,
    font: str,
    label_size: str,
    host: str,
    port: int,
    preview: bool,
    return_response: bool = False,
) -> dict | None:
    """Render and send the label to an Xprinter XP-420B using TSPL."""
    image = await _async_render_image(hass, parsed=parsed, font=font, label_size=label_size)
    preview_image = _image_to_data_url(image)
    if preview:
        return {"image": preview_image} if return_response else None

    command = _build_tspl_command(image, label_size=label_size)
    await _async_send_to_xprinter(host=host, port=port, command=command)
    return {"image": preview_image} if return_response else None


async def _async_render_image(
    hass: Any,
    *,
    parsed: Any,
    font: str,
    label_size: str,
) -> Image.Image:
    if hasattr(hass, "async_add_executor_job"):
        return await hass.async_add_executor_job(
            partial(
                render_label_image,
                parsed,
                font=font,
                label_size=label_size,
            )
        )
    return render_label_image(parsed, font=font, label_size=label_size)


def _image_to_data_url(image: Image.Image) -> str:
    import io

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _build_tspl_command(image: Image.Image, *, label_size: str) -> bytes:
    preset = get_label_preset(label_size)
    monochrome = image.convert("1")
    width_bytes = (monochrome.width + 7) // 8
    padded_width = width_bytes * 8
    if padded_width != monochrome.width:
        padded = Image.new("1", (padded_width, monochrome.height), 1)
        padded.paste(monochrome, (0, 0))
        monochrome = padded

    bitmap = monochrome.tobytes()
    header = [
        f"SIZE {preset.width_mm} mm,{preset.height_mm} mm",
        "GAP 2 mm,0 mm",
        "DIRECTION 1",
        "CLS",
    ]
    command = bytearray("\r\n".join(header).encode("ascii") + b"\r\n")
    command.extend(
        f"BITMAP 0,0,{width_bytes},{monochrome.height},0,".encode("ascii")
    )
    command.extend(bitmap)
    command.extend(b"\r\nPRINT 1,1\r\n")
    return bytes(command)


async def _async_send_to_xprinter(*, host: str, port: int, command: bytes) -> None:
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=10
        )
        del reader
        writer.write(command)
        await asyncio.wait_for(writer.drain(), timeout=10)
    except TimeoutError as err:
        raise RuntimeError("เครื่องพิมพ์ Xprinter ไม่ตอบสนอง") from err
    except OSError as err:
        raise RuntimeError("เชื่อมต่อ Xprinter ไม่สำเร็จ กรุณาตรวจสอบ IP และเครือข่าย") from err
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
