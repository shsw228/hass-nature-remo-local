"""Sensor platform for Nature Remo Local."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NatureRemoRuntime
from .const import DOMAIN
from .coordinator import NatureRemoDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class NatureRemoSensorDescription(SensorEntityDescription):
    """Describe a Nature Remo sensor."""

    event_key: str


@dataclass(frozen=True, kw_only=True)
class NatureRemoRateLimitSensorDescription(SensorEntityDescription):
    """Describe a Nature Remo rate limit sensor."""

    value_key: str


SENSOR_TYPES: tuple[NatureRemoSensorDescription, ...] = (
    NatureRemoSensorDescription(
        key="temperature",
        event_key="te",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NatureRemoSensorDescription(
        key="humidity",
        event_key="hu",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

RATE_LIMIT_SENSOR_TYPES: tuple[NatureRemoRateLimitSensorDescription, ...] = (
    NatureRemoRateLimitSensorDescription(
        key="rate_limit_remaining",
        value_key="remaining",
        name="Rate Limit Remaining",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:counter",
    ),
    NatureRemoRateLimitSensorDescription(
        key="rate_limit_limit",
        value_key="limit",
        name="Rate Limit Limit",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:gauge",
    ),
    NatureRemoRateLimitSensorDescription(
        key="rate_limit_reset_at",
        value_key="reset_at",
        name="Rate Limit Reset At",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nature Remo sensors from a config entry."""
    runtime: NatureRemoRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[CoordinatorEntity[NatureRemoDataUpdateCoordinator]] = []

    for device in runtime.coordinator.data.devices:
        newest_events = device.get("newest_events") or {}
        for description in SENSOR_TYPES:
            if description.event_key in newest_events:
                entities.append(
                    NatureRemoSensorEntity(
                        coordinator=runtime.coordinator,
                        device=device,
                        entity_description=description,
                    )
                )

    for description in RATE_LIMIT_SENSOR_TYPES:
        entities.append(
            NatureRemoRateLimitSensorEntity(
                coordinator=runtime.coordinator,
                config_entry=entry,
                entity_description=description,
            )
        )

    async_add_entities(entities)


class NatureRemoSensorEntity(
    CoordinatorEntity[NatureRemoDataUpdateCoordinator], SensorEntity
):
    """Representation of a Nature Remo sensor value."""

    entity_description: NatureRemoSensorDescription

    def __init__(
        self,
        *,
        coordinator: NatureRemoDataUpdateCoordinator,
        device: dict[str, Any],
        entity_description: NatureRemoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._device_id = device["id"]
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Nature",
            model="Nature Remo",
            name=device["name"],
            sw_version=device.get("firmware_version"),
        )
        self._attr_translation_key = entity_description.key

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        device = self.coordinator.data.devices_by_id.get(self._device_id)
        newest_events = (device or {}).get("newest_events") or {}
        event = newest_events.get(self.entity_description.event_key)
        if event is None:
            return None
        return event.get("val")

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        device = self.coordinator.data.devices_by_id.get(self._device_id)
        return device is not None and self.entity_description.event_key in (
            (device.get("newest_events") or {})
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self.coordinator.data.devices_by_id.get(self._device_id)
        newest_events = (device or {}).get("newest_events") or {}
        event = newest_events.get(self.entity_description.event_key)
        if event is None:
            return {}
        return {"event_created_at": event.get("created_at")}


class NatureRemoRateLimitSensorEntity(
    CoordinatorEntity[NatureRemoDataUpdateCoordinator], SensorEntity
):
    """Diagnostic sensor for Nature Remo rate limit state."""

    entity_description: NatureRemoRateLimitSensorDescription

    def __init__(
        self,
        *,
        coordinator: NatureRemoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_description: NatureRemoRateLimitSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_has_entity_name = True
        self._attr_translation_key = entity_description.key
        self._attr_unique_id = f"{config_entry.entry_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"account_{config_entry.entry_id}")},
            manufacturer="Nature",
            model="Cloud API",
            name=f"{config_entry.title} Cloud",
        )

    @property
    def available(self) -> bool:
        """Return whether the rate limit value is available."""
        return self.native_value is not None

    @property
    def native_value(self) -> int | datetime | None:
        """Return the current rate limit value."""
        rate_limit = self.coordinator.api.rate_limit
        return getattr(rate_limit, self.entity_description.value_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional rate limit attributes."""
        rate_limit = self.coordinator.api.rate_limit
        return {
            "limit": rate_limit.limit,
            "remaining": rate_limit.remaining,
            "reset_at": rate_limit.reset_at,
            "poll_interval_seconds": int(self.coordinator.update_interval.total_seconds()),
        }
