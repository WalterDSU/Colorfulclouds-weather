

"""Constants for colorfulclouds."""
DOMAIN = "colorfulclouds"

PLATFORMS = ["sensor"]
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "weather.py",
    "config_flow.py",
    "translations/en.json",
]
VERSION = "2025.4.18"
ISSUE_URL = "https://github.com/fineemb/Colorfulclouds-weather/issues"

ROOT_PATH = '/colorfulclouds-local'

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
"""

from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfTime,
    DEGREE,
    UV_INDEX,
    UnitOfPressure,
    UnitOfVolume,
    UnitOfSpeed,
    CONCENTRATION_PARTS_PER_MILLION,
)

from homeassistant.components.sensor.const import (
    SensorDeviceClass,
)

ATTRIBUTION = "Data provided by Colorfulclouds"
ATTR_ICON = "icon"
ATTR_FORECAST = CONF_DAILYSTEPS = "forecast"
ATTR_LABEL = "label"
ATTR_UNIT_IMPERIAL = "Imperial"
ATTR_UNIT_METRIC = "Metric"
MANUFACTURER = "Colorfulclouds, Inc."
NAME = "Colorfulclouds"

CONF_API_KEY = "api_key"
CONF_API_VERSION = "api_version"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALERT = "alert"
CONF_LIFEINDEX = "life"
CONF_CUSTOM_UI = "custom_ui"
CONF_HOURLYSTEPS = "hourlysteps"
CONF_DAILYSTEPS = "dailysteps"
CONF_STARTTIME = "starttime"
CONF_UPDATE_INTERVAL = "update_interval_minutes"

COORDINATOR = "coordinator"

UNDO_UPDATE_LISTENER = "undo_update_listener"


OPTIONAL_SENSORS = (

    "WindDirection",
)


SENSOR_TYPES = {
    "apparent_temperature": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "体感温度",
        ATTR_UNIT_METRIC: UnitOfTemperature.CELSIUS,
        ATTR_UNIT_IMPERIAL: UnitOfTemperature.FAHRENHEIT,
    },
    "temperature": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "温度",
        ATTR_UNIT_METRIC: UnitOfTemperature.CELSIUS,
        ATTR_UNIT_IMPERIAL: UnitOfTemperature.FAHRENHEIT,
    },
    "cloudrate": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-cloudy",
        ATTR_LABEL: "云量",
        ATTR_UNIT_METRIC: "%",
        ATTR_UNIT_IMPERIAL: "%",
    },
    "precipitation": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.PRECIPITATION,
        ATTR_ICON: "mdi:weather-rainy",
        ATTR_LABEL: "雨量",
        ATTR_UNIT_METRIC: UnitOfLength.MILLIMETERS,
        ATTR_UNIT_IMPERIAL: UnitOfLength.INCHES,
    },
    "pressure": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        ATTR_ICON: "mdi:gauge",
        ATTR_LABEL: "气压",
        ATTR_UNIT_METRIC: UnitOfPressure.PA,
        ATTR_UNIT_IMPERIAL: UnitOfPressure.PA,
    },
    "comfort": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:gauge",
        ATTR_LABEL: "舒适指数",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    "ultraviolet": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-sunny",
        ATTR_LABEL: "紫外线",
        ATTR_UNIT_METRIC: UV_INDEX,
        ATTR_UNIT_IMPERIAL: UV_INDEX,
    },
    "humidity": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        ATTR_ICON: "mdi:water-percent",
        ATTR_LABEL: "湿度",
        ATTR_UNIT_METRIC: "%",
        ATTR_UNIT_IMPERIAL: "%",
    },
    "visibility": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-fog",
        ATTR_LABEL: "能见度",
        ATTR_UNIT_METRIC: UnitOfLength.KILOMETERS,
        ATTR_UNIT_IMPERIAL: UnitOfLength.MILES,
    },
    "WindSpeed": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.WIND_SPEED,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "风速",
        ATTR_UNIT_METRIC: UnitOfSpeed.KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: UnitOfSpeed.MILES_PER_HOUR,
    },
    "WindDirection": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "风向",
        ATTR_UNIT_METRIC: DEGREE,
        ATTR_UNIT_IMPERIAL: DEGREE,
    },
    "update_time": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:update",
        ATTR_LABEL: "更新",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    "pm25": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.PM25,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "PM 2.5",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    },
    "pm10": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.PM10,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "PM 10",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    },
    "aqi": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.AQI,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "空气质量指数",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    "co": { 
        ATTR_DEVICE_CLASS: SensorDeviceClass.CO,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "一氧化碳",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    },
    "o3": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.OZONE,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "臭氧",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    },
    "so2": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.SULPHUR_DIOXIDE,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "二氧化硫",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    },
    "no2": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.NITROGEN_DIOXIDE,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "二氧化氮",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_MILLION,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_MILLION,
    }, 
    "aqi_usa": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.AQI,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "美国空气质量指数",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    "aqi_description": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "空气质量描述",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    "aqi_usa_description": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:lungs",
        ATTR_LABEL: "美国空气质量描述",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
    },
    
}



