"""Bluetooth discovery, manual setup and timeout options."""

import probatio as vol

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import (
    CONF_STALE_TIMEOUT, DEFAULT_STALE_TIMEOUT, DOMAIN,
    MAX_STALE_TIMEOUT, MIN_STALE_TIMEOUT, SERVICE_UUID,
)
from .parser import normalize_address, parse_payload


class GrillEyeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one validated device address."""

    VERSION = 1
    _address: str

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GrillEyeOptionsFlow()

    async def async_step_bluetooth(self, discovery_info):
        payload = discovery_info.manufacturer_data.get(0)
        if (
            SERVICE_UUID not in discovery_info.service_uuids
            or payload is None
            or parse_payload(payload, discovery_info.address) is None
        ):
            return self.async_abort(reason="not_supported")
        self._address = normalize_address(discovery_info.address)
        await self.async_set_unique_id(self._address)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"address": self._address}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"GrillEye Classic {self._address[-5:].replace(':', '')}",
                data={CONF_ADDRESS: self._address},
            )
        return self.async_show_form(
            step_id="confirm", data_schema=vol.Schema({}),
            description_placeholders={"address": self._address},
        )

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                address = normalize_address(user_input[CONF_ADDRESS].strip())
            except ValueError:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                info = bluetooth.async_last_service_info(self.hass, address, connectable=False)
                if info is not None and (
                    (payload := info.manufacturer_data.get(0)) is None
                    or parse_payload(payload, address) is None
                ):
                    errors["base"] = "not_supported"
                else:
                    return self.async_create_entry(
                        title=f"GrillEye Classic {address[-5:].replace(':', '')}",
                        data={CONF_ADDRESS: address},
                    )
        return self.async_show_form(
            step_id="user", errors=errors,
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
        )


class GrillEyeOptionsFlow(OptionsFlow):
    """Adjust the valid-measurement timeout."""

    async def async_step_init(self, user_input=None):
        schema = vol.Schema({
            vol.Required(CONF_STALE_TIMEOUT, default=self.config_entry.options.get(
                CONF_STALE_TIMEOUT, DEFAULT_STALE_TIMEOUT,
            )): vol.All(vol.Coerce(int), vol.Range(min=MIN_STALE_TIMEOUT, max=MAX_STALE_TIMEOUT)),
        })
        if user_input is not None:
            try:
                data = schema(user_input)
            except vol.Invalid:
                return self.async_show_form(
                    step_id="init", data_schema=schema, errors={"base": "invalid_timeout"},
                )
            return self.async_create_entry(title="", data=data)
        return self.async_show_form(step_id="init", data_schema=schema)
