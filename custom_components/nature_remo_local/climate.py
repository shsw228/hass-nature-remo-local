"""Climate platform for Nature Remo Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NatureRemoRuntime
from .const import DOMAIN
from .coordinator import NatureRemoDataUpdateCoordinator

NATURE_TO_HVAC: dict[str, HVACMode] = {
    "auto": HVACMode.AUTO,
    "blow": HVACMode.FAN_ONLY,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "warm": HVACMode.HEAT,
}

HVAC_TO_NATURE = {value: key for key, value in NATURE_TO_HVAC.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nature Remo climates from a config entry."""
    runtime: NatureRemoRuntime = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NatureRemoClimateEntity(runtime, appliance)
        for appliance in runtime.coordinator.data.appliances
        if appliance.get("aircon") is not None and appliance.get("settings") is not None
    ]
    async_add_entities(entities)


class NatureRemoClimateEntity(
    CoordinatorEntity[NatureRemoDataUpdateCoordinator], ClimateEntity
):
    """Representation of a Nature Remo air conditioner."""

    _attr_has_entity_name = True

    def __init__(
        self, runtime: NatureRemoRuntime, appliance: dict[str, Any]
    ) -> None:
        super().__init__(runtime.coordinator)
        self._api = runtime.api
        self._appliance_id = appliance["id"]
        self._linked_device_id = (appliance.get("device") or {}).get("id")
        self._optimistic_settings: dict[str, Any] | None = None
        self._attr_unique_id = appliance["id"]
        linked_device = appliance.get("device") or {}
        via_device = linked_device.get("id")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"appliance_{appliance['id']}")},
            manufacturer="Nature",
            model="Air Conditioner",
            name=appliance["nickname"],
            via_device=(DOMAIN, via_device) if via_device else None,
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        device = self._linked_device
        newest_events = (device or {}).get("newest_events") or {}
        event = newest_events.get("te")
        return None if event is None else event.get("val")

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        device = self._linked_device
        newest_events = (device or {}).get("newest_events") or {}
        event = newest_events.get("hu")
        return None if event is None else event.get("val")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        raw = (self._settings or {}).get("temp")
        if raw in (None, ""):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        unit = ((self._settings or {}).get("temp_unit") or "").lower()
        return UnitOfTemperature.FAHRENHEIT if unit == "f" else UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        settings = self._settings or {}
        if settings.get("button") == "power-off":
            return HVACMode.OFF

        mode = settings.get("mode")
        return NATURE_TO_HVAC.get(mode, HVACMode.AUTO)

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        mode = self.hvac_mode
        if mode == HVACMode.OFF:
            return HVACAction.OFF
        if mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        if mode == HVACMode.DRY:
            return HVACAction.DRYING

        current = self.current_temperature
        target = self.target_temperature
        if current is None or target is None:
            if mode == HVACMode.COOL:
                return HVACAction.COOLING
            if mode == HVACMode.HEAT:
                return HVACAction.HEATING
            return HVACAction.IDLE

        if mode == HVACMode.COOL:
            return HVACAction.COOLING if current > target else HVACAction.IDLE
        if mode == HVACMode.HEAT:
            return HVACAction.HEATING if current < target else HVACAction.IDLE
        if mode == HVACMode.AUTO:
            if current > target:
                return HVACAction.COOLING
            if current < target:
                return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return available HVAC modes."""
        modes = [HVACMode.OFF]
        for mode in (self._aircon_range.get("modes") or {}).keys():
            hvac_mode = NATURE_TO_HVAC.get(mode)
            if hvac_mode and hvac_mode not in modes:
                modes.append(hvac_mode)
        if len(modes) == 1:
            modes.extend([HVACMode.AUTO, HVACMode.COOL, HVACMode.HEAT])
        return modes

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        raw = (self._settings or {}).get("vol")
        return None if raw in (None, "") else raw

    @property
    def fan_modes(self) -> list[str] | None:
        """Return supported fan modes."""
        modes = self._available_values("vol")
        return modes or None

    @property
    def swing_mode(self) -> str | None:
        """Return the current vertical swing mode."""
        raw = (self._settings or {}).get("dir")
        return None if raw in (None, "") else raw

    @property
    def swing_modes(self) -> list[str] | None:
        """Return supported vertical swing modes."""
        modes = self._available_values("dir")
        return modes or None

    @property
    def swing_horizontal_mode(self) -> str | None:
        """Return the current horizontal swing mode."""
        raw = (self._settings or {}).get("dirh")
        return None if raw in (None, "") else raw

    @property
    def swing_horizontal_modes(self) -> list[str] | None:
        """Return supported horizontal swing modes."""
        modes = self._available_values("dirh")
        return modes or None

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        if self.fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        if self.swing_modes:
            features |= ClimateEntityFeature.SWING_MODE
        if self.swing_horizontal_modes:
            features |= ClimateEntityFeature.SWING_HORIZONTAL_MODE
        return features

    @property
    def min_temp(self) -> float:
        """Return the minimum target temperature."""
        temperatures = self._available_temperatures()
        return min(temperatures) if temperatures else super().min_temp

    @property
    def max_temp(self) -> float:
        """Return the maximum target temperature."""
        temperatures = self._available_temperatures()
        return max(temperatures) if temperatures else super().max_temp

    @property
    def target_temperature_step(self) -> float:
        """Return the supported target temperature step."""
        temperatures = self._available_temperatures()
        if len(temperatures) < 2:
            return 1.0

        unique = sorted(set(temperatures))
        if len(unique) < 2:
            return 1.0

        steps = [round(unique[index + 1] - unique[index], 1) for index in range(len(unique) - 1)]
        positive = [step for step in steps if step > 0]
        return min(positive, default=1.0)

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        if self._appliance is None:
            return False
        if self._linked_device is None:
            return True
        return bool(self._linked_device.get("online", True))

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)

        if hvac_mode is None and temperature is None:
            return

        operation_mode = None
        button = None
        if hvac_mode is not None:
            if hvac_mode == HVACMode.OFF:
                button = "power-off"
            else:
                button = ""
                operation_mode = HVAC_TO_NATURE.get(
                    hvac_mode, self._default_operation_mode()
                )

        target = None
        if temperature is not None:
            value = float(temperature)
            target = str(int(value) if value.is_integer() else value)

        await self._async_send_settings(
            button=button,
            operation_mode=operation_mode,
            temperature=target,
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._async_send_settings(button="power-off")
        else:
            await self._async_send_settings(
                button="",
                operation_mode=HVAC_TO_NATURE.get(hvac_mode, self._default_operation_mode()),
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set a new fan mode."""
        await self._async_send_settings(air_volume=fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set a new vertical swing mode."""
        await self._async_send_settings(air_direction=swing_mode)

    async def async_set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        """Set a new horizontal swing mode."""
        await self._async_send_settings(air_direction_h=swing_horizontal_mode)

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        mode = self.hvac_mode
        if mode == HVACMode.OFF:
            mode = next(
                (candidate for candidate in self.hvac_modes if candidate != HVACMode.OFF),
                HVACMode.AUTO,
            )
        await self.async_set_hvac_mode(mode)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    def _handle_coordinator_update(self) -> None:
        """Reset optimistic state once fresh coordinator data arrives."""
        self._optimistic_settings = None
        super()._handle_coordinator_update()

    @property
    def _appliance(self) -> dict[str, Any] | None:
        return self.coordinator.data.appliances_by_id.get(self._appliance_id)

    @property
    def _linked_device(self) -> dict[str, Any] | None:
        if self._linked_device_id is None:
            return None
        return self.coordinator.data.devices_by_id.get(self._linked_device_id)

    @property
    def _settings(self) -> dict[str, Any] | None:
        appliance = self._appliance or {}
        settings = dict(appliance.get("settings") or {})
        if self._optimistic_settings:
            settings.update(self._optimistic_settings)
        return settings

    @property
    def _aircon_range(self) -> dict[str, Any]:
        appliance = self._appliance or {}
        aircon = appliance.get("aircon") or {}
        return aircon.get("range") or {}

    def _default_operation_mode(self) -> str:
        current_mode = (self._settings or {}).get("mode")
        if current_mode:
            return current_mode

        modes = self._aircon_range.get("modes") or {}
        if modes:
            return next(iter(modes))
        return "auto"

    def _default_temperature(self, operation_mode: str | None = None) -> str:
        current_temperature = (self._settings or {}).get("temp")
        if current_temperature not in (None, ""):
            return str(current_temperature)

        temperatures = self._available_temperatures(operation_mode)
        if temperatures:
            raw = temperatures[0]
            return str(int(raw) if raw.is_integer() else raw)
        return ""

    def _available_temperatures(self, operation_mode: str | None = None) -> list[float]:
        mode = operation_mode or self._default_operation_mode()
        modes = self._aircon_range.get("modes") or {}
        raw_temperatures = (modes.get(mode) or {}).get("temp") or []
        temperatures: list[float] = []
        for raw in raw_temperatures:
            try:
                temperatures.append(float(raw))
            except (TypeError, ValueError):
                continue
        return temperatures

    def _available_values(
        self, key: str, operation_mode: str | None = None
    ) -> list[str]:
        mode = operation_mode or self._default_operation_mode()
        modes = self._aircon_range.get("modes") or {}
        values = (modes.get(mode) or {}).get(key) or []
        if values:
            return list(values)

        merged: list[str] = []
        for mode_data in modes.values():
            for value in (mode_data or {}).get(key) or []:
                if value not in merged:
                    merged.append(value)
        return merged

    def _build_payload(
        self,
        *,
        button: str | None = None,
        operation_mode: str | None = None,
        temperature: str | None = None,
        air_volume: str | None = None,
        air_direction: str | None = None,
        air_direction_h: str | None = None,
    ) -> dict[str, str]:
        settings = self._settings or {}
        mode = operation_mode or self._default_operation_mode()
        return {
            "button": settings.get("button", "") if button is None else button,
            "operation_mode": mode,
            "temperature": temperature or self._default_temperature(mode),
            "temperature_unit": settings.get("temp_unit")
            or (self._appliance or {}).get("aircon", {}).get("tempUnit", "c"),
            "air_volume": settings.get("vol", "") if air_volume is None else air_volume,
            "air_direction": settings.get("dir", "")
            if air_direction is None
            else air_direction,
            "air_direction_h": settings.get("dirh", "")
            if air_direction_h is None
            else air_direction_h,
        }

    async def _async_send_settings(
        self,
        *,
        button: str | None = None,
        operation_mode: str | None = None,
        temperature: str | None = None,
        air_volume: str | None = None,
        air_direction: str | None = None,
        air_direction_h: str | None = None,
    ) -> None:
        """Send aircon settings and keep the entity responsive when refresh is deferred."""
        payload = self._build_payload(
            button=button,
            operation_mode=operation_mode,
            temperature=temperature,
            air_volume=air_volume,
            air_direction=air_direction,
            air_direction_h=air_direction_h,
        )
        response = await self._api.async_set_aircon_settings(self._appliance_id, payload)
        self._optimistic_settings = response
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh_if_safe()
