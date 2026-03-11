"""Data coordinator for Nature Remo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from logging import getLogger
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NatureRemoApi, NatureRemoApiError, NatureRemoAuthenticationError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN


@dataclass(slots=True)
class NatureRemoSnapshot:
    """Normalized Nature Remo data."""

    user: dict[str, Any]
    devices: list[dict[str, Any]]
    appliances: list[dict[str, Any]]

    @property
    def devices_by_id(self) -> dict[str, dict[str, Any]]:
        """Return a device lookup."""
        return {device["id"]: device for device in self.devices}

    @property
    def appliances_by_id(self) -> dict[str, dict[str, Any]]:
        """Return an appliance lookup."""
        return {appliance["id"]: appliance for appliance in self.appliances}


class NatureRemoDataUpdateCoordinator(DataUpdateCoordinator[NatureRemoSnapshot]):
    """Manage Nature Remo Cloud API polling."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: NatureRemoApi,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            logger=getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(
                seconds=config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )
        self.api = api
        self.config_entry = config_entry

    async def _async_update_data(self) -> NatureRemoSnapshot:
        """Fetch data from Nature Remo."""
        try:
            user = await self.api.async_get_user()
            devices = await self.api.async_get_devices()
            appliances = await self.api.async_get_appliances()
        except NatureRemoAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except NatureRemoApiError as err:
            raise UpdateFailed(str(err)) from err

        return NatureRemoSnapshot(
            user=user,
            devices=devices,
            appliances=appliances,
        )
