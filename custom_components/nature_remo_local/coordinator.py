"""Data coordinator for Nature Remo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    NatureRemoApi,
    NatureRemoApiError,
    NatureRemoAuthenticationError,
    NatureRemoRateLimitError,
    NatureRemoRateLimitStatus,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_RATE_LIMIT_BUFFER_SECONDS = 5
_POLL_REQUEST_COST = 2
_POST_ACTION_REFRESH_COST = 2


@dataclass(slots=True)
class NatureRemoSnapshot:
    """Normalized Nature Remo data."""

    devices: list[dict[str, Any]]
    appliances: list[dict[str, Any]]
    rate_limit: NatureRemoRateLimitStatus

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
        self._base_update_interval = timedelta(
            seconds=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            logger=getLogger(__name__),
            name=DOMAIN,
            update_interval=self._base_update_interval,
        )
        self.api = api
        self.config_entry = config_entry

    async def _async_update_data(self) -> NatureRemoSnapshot:
        """Fetch data from Nature Remo."""
        try:
            devices = await self.api.async_get_devices()
            appliances = await self.api.async_get_appliances()
        except NatureRemoAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except NatureRemoRateLimitError as err:
            self._apply_rate_limit_backoff()
            raise UpdateFailed(str(err)) from err
        except NatureRemoApiError as err:
            raise UpdateFailed(str(err)) from err

        snapshot = NatureRemoSnapshot(
            devices=devices,
            appliances=appliances,
            rate_limit=self.api.rate_limit,
        )
        self._apply_rate_limit_backoff()
        return snapshot

    async def async_request_refresh_if_safe(self) -> bool:
        """Refresh only when enough rate limit budget remains."""
        if not self._has_budget(_POST_ACTION_REFRESH_COST):
            self.logger.warning(
                "Skipping immediate Nature Remo refresh due to low rate limit budget: "
                "remaining=%s limit=%s reset_at=%s",
                self.api.rate_limit.remaining,
                self.api.rate_limit.limit,
                self.api.rate_limit.reset_at,
            )
            self._apply_rate_limit_backoff()
            return False

        await self.async_request_refresh()
        return True

    def _has_budget(self, request_cost: int) -> bool:
        """Return whether enough requests remain for the desired action."""
        remaining = self.api.rate_limit.remaining
        if remaining is None:
            return True
        return remaining >= request_cost

    def _apply_rate_limit_backoff(self) -> None:
        """Stretch the polling interval when approaching the rate limit."""
        rate_limit = self.api.rate_limit
        self.update_interval = self._base_update_interval

        if self._has_budget(_POLL_REQUEST_COST):
            return

        reset_at = rate_limit.reset_at
        if reset_at is None:
            return

        now = datetime.now(UTC)
        if reset_at <= now:
            return

        reset_delay = (reset_at - now) + timedelta(seconds=_RATE_LIMIT_BUFFER_SECONDS)
        if reset_delay > self.update_interval:
            self.update_interval = reset_delay
