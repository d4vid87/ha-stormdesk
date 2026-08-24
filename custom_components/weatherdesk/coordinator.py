"""Fetch /api/v1 once per interval and hand the same payload to every entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_PATH, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WeatherDeskCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """One request per interval, shared by the weather entity and every sensor.

    A sensor per field polling for itself would be twenty requests a minute at one dashboard,
    which is rude to a machine that is also drawing a radar loop.
    """

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.host = host.rstrip("/")
        self._session = async_get_clientsession(hass)

    @property
    def url(self) -> str:
        return f"{self.host}{API_PATH}"

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with self._session.get(self.url, timeout=20) as response:
                if response.status != 200:
                    raise UpdateFailed(f"HTTP {response.status} from {self.host}")
                payload = await response.json(content_type=None)
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001 - aiohttp raises a family of these
            raise UpdateFailed(f"cannot reach {self.host}") from err

        if not isinstance(payload, dict) or "current" not in payload:
            raise UpdateFailed(f"{self.host} answered something that is not a WeatherDesk")
        return payload

    @property
    def station_id(self) -> str:
        return str((self.data or {}).get("station", {}).get("id") or "")

    @property
    def station_name(self) -> str:
        return (self.data or {}).get("station", {}).get("name") or "WeatherDesk"

    def value(self, field: str) -> Any:
        """One reading, or None. A field the station does not measure is null, not missing."""
        return ((self.data or {}).get("current") or {}).get(field)
