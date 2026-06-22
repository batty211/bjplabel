"""Config flow for BJP Label."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    DeviceSelector,
    DeviceSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import CONF_DEVICE_ID, CONF_FONT, DEFAULT_FONT, DOMAIN


class BjpLabelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure BJP Label from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the single setup step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="BJP Label", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): DeviceSelector(
                    DeviceSelectorConfig(integration="niimbot")
                ),
                vol.Required(CONF_FONT, default=DEFAULT_FONT): TextSelector(
                    TextSelectorConfig()
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
