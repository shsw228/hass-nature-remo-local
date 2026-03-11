"""Nature Remo Local integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NatureRemoApi
from .const import DOMAIN, PLATFORMS
from .coordinator import NatureRemoDataUpdateCoordinator


@dataclass(slots=True)
class NatureRemoRuntime:
    """Runtime objects stored per config entry."""

    api: NatureRemoApi
    coordinator: NatureRemoDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nature Remo from a config entry."""
    session = async_get_clientsession(hass)
    api = NatureRemoApi(session, entry.data[CONF_ACCESS_TOKEN])
    coordinator = NatureRemoDataUpdateCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    runtime = NatureRemoRuntime(api=api, coordinator=coordinator)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
