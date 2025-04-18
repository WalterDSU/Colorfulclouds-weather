"""Support for the Colorfulclouds service."""
import logging

from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    CONF_NAME,
)
import time

from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_ICON,
    ATTR_LABEL,
    ATTRIBUTION,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    NAME,
    OPTIONAL_SENSORS,
    SENSOR_TYPES,
)

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add Colorfulclouds entities from a config_entry."""
    name = config_entry.data[CONF_NAME]

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    sensors = []
    for sensor in SENSOR_TYPES:
        sensors.append(ColorfulcloudsSensor(name, sensor, coordinator))

    # if coordinator.forecast:
    #     for sensor in FORECAST_SENSOR_TYPES:
    #         for day in FORECAST_DAYS:
    #             # Some air quality/allergy sensors are only available for certain
    #             # locations.
    #             if sensor in coordinator.data[ATTR_FORECAST][0]:
    #                 sensors.append(
    #                     ColorfulcloudsSensor(name, sensor, coordinator, forecast_day=day)
    #                 )

    async_add_entities(sensors, False)


class ColorfulcloudsSensor(Entity):
    """Define an Colorfulclouds entity."""

    def __init__(self, name, kind, coordinator, forecast_day=None):
        """Initialize."""
        self._name = name
        self.kind = kind
        self.coordinator = coordinator
        self._device_class = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._unit_system = "Metric" if self.coordinator.data["is_metric"]=="metric:v2" else "Imperial"
        self.forecast_day = forecast_day

    @property
    def name(self):
        """Return the name."""
        if self.forecast_day is not None:
            return f"{self._name} {FORECAST_SENSOR_TYPES[self.kind][ATTR_LABEL]} {self.forecast_day}d"
        return f"{self._name} {SENSOR_TYPES[self.kind][ATTR_LABEL]}"

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        # if self.forecast_day is not None:
        #     return f"{self.coordinator.location_key}-{self.kind}-{self.forecast_day}".lower()
        _LOGGER.info("sensor_unique_id: %s-%s", self.coordinator.data["location_key"], self.kind)
        return f"{self.coordinator.data['location_key']}-{self.kind}".lower()

    @property
    def device_info(self):
        """Return the device info."""
        info = {
            "identifiers": {(DOMAIN, self.coordinator.data["location_key"])},
            "name": self._name,
            "manufacturer": MANUFACTURER,
        }
        # LEGACY can be removed when min HA version is 2021.12
        info = {
            "identifiers": {(DOMAIN, self.coordinator.data["location_key"])},
            "name": self._name,
            "manufacturer": MANUFACTURER,
        }        
        from homeassistant.helpers.device_registry import DeviceEntryType
        info["entry_type"] = DeviceEntryType.SERVICE        
        return info

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        #return self.coordinator.last_update_success
        return (int(datetime.now().timestamp()) - int(self.coordinator.data["server_time"]) < 1800)

    @property
    def state(self):
        """Return the state."""
        if self.kind == "apparent_temperature":
            return self.coordinator.data["result"]["realtime"][self.kind]
        if self.kind == "pressure":
            return round(float(self.coordinator.data["result"]["realtime"][self.kind])/100)
        if self.kind == "temperature":
            return self.coordinator.data["result"]["realtime"][self.kind]
        if self.kind == "humidity":
            return round(float(self.coordinator.data["result"]["realtime"][self.kind])*100)
        if self.kind == "cloudrate":
            return self.coordinator.data["result"]["realtime"][self.kind]
        if self.kind == "visibility":
            return self.coordinator.data["result"]["realtime"][self.kind]
        if self.kind == "WindSpeed":
            return self.coordinator.data["result"]["realtime"]["wind"]["speed"]
        if self.kind == "WindDirection":
            return self.coordinator.data["result"]["realtime"]["wind"]["direction"]
        if self.kind == "comfort":
            return self.coordinator.data["result"]["realtime"]["life_index"]["comfort"]["index"]
        if self.kind == "ultraviolet":
            return self.coordinator.data["result"]["realtime"]["life_index"]["ultraviolet"]["index"]
        if self.kind == "precipitation":
            return self.coordinator.data["result"]["realtime"]["precipitation"]["local"]["intensity"]
        if self.kind == "update_time":
            return datetime.fromtimestamp(self.coordinator.data["server_time"]) 
        if self.kind == "pm25":
            return self.coordinator.data["result"]["realtime"]["air_quality"]["pm25"]
        if self.kind == "pm10": 
            return self.coordinator.data["result"]["realtime"]["air_quality"]["pm10"]
        if self.kind == "so2":      
            return self.coordinator.data["result"]["realtime"]["air_quality"]["so2"]
        if self.kind == "no2":                              
            return self.coordinator.data["result"]["realtime"]["air_quality"]["no2"]
        if self.kind == "co":
            return self.coordinator.data["result"]["realtime"]["air_quality"]["co"]
        if self.kind == "o3":
            return self.coordinator.data["result"]["realtime"]["air_quality"]["o3"]
        if self.kind == "aqi":
            return self.coordinator.data["result"]["realtime"]["air_quality"]["aqi"]['chn']
        if self.kind == "aqi_description":
            return self.coordinator.data["result"]["realtime"]["air_quality"]['description']['chn']
        if self.kind == "aqi_usa":
            return self.coordinator.data["result"]["realtime"]["air_quality"]['aqi']['usa']
        if self.kind == "aqi_usa_description": 
            return self.coordinator.data["result"]["realtime"]["air_quality"]['description']['usa']                                                                  

    @property
    def icon(self):
        """Return the icon."""
        # if self.forecast_day is not None:
        #     return FORECAST_SENSOR_TYPES[self.kind][ATTR_ICON]
        return SENSOR_TYPES[self.kind][ATTR_ICON]

    @property
    def device_class(self):
        """Return the device_class."""
        # if self.forecast_day is not None:
        #     return FORECAST_SENSOR_TYPES[self.kind][ATTR_DEVICE_CLASS]
        return SENSOR_TYPES[self.kind][ATTR_DEVICE_CLASS]

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        # if self.forecast_day is not None:
        #     return FORECAST_SENSOR_TYPES[self.kind][self._unit_system]
        return SENSOR_TYPES[self.kind][self._unit_system]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        # if self.forecast_day is not None:
        #     if self.kind in ["WindGustDay", "WindGustNight"]:
        #         self._attrs["direction"] = self.coordinator.data.data[ATTR_FORECAST][
        #             self.forecast_day
        #         ][self.kind]["Direction"]["English"]
        #     elif self.kind in ["Grass", "Mold", "Ragweed", "Tree", "UVIndex", "Ozone"]:
        #         self._attrs["level"] = self.coordinator.data.data[ATTR_FORECAST][
        #             self.forecast_day
        #         ][self.kind]["Category"]
        #     return self._attrs
        if self.kind == "ultraviolet":
            self._attrs["desc"] = self.coordinator.data["result"]["realtime"]["life_index"]["ultraviolet"]["desc"]
        elif self.kind == "comfort":
            self._attrs["desc"] = self.coordinator.data["result"]["realtime"]["life_index"]["comfort"]["desc"]
        elif self.kind == "precipitation":
            self._attrs["datasource"] = self.coordinator.data["result"]["realtime"]["precipitation"]["local"]["datasource"]
            if self.coordinator.data["result"]["realtime"]["precipitation"].get("nearest"):
              self._attrs["nearest_intensity"] = self.coordinator.data["result"]["realtime"]["precipitation"]["nearest"]["intensity"]
              self._attrs["nearest_distance"] = self.coordinator.data["result"]["realtime"]["precipitation"]["nearest"]["distance"]
        return self._attrs

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return bool(self.kind not in OPTIONAL_SENSORS)

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Colorfulclouds entity."""
        await self.coordinator.async_request_refresh()
