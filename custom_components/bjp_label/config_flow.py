"""Config flow for BJP Label."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
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


class BjpLabelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure BJP Label from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the single setup step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}

        if user_input is not None:
            backend = user_input[CONF_PRINTER_BACKEND]
            if backend == PRINTER_BACKEND_NIIMBOT and not user_input.get(CONF_DEVICE_ID):
                errors[CONF_DEVICE_ID] = "required"
            if backend == PRINTER_BACKEND_XPRINTER_TSPL and not str(
                user_input.get(CONF_HOST, "")
            ).strip():
                errors[CONF_HOST] = "required"
            if not errors:
                return self.async_create_entry(title="BJP Label", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRINTER_BACKEND, default=DEFAULT_PRINTER_BACKEND
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {
                                "label": "Niimbot",
                                "value": PRINTER_BACKEND_NIIMBOT,
                            },
                            {
                                "label": "Xprinter XP-420B (TSPL)",
                                "value": PRINTER_BACKEND_XPRINTER_TSPL,
                            },
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(CONF_DEVICE_ID): DeviceSelector(
                    DeviceSelectorConfig(integration="niimbot")
                ),
                vol.Optional(CONF_HOST): TextSelector(TextSelectorConfig()),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_LABEL_SIZE, default=DEFAULT_LABEL_SIZE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"label": "100 x 75 mm", "value": LABEL_SIZE_100X75},
                            {"label": "100 x 150 mm", "value": LABEL_SIZE_100X150},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Required(CONF_FONT, default=DEFAULT_FONT): TextSelector(
                    TextSelectorConfig()
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
