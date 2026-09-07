"""One sensor per reading the station actually takes.

The payload is SI and says so, which is why every description below states a native unit and lets
Home Assistant convert. A dashboard set to °F must never rewrite months of Home Assistant history,
so the wire never carries display units.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    LIGHT_LUX,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import StormDeskEntity


@dataclass(frozen=True, kw_only=True)
class StormDeskSensor(SensorEntityDescription):
    """A reading, and where to find it in the payload."""

    field: str


MEASURE = SensorStateClass.MEASUREMENT

SENSORS: tuple[StormDeskSensor, ...] = (
    StormDeskSensor(
        key="temp", field="temp", translation_key="temp",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    StormDeskSensor(
        key="feels_like", field="feels_like", translation_key="feels_like",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    StormDeskSensor(
        key="humidity", field="humidity", translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY, state_class=MEASURE,
        native_unit_of_measurement=PERCENTAGE,
    ),
    StormDeskSensor(
        key="pressure", field="pressure", translation_key="pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
    ),
    StormDeskSensor(
        key="pressure_trend", field="pressure_trend", translation_key="pressure_trend",
    ),
    StormDeskSensor(
        key="wind_avg", field="wind_avg", translation_key="wind_avg",
        device_class=SensorDeviceClass.WIND_SPEED, state_class=MEASURE,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    StormDeskSensor(
        key="wind_gust", field="wind_gust", translation_key="wind_gust",
        device_class=SensorDeviceClass.WIND_SPEED, state_class=MEASURE,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    StormDeskSensor(
        key="wind_lull", field="wind_lull", translation_key="wind_lull",
        device_class=SensorDeviceClass.WIND_SPEED, state_class=MEASURE,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    StormDeskSensor(
        key="wind_dir", field="wind_dir", translation_key="wind_dir",
        state_class=MEASURE, native_unit_of_measurement=DEGREE,
    ),
    StormDeskSensor(
        key="uv", field="uv", translation_key="uv", state_class=MEASURE,
    ),
    StormDeskSensor(
        key="solar", field="solar", translation_key="solar",
        device_class=SensorDeviceClass.IRRADIANCE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
    ),
    StormDeskSensor(
        key="lux", field="lux", translation_key="lux",
        device_class=SensorDeviceClass.ILLUMINANCE, state_class=MEASURE,
        native_unit_of_measurement=LIGHT_LUX,
    ),
    StormDeskSensor(
        key="rain", field="rain", translation_key="rain",
        device_class=SensorDeviceClass.PRECIPITATION, state_class=MEASURE,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
    ),
    StormDeskSensor(
        key="day_rain", field="day_rain", translation_key="day_rain",
        device_class=SensorDeviceClass.PRECIPITATION,
        # Resets at local midnight, which is exactly what total_increasing is for — the statistics
        # engine treats the drop to zero as a new day rather than as a meter running backwards.
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
    ),
    StormDeskSensor(
        key="strikes", field="strikes", translation_key="strikes", state_class=MEASURE,
    ),
    StormDeskSensor(
        key="strike_dist", field="strike_dist", translation_key="strike_dist",
        device_class=SensorDeviceClass.DISTANCE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
    ),
    StormDeskSensor(
        key="battery", field="battery", translation_key="battery",
        device_class=SensorDeviceClass.VOLTAGE, state_class=MEASURE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    current = (coordinator.data or {}).get("current") or {}
    # Only what this station reports. An Ecowitt has no lightning sensor, and thirteen entities
    # permanently showing "unknown" is how an integration earns a reputation.
    async_add_entities(
        StormDeskSensorEntity(coordinator, description)
        for description in SENSORS
        if current.get(description.field) is not None
    )


class StormDeskSensorEntity(StormDeskEntity, SensorEntity):
    entity_description: StormDeskSensor

    def __init__(self, coordinator, description: StormDeskSensor) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id or coordinator.host}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.coordinator.value(self.entity_description.field)
