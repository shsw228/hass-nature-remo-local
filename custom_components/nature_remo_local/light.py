"""Light platform for Nature Remo Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NatureRemoRuntime
from .const import DOMAIN
from .coordinator import NatureRemoDataUpdateCoordinator

ON_BUTTON_KEYWORDS = ("on", "全灯", "点灯", "power")
OFF_BUTTON_KEYWORDS = ("off", "消灯")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nature Remo lights from a config entry."""
    runtime: NatureRemoRuntime = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NatureRemoLightEntity(runtime, appliance)
        for appliance in runtime.coordinator.data.appliances
        if appliance.get("light") is not None
    ]
    async_add_entities(entities)


class NatureRemoLightEntity(
    CoordinatorEntity[NatureRemoDataUpdateCoordinator], LightEntity
):
    """Representation of a Nature Remo light appliance."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, runtime: NatureRemoRuntime, appliance: dict[str, Any]) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._appliance_id = appliance["id"]
        self._attr_unique_id = appliance["id"]
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
    def is_on(self) -> bool | None:
        """Return whether the light is on."""
        state = ((self._appliance or {}).get("light") or {}).get("state") or {}
        return state.get("power") == "on"

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._appliance is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        button = self._resolve_button_name(is_turn_on=True)
        if button is None:
            raise HomeAssistantError("No matching on button found for this light")

        await self._api.async_set_light_button(self._appliance_id, button)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        button = self._resolve_button_name(is_turn_on=False)
        if button is None:
            raise HomeAssistantError("No matching off button found for this light")

        await self._api.async_set_light_button(self._appliance_id, button)
        await self.coordinator.async_request_refresh()

    @property
    def _appliance(self) -> dict[str, Any] | None:
        return self.coordinator.data.appliances_by_id.get(self._appliance_id)

    def _resolve_button_name(self, *, is_turn_on: bool) -> str | None:
        buttons = ((self._appliance or {}).get("light") or {}).get("buttons") or []
        keywords = ON_BUTTON_KEYWORDS if is_turn_on else OFF_BUTTON_KEYWORDS

        for button in buttons:
            text = " ".join(
                str(button.get(key, "")).lower() for key in ("name", "label", "image")
            )
            if any(keyword in text for keyword in keywords):
                return button.get("name")

        return None
