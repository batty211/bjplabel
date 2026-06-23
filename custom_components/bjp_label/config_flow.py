"""Config flow for BJP Label."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    DeviceSelector,
    DeviceSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_DEVICE_ID,
    CONF_FONT,
    CONF_HOST,
    CONF_LABEL_SIZE,
    CONF_PORT,
    CONF_PRINTER_BACKEND,
    DEFAULT_FONT,
    DEFAULT_LABEL_SIZE,
    DEFAULT_PORT,
    DEFAULT_PRINTER_BACKEND,
    DOMAIN,
    LABEL_SIZE_100X150,
    LABEL_SIZE_100X75,
    PRINTER_BACKEND_NIIMBOT,
    PRINTER_BACKEND_XPRINTER_TSPL,
)


def _json_safe(value: Any) -> Any:
    """Convert flow values into JSON-safe debug output."""
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _write_flow_log(
    hass: HomeAssistant | None, event: str, **details: Any
) -> None:
    """Append config flow debug details to a file in the HA config directory."""
    if hass is not None:
        log_path = Path(hass.config.path(f"{DOMAIN}_config_flow.log"))
    else:
        log_path = Path(__file__).resolve().parents[2] / f"{DOMAIN}_config_flow.log"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **{key: _json_safe(value) for key, value in details.items()},
    }
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


class _BackendFlowMixin:
    """Shared backend-specific forms for setup and options flows."""

    _selected_backend: str

    def _backend_selector(self) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"label": "Niimbot", "value": PRINTER_BACKEND_NIIMBOT},
                    {
                        "label": "Xprinter XP-420B (TSPL)",
                        "value": PRINTER_BACKEND_XPRINTER_TSPL,
                    },
                ],
                mode="dropdown",
            )
        )

    def _niimbot_schema(self, defaults: Mapping[str, Any]) -> vol.Schema:
        fields: dict[Any, Any] = {
            vol.Required(
                CONF_PRINTER_BACKEND, default=PRINTER_BACKEND_NIIMBOT
            ): self._backend_selector(),
            vol.Required(
                CONF_FONT,
                default=defaults.get(CONF_FONT, DEFAULT_FONT),
            ): TextSelector(TextSelectorConfig()),
        }
        device_id = defaults.get(CONF_DEVICE_ID)
        if device_id:
            fields[
                vol.Optional(
                    CONF_DEVICE_ID,
                    default=device_id,
                )
            ] = DeviceSelector(DeviceSelectorConfig(integration="niimbot"))
        else:
            fields[vol.Optional(CONF_DEVICE_ID)] = DeviceSelector(
                DeviceSelectorConfig(integration="niimbot")
            )
        return vol.Schema(fields)

    def _xprinter_schema(self, defaults: Mapping[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_PRINTER_BACKEND, default=PRINTER_BACKEND_XPRINTER_TSPL
                ): self._backend_selector(),
                vol.Required(
                    CONF_HOST,
                    default=defaults.get(CONF_HOST, ""),
                ): TextSelector(TextSelectorConfig()),
                vol.Required(
                    CONF_PORT,
                    default=defaults.get(CONF_PORT, DEFAULT_PORT),
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_LABEL_SIZE,
                    default=defaults.get(CONF_LABEL_SIZE, DEFAULT_LABEL_SIZE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"label": "100 x 75 mm", "value": LABEL_SIZE_100X75},
                            {"label": "100 x 150 mm", "value": LABEL_SIZE_100X150},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Required(
                    CONF_FONT,
                    default=defaults.get(CONF_FONT, DEFAULT_FONT),
                ): TextSelector(TextSelectorConfig()),
            }
        )

    def _normalize_backend_data(self, user_input: Mapping[str, Any]) -> dict[str, Any]:
        backend = str(user_input[CONF_PRINTER_BACKEND])
        base: dict[str, Any] = {
            CONF_PRINTER_BACKEND: backend,
            CONF_FONT: str(user_input.get(CONF_FONT, DEFAULT_FONT)),
        }
        if backend == PRINTER_BACKEND_NIIMBOT:
            base[CONF_DEVICE_ID] = str(user_input.get(CONF_DEVICE_ID, ""))
            return base
        base[CONF_HOST] = str(user_input.get(CONF_HOST, "")).strip()
        base[CONF_PORT] = int(user_input.get(CONF_PORT, DEFAULT_PORT))
        base[CONF_LABEL_SIZE] = str(user_input.get(CONF_LABEL_SIZE, DEFAULT_LABEL_SIZE))
        return base

    def _validate_backend_input(self, user_input: Mapping[str, Any]) -> dict[str, str]:
        backend = str(user_input[CONF_PRINTER_BACKEND])
        if backend == PRINTER_BACKEND_NIIMBOT and not user_input.get(CONF_DEVICE_ID):
            return {CONF_DEVICE_ID: "required"}
        if backend == PRINTER_BACKEND_XPRINTER_TSPL and not str(
            user_input.get(CONF_HOST, "")
        ).strip():
            return {CONF_HOST: "required"}
        return {}


class BjpLabelConfigFlow(_BackendFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Configure BJP Label from the Home Assistant UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._selected_backend = DEFAULT_PRINTER_BACKEND

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return BjpLabelOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Pick the printer backend first."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._selected_backend = user_input[CONF_PRINTER_BACKEND]
            if self._selected_backend == PRINTER_BACKEND_XPRINTER_TSPL:
                return await self.async_step_xprinter()
            return await self.async_step_niimbot()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRINTER_BACKEND, default=DEFAULT_PRINTER_BACKEND
                ): self._backend_selector()
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors={})

    async def async_step_niimbot(self, user_input=None):
        """Configure a Niimbot-backed entry."""
        errors = {}
        defaults = {
            CONF_DEVICE_ID: "",
            CONF_FONT: DEFAULT_FONT,
        }
        if user_input is not None:
            errors = self._validate_backend_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title="BJP Label",
                    data=self._normalize_backend_data(user_input),
                )
            if user_input.get(CONF_PRINTER_BACKEND) == PRINTER_BACKEND_XPRINTER_TSPL:
                self._selected_backend = PRINTER_BACKEND_XPRINTER_TSPL
                return await self.async_step_xprinter(user_input)

        return self.async_show_form(
            step_id="niimbot",
            data_schema=self._niimbot_schema(defaults if user_input is None else user_input),
            errors=errors,
        )

    async def async_step_xprinter(self, user_input=None):
        """Configure an Xprinter-backed entry."""
        errors = {}
        defaults = {
            CONF_HOST: "",
            CONF_PORT: DEFAULT_PORT,
            CONF_LABEL_SIZE: DEFAULT_LABEL_SIZE,
            CONF_FONT: DEFAULT_FONT,
        }
        if user_input is not None:
            errors = self._validate_backend_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title="BJP Label",
                    data=self._normalize_backend_data(user_input),
                )
            if user_input.get(CONF_PRINTER_BACKEND) == PRINTER_BACKEND_NIIMBOT:
                self._selected_backend = PRINTER_BACKEND_NIIMBOT
                return await self.async_step_niimbot(user_input)

        return self.async_show_form(
            step_id="xprinter",
            data_schema=self._xprinter_schema(defaults if user_input is None else user_input),
            errors=errors,
        )


class BjpLabelOptionsFlow(config_entries.OptionsFlowWithReload, _BackendFlowMixin):
    """Edit BJP Label settings without deleting the entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._config_entry = config_entry
        self._selected_backend = str(
            self._config_entry.options.get(
                CONF_PRINTER_BACKEND,
                self._config_entry.data.get(
                    CONF_PRINTER_BACKEND, DEFAULT_PRINTER_BACKEND
                ),
            )
        )
        _write_flow_log(
            None,
            "options_flow_init",
            entry_id=config_entry.entry_id,
            selected_backend=self._selected_backend,
            data=dict(config_entry.data),
            options=dict(config_entry.options),
        )

    def _current_defaults(self) -> dict[str, Any]:
        return {
            **dict(self._config_entry.data),
            **dict(self._config_entry.options),
        }

    def _log_event(self, event: str, **details: Any) -> None:
        """Write a structured debug line for the options flow."""
        _write_flow_log(
            getattr(self, "hass", None),
            event,
            entry_id=self._config_entry.entry_id,
            selected_backend=self._selected_backend,
            **details,
        )

    def _save_backend_settings(
        self, user_input: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        normalized = self._normalize_backend_data(user_input)
        self._log_event(
            "options_save_start",
            user_input=user_input,
            normalized=normalized,
            previous_data=dict(self._config_entry.data),
            previous_options=dict(self._config_entry.options),
        )
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            data=normalized,
            options={},
        )
        self._log_event(
            "options_save_complete",
            stored_data=dict(self._config_entry.data),
            stored_options=dict(self._config_entry.options),
        )
        return self.async_create_entry(title="", data=None)

    async def async_step_init(self, user_input=None):
        """Pick which backend config to edit."""
        try:
            self._log_event(
                "options_step_init_enter",
                user_input=user_input,
                defaults=self._current_defaults(),
            )
            if user_input is not None:
                self._selected_backend = user_input[CONF_PRINTER_BACKEND]
                self._log_event(
                    "options_step_init_route",
                    next_backend=self._selected_backend,
                )
                if self._selected_backend == PRINTER_BACKEND_XPRINTER_TSPL:
                    return await self.async_step_xprinter()
                return await self.async_step_niimbot()

            defaults = self._current_defaults()
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_PRINTER_BACKEND,
                        default=defaults.get(
                            CONF_PRINTER_BACKEND, DEFAULT_PRINTER_BACKEND
                        ),
                    ): self._backend_selector()
                }
            )
            self._log_event("options_step_init_show_form", defaults=defaults)
            return self.async_show_form(step_id="init", data_schema=schema, errors={})
        except Exception:
            self._log_event(
                "options_step_init_exception",
                user_input=user_input,
                traceback=traceback.format_exc(),
            )
            raise

    async def async_step_niimbot(self, user_input=None):
        """Edit Niimbot settings."""
        try:
            errors = {}
            defaults = self._current_defaults()
            defaults[CONF_PRINTER_BACKEND] = PRINTER_BACKEND_NIIMBOT
            self._log_event(
                "options_step_niimbot_enter",
                user_input=user_input,
                defaults=defaults,
            )
            if user_input is not None:
                errors = self._validate_backend_input(user_input)
                self._log_event(
                    "options_step_niimbot_validated",
                    user_input=user_input,
                    errors=errors,
                )
                if not errors:
                    return self._save_backend_settings(user_input)
                if user_input.get(CONF_PRINTER_BACKEND) == PRINTER_BACKEND_XPRINTER_TSPL:
                    self._selected_backend = PRINTER_BACKEND_XPRINTER_TSPL
                    self._log_event("options_step_niimbot_switch_backend")
                    return await self.async_step_xprinter(user_input)

            self._log_event(
                "options_step_niimbot_show_form",
                defaults=defaults if user_input is None else user_input,
                errors=errors,
            )
            return self.async_show_form(
                step_id="niimbot",
                data_schema=self._niimbot_schema(
                    defaults if user_input is None else user_input
                ),
                errors=errors,
            )
        except Exception:
            self._log_event(
                "options_step_niimbot_exception",
                user_input=user_input,
                traceback=traceback.format_exc(),
            )
            raise

    async def async_step_xprinter(self, user_input=None):
        """Edit Xprinter settings."""
        try:
            errors = {}
            defaults = self._current_defaults()
            defaults[CONF_PRINTER_BACKEND] = PRINTER_BACKEND_XPRINTER_TSPL
            self._log_event(
                "options_step_xprinter_enter",
                user_input=user_input,
                defaults=defaults,
            )
            if user_input is not None:
                errors = self._validate_backend_input(user_input)
                self._log_event(
                    "options_step_xprinter_validated",
                    user_input=user_input,
                    errors=errors,
                )
                if not errors:
                    return self._save_backend_settings(user_input)
                if user_input.get(CONF_PRINTER_BACKEND) == PRINTER_BACKEND_NIIMBOT:
                    self._selected_backend = PRINTER_BACKEND_NIIMBOT
                    self._log_event("options_step_xprinter_switch_backend")
                    return await self.async_step_niimbot(user_input)

            self._log_event(
                "options_step_xprinter_show_form",
                defaults=defaults if user_input is None else user_input,
                errors=errors,
            )
            return self.async_show_form(
                step_id="xprinter",
                data_schema=self._xprinter_schema(
                    defaults if user_input is None else user_input
                ),
                errors=errors,
            )
        except Exception:
            self._log_event(
                "options_step_xprinter_exception",
                user_input=user_input,
                traceback=traceback.format_exc(),
            )
            raise
