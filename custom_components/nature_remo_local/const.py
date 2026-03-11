"""Constants for the Nature Remo Local integration."""

from datetime import timedelta

from homeassistant.const import CONF_SCAN_INTERVAL as HA_CONF_SCAN_INTERVAL, Platform

DOMAIN = "nature_remo_local"
API_BASE_URL = "https://api.nature.global"

PLATFORMS: tuple[Platform, ...] = (
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.BUTTON,
)

DEFAULT_SCAN_INTERVAL = 180
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

CONF_SCAN_INTERVAL = HA_CONF_SCAN_INTERVAL
