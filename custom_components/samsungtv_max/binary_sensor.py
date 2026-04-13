"""Samsung TV Max — Binary sensor for keyboard/IME state."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MODEL, DOMAIN
from .coordinator import SamsungTVCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SamsungTVCoordinator = entry.runtime_data
    async_add_entities([SamsungTVKeyboardSensor(coordinator, entry)])


class SamsungTVKeyboardSensor(BinarySensorEntity):
    """On when the TV has a text field focused (ms.remote.imeStart)."""

    _attr_has_entity_name = True
    _attr_name = "Keyboard Active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: SamsungTVCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_keyboard_active"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Samsung",
            model=entry.data.get(CONF_MODEL) or "Smart TV",
        )
        self._remove_listener: None | object = None

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self._coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._coordinator.keyboard_active
