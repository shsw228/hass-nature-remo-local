"""Constants for the Nature Remo Local integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "nature_remo_local"
API_BASE_URL = "https://api.nature.global"

PLATFORMS: tuple[Platform, ...] = (
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.LIGHT,
)

DEFAULT_SCAN_INTERVAL = 180
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
