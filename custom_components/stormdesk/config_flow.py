"""Setup, by discovery or by typing an address.

StormDesk announces itself on the LAN as `_stormdesk._tcp`, so the usual path is Home
Assistant offering it before anyone goes looking for an IP address. The manual path is for a
dashboard on another subnet, or in a container with host networking off, where mDNS does not
carry.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import API_PATH, DOMAIN


async def _probe(hass, host: str) -> dict[str, Any] | None:
    """Is a StormDesk actually there? Returns its station block, or None."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{host.rstrip('/')}{API_PATH}", timeout=15) as response:
            if response.status != 200:
                return None
            payload = await response.json(content_type=None)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(payload, dict) or "current" not in payload:
        return None
    return payload.get("station") or {}


class StormDeskConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if "://" not in host:
                host = f"http://{host}"
            station = await _probe(self.hass, host)
            if station is None:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(station.get("id") or host))
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=station.get("name") or "StormDesk", data={CONF_HOST: host}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        host = f"http://{discovery_info.host}:{discovery_info.port}"
        station = await _probe(self.hass, host)
        if station is None:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(str(station.get("id") or host))
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._host = host
        self._name = station.get("name") or "StormDesk"
        # Without this the discovered card in the UI is titled with the domain rather than the
        # station, which is unhelpful in a house with two of them.
        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._name or "StormDesk", data={CONF_HOST: self._host}
            )
        return self.async_show_form(
            step_id="confirm", description_placeholders={"name": self._name or "StormDesk"}
        )
