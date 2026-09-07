"""The device every entity hangs off, so Home Assistant shows one StormDesk, not twenty."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StormDeskCoordinator


class StormDeskEntity(CoordinatorEntity[StormDeskCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: StormDeskCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.station_id or coordinator.host)},
            name=coordinator.station_name,
            manufacturer="StormDesk",
            model="Weather station",
            sw_version=(coordinator.data or {}).get("version"),
            # The device page gets a way back to the dashboard itself.
            configuration_url=coordinator.host,
        )
