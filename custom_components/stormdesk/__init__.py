"""StormDesk — a local weather station dashboard, on the Home Assistant bus.

There are two ways to get a StormDesk station into Home Assistant, and they answer different
questions. The MQTT route needs a broker but no custom code, and it is what most people already
have. This integration needs no broker at all: it polls the dashboard's own /api/v1 and adds the
one thing MQTT discovery cannot express — a weather entity with a forecast, which is what the
forecast card on a Lovelace dashboard wants.

Running both is fine. They are separate devices in Home Assistant and neither writes to the
other's entities.
"""

from __future__ import annotations

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_URL
from .coordinator import StormDeskCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = StormDeskCoordinator(hass, entry.data[CONF_HOST])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _add_panel(hass, coordinator.host)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


def _add_panel(hass: HomeAssistant, host: str) -> None:
    """The dashboard itself, in the sidebar.

    An iframe rather than a custom Lovelace card: the dashboard is a whole application with its
    own layout engine, and reimplementing any part of it as a card would be two things to keep in
    step. Hide the entry like any other sidebar item if it is not wanted.

    A Home Assistant served over https cannot frame a dashboard served over http — browsers block
    the mixed content and the panel is blank. That is a browser rule, not something this can work
    around; put the dashboard behind the same kind of URL, or drop the panel.
    """
    if PANEL_URL in hass.data.get("frontend_panels", {}):
        return
    frontend.async_register_built_in_panel(
        hass,
        "iframe",
        sidebar_title="StormDesk",
        sidebar_icon="mdi:weather-partly-cloudy",
        frontend_url_path=PANEL_URL,
        config={"url": host},
        require_admin=False,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Only the last station takes the sidebar entry with it — a house with two dashboards
        # configured should not lose the panel when one is removed.
        if not hass.data[DOMAIN]:
            frontend.async_remove_panel(hass, PANEL_URL)
    return unloaded


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
