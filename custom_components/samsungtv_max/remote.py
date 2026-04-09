"""Samsung TV Max — Remote entity.

This is the primary building block for the future custom remote panel.
It exposes the full app catalog, TV capabilities, and power state via
extra_state_attributes so a custom Lovelace-free panel can read everything
it needs from a single entity.

send_command() accepts one or more key names, space-separated or as a list,
with optional num_repeats and delay_secs overrides.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity, RemoteEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_GENERATION,
    CONF_HOST,
    CONF_MODEL,
    DOMAIN,
)
from .coordinator import SamsungTVCoordinator
from .tizen.power_fsm import PowerState

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SamsungTVCoordinator = entry.runtime_data
    async_add_entities([SamsungTVRemote(coordinator, entry)])


class SamsungTVRemote(RemoteEntity):
    """Remote entity — the foundation for a full custom TV remote panel.

    extra_state_attributes exposes:
      - apps          full catalog [{id, name, type}] for dynamic button generation
      - power_state   raw FSM state string
      - tv_model      model string (generation detection)
      - tv_generation generation prefix e.g. "19_"
      - capabilities  {meta_tag_nav, has_ghost_api}
    """

    _attr_has_entity_name = True
    _attr_name = "Remote"
    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(self, coordinator: SamsungTVCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_remote"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Samsung",
            model=entry.data.get(CONF_MODEL) or "Smart TV",
        )
        self._remove_listener: None | object = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

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

    # ── State ─────────────────────────────────────────────────────────────────

    @property
    def is_on(self) -> bool:
        return self._coordinator.power_state == PowerState.ON

    @property
    def activity_list(self) -> list[str]:
        """List of app names — used as 'activities' for the remote entity."""
        return self._coordinator.app_names

    @property
    def current_activity(self) -> str | None:
        return self._coordinator.current_app

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Rich attributes consumed by the future custom remote panel."""
        apps = [
            {
                "id": a.get("appId", ""),
                "name": a.get("name", ""),
                "type": a.get("app_type", 2),
            }
            for a in self._coordinator.apps
            if a.get("is_visible", True)
        ]
        caps = self._coordinator.caps
        return {
            "apps": apps,
            "power_state": str(self._coordinator.power_state),
            "tv_model": self._entry.data.get(CONF_MODEL, ""),
            "tv_generation": self._entry.data.get(CONF_GENERATION, ""),
            "tv_host": self._entry.data.get(CONF_HOST, ""),
            "capabilities": {
                "meta_tag_nav": caps.meta_tag_nav,
                "has_ghost_api": caps.has_ghost_api,
            },
        }

    # ── Commands ──────────────────────────────────────────────────────────────

    async def async_turn_on(self, **kwargs: Any) -> None:
        activity = kwargs.get("activity")
        await self._coordinator.async_turn_on()
        if activity:
            await self._coordinator.async_launch_app(activity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._coordinator.async_turn_off()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send one or more key commands.

        Supports:
          command: ["KEY_VOLUMEUP", "KEY_MUTE"]
          num_repeats: 3  (applies to each command)
          delay_secs: 0.5  (override inter-key delay; default TIZEN_KEY_DELAY)
        """
        num_repeats: int = int(kwargs.get("num_repeats", 1))
        # delay_secs is informational here — KeySender uses its own delay
        # but we respect num_repeats per command via enqueue(count=)

        for key in command:
            # command items may be space-separated key lists (HA convention)
            for single_key in key.split():
                self._coordinator.send_key(single_key, count=num_repeats)
