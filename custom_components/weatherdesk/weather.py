"""The weather entity — the one thing MQTT discovery cannot express.

Home Assistant's MQTT discovery has no weather platform, so a station published over MQTT is a
pile of sensors with no forecast card behind it. This entity is the reason to install a custom
component at all: current conditions from the station in the garden, and the five-day forecast the
dashboard already fetches, in one thing the standard forecast card can draw.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import WeatherDeskEntity

# WMO code to the condition names Home Assistant draws. Two codes map to `partlycloudy` and three
# to `rainy`; the table is the one open-meteo publishes, not a guess.
WMO: dict[int, str] = {
    0: "sunny", 1: "sunny", 2: "partlycloudy", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "rainy", 53: "rainy", 55: "rainy",
    56: "rainy", 57: "rainy",
    61: "rainy", 63: "rainy", 65: "pouring",
    66: "rainy", 67: "pouring",
    71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
    80: "rainy", 81: "rainy", 82: "pouring",
    85: "snowy", 86: "snowy",
    95: "lightning", 96: "lightning-rainy", 99: "lightning-rainy",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([WeatherDeskWeather(hass.data[DOMAIN][entry.entry_id])])


class WeatherDeskWeather(WeatherDeskEntity, WeatherEntity):
    _attr_name = None  # the device's own name is the entity's name
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id or coordinator.host}_weather"

    @property
    def _days(self) -> list[dict[str, Any]]:
        return ((self.coordinator.data or {}).get("forecast") or {}).get("days") or []

    @property
    def condition(self) -> str | None:
        # Today's forecast code. The station measures the air, not the sky — nothing in the
        # archive says whether it is cloudy.
        if not self._days:
            return None
        return WMO.get(self._days[0].get("wmo_code"))

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.value("temp")

    @property
    def native_apparent_temperature(self) -> float | None:
        return self.coordinator.value("feels_like")

    @property
    def humidity(self) -> float | None:
        return self.coordinator.value("humidity")

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.value("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.value("wind_avg")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self.coordinator.value("wind_gust")

    @property
    def wind_bearing(self) -> float | None:
        return self.coordinator.value("wind_dir")

    @property
    def uv_index(self) -> float | None:
        return self.coordinator.value("uv")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        out: list[Forecast] = []
        for day in self._days:
            at = day.get("at")
            if at is None:
                continue
            out.append(
                Forecast(
                    datetime=datetime.fromtimestamp(at, tz=timezone.utc).isoformat(),
                    condition=WMO.get(day.get("wmo_code")),
                    native_temperature=day.get("high_c"),
                    native_templow=day.get("low_c"),
                    precipitation_probability=day.get("precip_chance"),
                )
            )
        return out or None
