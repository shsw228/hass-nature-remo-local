"""Button platform for Nature Remo light buttons."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NatureRemoRuntime
from .const import DOMAIN
from .coordinator import NatureRemoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nature Remo light buttons from a config entry."""
    runtime: NatureRemoRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[NatureRemoLightButtonEntity] = []

    for appliance in runtime.coordinator.data.appliances:
        light = appliance.get("light")
        if light is None:
            continue

        for button in light.get("buttons") or []:
            button_name = button.get("name")
            if not button_name:
                continue
            entities.append(
                NatureRemoLightButtonEntity(
                    runtime=runtime,
                    appliance=appliance,
                    button_data=button,
                )
            )

    async_add_entities(entities)


class NatureRemoLightButtonEntity(
    CoordinatorEntity[NatureRemoDataUpdateCoordinator], ButtonEntity
):
    """Expose a Nature Remo light button as a Home Assistant button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        *,
        runtime: NatureRemoRuntime,
        appliance: dict[str, Any],
        button_data: dict[str, Any],
    ) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._appliance_id = appliance["id"]
        self._button_name = button_data["name"]
        self._attr_unique_id = f"{self._appliance_id}_{self._button_name}"
        self._attr_name = button_data.get("label") or self._button_name
        linked_device = appliance.get("device") or {}
        via_device = linked_device.get("id")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"appliance_{appliance['id']}")},
            manufacturer="Nature",
            model="Light",
            name=appliance["nickname"],
            via_device=(DOMAIN, via_device) if via_device else None,
        )

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        return self.coordinator.data.appliances_by_id.get(self._appliance_id) is not None

    async def async_press(self) -> None:
        """Press the Nature Remo light button."""
        await self._api.async_set_light_button(self._appliance_id, self._button_name)
        await self.coordinator.async_request_refresh_if_safe()
