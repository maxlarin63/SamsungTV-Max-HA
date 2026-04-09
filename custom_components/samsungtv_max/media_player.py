"""Samsung TV Max — MediaPlayer entity."""

from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_HOST,
    CONF_MODEL,
    DOMAIN,
    KEY_MUTE,
    KEY_NEXT,
    KEY_PAUSE,
    KEY_PLAY,
    KEY_PREV,
    KEY_VOLUMEDOWN,
    KEY_VOLUMEUP,
)
from .coordinator import SamsungTVCoordinator
from .tizen.power_fsm import PowerState

_LOGGER = logging.getLogger(__name__)

_SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
)

_POWER_STATE_MAP: dict[PowerState, MediaPlayerState] = {
    PowerState.OFF: MediaPlayerState.OFF,
    PowerState.WAKING_UP: MediaPlayerState.OFF,
    PowerState.ON: MediaPlayerState.ON,
    PowerState.TURNING_OFF: MediaPlayerState.OFF,
    PowerState.UNAUTHORIZED: MediaPlayerState.OFF,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SamsungTVCoordinator = entry.runtime_data
    async_add_entities([SamsungTVMediaPlayer(coordinator, entry)])


class SamsungTVMediaPlayer(MediaPlayerEntity):
    """Represents the Samsung TV as a media player."""

    _attr_has_entity_name = True
    _attr_name = None  # use device name

    def __init__(self, coordinator: SamsungTVCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Samsung",
            model=entry.data.get(CONF_MODEL) or "Smart TV",
        )
        self._attr_supported_features = _SUPPORTED_FEATURES
        self._remove_listener: None | object = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self._coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        await self.async_update_ha_state(True)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    # ── State ─────────────────────────────────────────────────────────────────

    @property
    def state(self) -> MediaPlayerState:
        if self._coordinator.ui_shows_power_on():
            return MediaPlayerState.ON
        return _POWER_STATE_MAP.get(self._coordinator.power_state, MediaPlayerState.OFF)

    @property
    def source_list(self) -> list[str]:
        return self._coordinator.app_names

    @property
    def source(self) -> str | None:
        return self._coordinator.current_app

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "power_state": self._coordinator.power_state,
            "tv_model": self._entry.data.get(CONF_MODEL, ""),
            "tv_host": self._entry.data.get(CONF_HOST, ""),
        }

    # ── Commands ──────────────────────────────────────────────────────────────

    async def async_turn_on(self) -> None:
        await self._coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        await self._coordinator.async_turn_off()

    async def async_mute_volume(self, mute: bool) -> None:
        self._coordinator.send_key(KEY_MUTE)

    async def async_volume_up(self) -> None:
        self._coordinator.send_key(KEY_VOLUMEUP)

    async def async_volume_down(self) -> None:
        self._coordinator.send_key(KEY_VOLUMEDOWN)

    async def async_media_next_track(self) -> None:
        self._coordinator.send_key(KEY_NEXT)

    async def async_media_previous_track(self) -> None:
        self._coordinator.send_key(KEY_PREV)

    async def async_media_play(self) -> None:
        self._coordinator.send_key(KEY_PLAY)

    async def async_media_pause(self) -> None:
        self._coordinator.send_key(KEY_PAUSE)

    async def async_media_stop(self) -> None:
        from .const import KEY_STOP
        self._coordinator.send_key(KEY_STOP)

    async def async_select_source(self, source: str) -> None:
        await self._coordinator.async_launch_app(source)
