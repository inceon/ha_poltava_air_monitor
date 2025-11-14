"""Constants for the Poltava Air Monitor integration."""

from typing import Final

DOMAIN: Final = "poltava_air_monitor"

# API
API_BASE_URL: Final = "https://improvement-pl.gov.ua"
API_POSTS_ENDPOINT: Final = "/posts/posts.json"
API_POST_DETAIL_ENDPOINT: Final = "/posts/post-{post_id}.json"

# Configuration
CONF_POST_ID: Final = "post_id"
CONF_POST_NAME: Final = "post_name"
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 600  # 10 minutes
DEFAULT_NAME: Final = "Poltava Air Monitor"

# Sensor types
SENSOR_TYPE_AQI: Final = "aqi"
SENSOR_TYPE_PM25: Final = "pm25"
SENSOR_TYPE_PM10: Final = "pm10"
SENSOR_TYPE_PM1: Final = "pm1"
SENSOR_TYPE_OZONE: Final = "ozone"
SENSOR_TYPE_NO2: Final = "no2"
SENSOR_TYPE_SO2: Final = "so2"
SENSOR_TYPE_CO: Final = "co"
SENSOR_TYPE_TEMPERATURE: Final = "temperature"
SENSOR_TYPE_HUMIDITY: Final = "humidity"
SENSOR_TYPE_PRESSURE: Final = "pressure"
SENSOR_TYPE_WIND_SPEED: Final = "wind_speed"
SENSOR_TYPE_WIND_DIRECTION: Final = "wind_direction"

# Sensor name mappings (Ukrainian to English)
SENSOR_NAME_MAPPING: Final = {
    "ТЧ2,5": SENSOR_TYPE_PM25,
    "ТЧ10": SENSOR_TYPE_PM10,
    "ТЧ1": SENSOR_TYPE_PM1,
    "Озон – O": SENSOR_TYPE_OZONE,
    "Діоксид азоту – NO": SENSOR_TYPE_NO2,
    "Діоксид сірки – SO": SENSOR_TYPE_SO2,
    "Оксид вуглецю – CO": SENSOR_TYPE_CO,
    "Температура повітря": SENSOR_TYPE_TEMPERATURE,
    "Вологість": SENSOR_TYPE_HUMIDITY,
    "Тиск": SENSOR_TYPE_PRESSURE,
    "Швидкість вітру": SENSOR_TYPE_WIND_SPEED,
    "Напрям вітру": SENSOR_TYPE_WIND_DIRECTION,
}

