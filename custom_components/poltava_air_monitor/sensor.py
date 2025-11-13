"""Sensor platform for Poltava Air Monitor."""

from __future__ import annotations

import html
import logging
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_POST_NAME,
    DOMAIN,
    SENSOR_NAME_MAPPING,
    SENSOR_TYPE_AQI,
    SENSOR_TYPE_CO,
    SENSOR_TYPE_HUMIDITY,
    SENSOR_TYPE_NO2,
    SENSOR_TYPE_OZONE,
    SENSOR_TYPE_PM1,
    SENSOR_TYPE_PM10,
    SENSOR_TYPE_PM25,
    SENSOR_TYPE_PRESSURE,
    SENSOR_TYPE_SO2,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_WIND_DIRECTION,
    SENSOR_TYPE_WIND_SPEED,
)
from .coordinator import PoltavaAirMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities from text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_sensor_type_from_name(name: str) -> str | None:
    """Determine sensor type from Ukrainian parameter name."""
    clean_name = clean_html(name)
    
    for key, sensor_type in SENSOR_NAME_MAPPING.items():
        if key in clean_name:
            return sensor_type
    
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Poltava Air Monitor sensors from a config entry."""
    coordinator: PoltavaAirMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("Setting up sensors for entry: %s", entry.entry_id)
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    entities: list[PoltavaAirMonitorSensor] = []
    
    # Add AQI sensor
    entities.append(
        PoltavaAirMonitorAQISensor(
            coordinator=coordinator,
            entry=entry,
        )
    )
    _LOGGER.debug("Added AQI sensor")
    
    # Add parameter sensors from the data
    if coordinator.data and "params" in coordinator.data:
        _LOGGER.debug("Found %d params in coordinator data", len(coordinator.data["params"]))
        # Create sensors based on actual data
        for param in coordinator.data["params"]:
            sensor_type = get_sensor_type_from_name(param["name"])
            
            if sensor_type:
                _LOGGER.debug("Creating sensor for %s (type: %s)", param["name"], sensor_type)
                entities.append(
                    PoltavaAirMonitorParameterSensor(
                        coordinator=coordinator,
                        entry=entry,
                        param_name=param["name"],
                        sensor_type=sensor_type,
                    )
                )
            else:
                _LOGGER.warning("Unknown sensor type for parameter: %s", param["name"])
    else:
        # No data yet - create default sensors that will populate when data arrives
        _LOGGER.warning("No coordinator data available yet, creating default sensors")
        _LOGGER.debug("coordinator.data = %s", coordinator.data)
        
        # Create all standard sensor types
        default_sensors = [
            (SENSOR_TYPE_PM25, "ТЧ2,5,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_PM10, "ТЧ10,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_PM1, "ТЧ1,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_OZONE, "Озон – O<sub>3</sub>,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_NO2, "Діоксид азоту – NO<sub>2</sub>,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_SO2, "Діоксид сірки – SO<sub>2</sub>,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_CO, "Оксид вуглецю – CO,&nbsp;мкг/м<sup>3</sup>"),
            (SENSOR_TYPE_TEMPERATURE, "Температура повітря, °С"),
            (SENSOR_TYPE_HUMIDITY, "Вологість, %"),
            (SENSOR_TYPE_PRESSURE, "Тиск, кПа"),
            (SENSOR_TYPE_WIND_SPEED, "Швидкість вітру, м/с"),
            (SENSOR_TYPE_WIND_DIRECTION, "Напрям вітру, °"),
        ]
        
        for sensor_type, param_name in default_sensors:
            _LOGGER.debug("Creating default sensor for %s", sensor_type)
            entities.append(
                PoltavaAirMonitorParameterSensor(
                    coordinator=coordinator,
                    entry=entry,
                    param_name=param_name,
                    sensor_type=sensor_type,
                )
            )
    
    _LOGGER.info("Adding %d entities to Home Assistant", len(entities))
    async_add_entities(entities)


class PoltavaAirMonitorSensor(CoordinatorEntity[PoltavaAirMonitorCoordinator], SensorEntity):
    """Base class for Poltava Air Monitor sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoltavaAirMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_POST_NAME, "Poltava Air Monitor"),
            "manufacturer": "Poltava City",
            "model": "Air Quality Monitor",
            "entry_type": "service",
        }


class PoltavaAirMonitorAQISensor(PoltavaAirMonitorSensor):
    """Air Quality Index sensor."""

    _attr_icon = "mdi:air-filter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PoltavaAirMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the AQI sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_aqi"
        self._attr_name = "Air Quality Index"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("value")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        return {
            "index": self.coordinator.data.get("index"),
            "description": self.coordinator.data.get("qualityDesc"),
            "recommendation": self.coordinator.data.get("qualityRecommendation"),
            "updated": self.coordinator.data.get("updated"),
            "station_name": self.coordinator.data.get("name"),
            "station_address": self.coordinator.data.get("address"),
            "station_type": self.coordinator.data.get("description"),
        }


class PoltavaAirMonitorParameterSensor(PoltavaAirMonitorSensor):
    """Parameter sensor for specific air quality measurements."""

    def __init__(
        self,
        coordinator: PoltavaAirMonitorCoordinator,
        entry: ConfigEntry,
        param_name: str,
        sensor_type: str,
    ) -> None:
        """Initialize the parameter sensor."""
        super().__init__(coordinator, entry)
        self._param_name = param_name
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        
        # Configure sensor based on type
        self._configure_sensor()

    def _configure_sensor(self) -> None:
        """Configure sensor attributes based on type."""
        # Helper function to safely get device class
        def get_device_class(attr_name: str):
            """Get device class if it exists."""
            try:
                return getattr(SensorDeviceClass, attr_name, None)
            except AttributeError:
                return None
        
        config = {
            SENSOR_TYPE_PM25: {
                "name": "PM2.5",
                "icon": "mdi:dots-hexagon",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("PM25"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_PM10: {
                "name": "PM10",
                "icon": "mdi:dots-hexagon",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("PM10"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_PM1: {
                "name": "PM1",
                "icon": "mdi:dots-hexagon",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("PM1"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_OZONE: {
                "name": "Ozone",
                "icon": "mdi:molecule",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("OZONE"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_NO2: {
                "name": "Nitrogen Dioxide",
                "icon": "mdi:molecule",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("NITROGEN_DIOXIDE"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_SO2: {
                "name": "Sulfur Dioxide",
                "icon": "mdi:molecule",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("SULPHUR_DIOXIDE"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_CO: {
                "name": "Carbon Monoxide",
                "icon": "mdi:molecule-co",
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "device_class": get_device_class("CARBON_MONOXIDE") or get_device_class("CO"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_TEMPERATURE: {
                "name": "Temperature",
                "icon": "mdi:thermometer",
                "unit": UnitOfTemperature.CELSIUS,
                "device_class": get_device_class("TEMPERATURE"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_HUMIDITY: {
                "name": "Humidity",
                "icon": "mdi:water-percent",
                "unit": PERCENTAGE,
                "device_class": get_device_class("HUMIDITY"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_PRESSURE: {
                "name": "Pressure",
                "icon": "mdi:gauge",
                "unit": UnitOfPressure.HPA,
                "device_class": get_device_class("ATMOSPHERIC_PRESSURE"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_WIND_SPEED: {
                "name": "Wind Speed",
                "icon": "mdi:weather-windy",
                "unit": UnitOfSpeed.METERS_PER_SECOND,
                "device_class": get_device_class("WIND_SPEED"),
                "state_class": SensorStateClass.MEASUREMENT,
            },
            SENSOR_TYPE_WIND_DIRECTION: {
                "name": "Wind Direction",
                "icon": "mdi:compass",
                "unit": "°",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        }
        
        sensor_config = config.get(self._sensor_type, {})
        
        self._attr_name = sensor_config.get("name", self._sensor_type.replace("_", " ").title())
        self._attr_icon = sensor_config.get("icon")
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")

    def _get_param_data(self) -> dict[str, Any] | None:
        """Get parameter data from coordinator."""
        if not self.coordinator.data or "params" not in self.coordinator.data:
            return None
        
        for param in self.coordinator.data["params"]:
            if get_sensor_type_from_name(param["name"]) == self._sensor_type:
                return param
        
        return None

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        param_data = self._get_param_data()
        if param_data:
            current_value = param_data.get("currentValue")
            # Return None for 0 values if they seem invalid (especially for wind)
            if current_value == 0 and self._sensor_type in [
                SENSOR_TYPE_WIND_SPEED,
                SENSOR_TYPE_WIND_DIRECTION,
                SENSOR_TYPE_OZONE,
            ]:
                # Check if it's truly 0 or just unavailable
                if param_data.get("avgDailyValue") == 0 and param_data.get("qualityIndex") == 0:
                    return None
            return current_value
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        param_data = self._get_param_data()
        if not param_data:
            return {}
        
        attrs = {
            "daily_average": param_data.get("avgDailyValue"),
        }
        
        # Add quality index if it's not 0
        quality_index = param_data.get("qualityIndex")
        if quality_index and quality_index > 0:
            attrs["quality_index"] = quality_index
        
        return attrs

