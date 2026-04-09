"""Samsung TV Max coordinator.

Owns the WebSocket client and power FSM.  All timer logic lives here,
mirroring powerControl.lua.  Entities register callbacks and read state via
coordinator attributes rather than calling poll().

Token rotation / preservation
------------------------------
When the TV sends a new token in ms.channel.connect, _handle_new_token()
persists it immediately to the config entry via async_update_entry so it
survives restarts and the next connection uses the up-to-date token.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import aiohttp
import wakeonlan
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_TOKEN,
    KEY_POWER,
    OFF_SLOW_POLL,
    ON_LIVENESS_INTERVAL,
    ON_LIVENESS_TIMEOUT,
    POWER_PROBE_TIMEOUT,
    TIZEN_REST_PORT,
    TURNING_OFF_TIMEOUT,
    UNAUTHORIZED_RETRY,
    WAKING_GIVE_UP,
    WAKING_POLL_INTERVAL,
    WOL_BURST_ROUNDS,
    WOL_BURST_STEP,
)
from .tizen.app_manager import AppManager
from .tizen.caps import TizenCaps, detect_caps
from .tizen.key_sender import KeySender
from .tizen.power_fsm import PowerState
from .tizen.ws_client import TizenWSClient

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class SamsungTVCoordinator:
    """Central coordinator for one Samsung TV config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._host: str = entry.data[CONF_HOST]
        self._mac: str = entry.data.get(CONF_MAC, "")
        self._token: str = entry.data.get(CONF_TOKEN, "")
        self._model: str = entry.data.get(CONF_MODEL, "")

        self.caps: TizenCaps = detect_caps(self._model)
        self.power_state: PowerState = PowerState.OFF

        # App catalog populated after WS connect
        self.apps: list[dict] = []
        self.current_app: str | None = None

        # Listener callbacks registered by entities
        self._listeners: list[Callable[[], None]] = []

        # aiohttp session — shared across WS client and app manager
        self._session: aiohttp.ClientSession | None = None
        self._ws: TizenWSClient | None = None
        self._app_manager: AppManager | None = None
        self._key_sender: KeySender | None = None

        # Active asyncio timers
        self._wake_timer: asyncio.TimerHandle | None = None
        self._liveness_timer: asyncio.TimerHandle | None = None
        self._off_poll_timer: asyncio.TimerHandle | None = None
        self._turning_off_timer: asyncio.TimerHandle | None = None
        self._unauth_timer: asyncio.TimerHandle | None = None
        self._waking_deadline: float = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def async_setup(self) -> None:
        """Start the coordinator.  Called from async_setup_entry."""
        connector = aiohttp.TCPConnector(ssl=False)
        self._session = aiohttp.ClientSession(connector=connector)

        self._ws = TizenWSClient(
            self._session,
            self._host,
            token=self._token,
            on_connected=self._on_ws_connected,
            on_disconnected=self._on_ws_disconnected,
            on_apps_received=self._on_apps_received,
            on_token_received=self._handle_new_token,
        )

        self._app_manager = AppManager(
            self._session,
            self._host,
            self.caps,
            ws_launch_fn=self._ws.async_launch_app_ws,
        )

        self._key_sender = KeySender(self._ws.async_send_key)

        await self._enter_waking_up()

    async def async_shutdown(self) -> None:
        """Stop timers and close connections.  Called from async_unload_entry."""
        self._cancel_all_timers()
        if self._ws:
            await self._ws.async_close()
        if self._session:
            await self._session.close()

    # ── Listener registration ─────────────────────────────────────────────────

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        """Register an entity callback; return a remove-listener function."""
        self._listeners.append(update_callback)

        def _remove() -> None:
            self._listeners.remove(update_callback)

        return _remove

    def _notify_listeners(self) -> None:
        for cb in list(self._listeners):
            cb()

    # ── Power control (public, called by entities) ───────────────────────────

    async def async_turn_on(self) -> None:
        """Power on: send WOL then enter WAKING_UP."""
        if self.power_state == PowerState.ON:
            return
        if self._mac:
            await self._send_wol()
        await self._enter_waking_up()

    async def async_turn_off(self) -> None:
        """Power off: send KEY_POWER then enter TURNING_OFF."""
        if self.power_state != PowerState.ON:
            return
        self.send_key(KEY_POWER)
        await self._set_power_state(PowerState.TURNING_OFF)

    # ── Key / app (public, called by entities) ────────────────────────────────

    def send_key(self, key: str, count: int = 1) -> None:
        """Enqueue a key for sending (fire-and-forget)."""
        if self._key_sender is None:
            return
        if self.power_state != PowerState.ON:
            _LOGGER.debug("Key %s ignored — TV not ON (%s)", key, self.power_state)
            return
        self._key_sender.enqueue(key, count)

    async def async_launch_app(self, name_or_id: str) -> bool:
        """Launch an app by name or ID; returns False if not possible."""
        if self._app_manager is None or self.power_state != PowerState.ON:
            return False
        return await self._app_manager.async_launch_by_name(name_or_id)

    async def async_enumerate_apps(self) -> None:
        """Re-request the installed-app list from the TV."""
        if self._ws and self._ws.is_connected and self.caps.has_ghost_api:
            await self._ws.async_request_app_list()

    # ── Power FSM ─────────────────────────────────────────────────────────────

    async def _set_power_state(self, new_state: PowerState) -> None:
        if self.power_state == new_state and new_state in (
            PowerState.ON,
            PowerState.OFF,
            PowerState.UNAUTHORIZED,
        ):
            return

        _LOGGER.debug("Power: %s → %s", self.power_state, new_state)
        self.power_state = new_state

        # Cancel timers that don't apply to new state
        if new_state != PowerState.TURNING_OFF:
            self._cancel_timer("turning_off")

        if new_state == PowerState.ON:
            self._cancel_all_timers()
            self._unauth_timer = None
            if self._key_sender:
                self._key_sender.clear()
            await self._start_liveness()

        elif new_state == PowerState.OFF:
            self._cancel_all_timers()
            if self._ws:
                await self._ws.async_close()
            if self._key_sender:
                self._key_sender.clear()
            self._schedule_off_slow_poll()

        elif new_state == PowerState.WAKING_UP:
            self._cancel_all_timers()

        elif new_state == PowerState.TURNING_OFF:
            self._cancel_timer("wake")
            self._cancel_timer("liveness")
            self._cancel_timer("off_poll")
            self._cancel_timer("unauth")
            self._schedule_turning_off_fallback()

        elif new_state == PowerState.UNAUTHORIZED:
            self._cancel_all_timers()
            self._schedule_unauth_retry()

        self._notify_listeners()

    async def _enter_waking_up(self) -> None:
        await self._set_power_state(PowerState.WAKING_UP)
        self._waking_deadline = asyncio.get_event_loop().time() + WAKING_GIVE_UP
        self._schedule_wake_tick(0)

    def _schedule_wake_tick(self, delay: float) -> None:
        self._cancel_timer("wake")
        self._wake_timer = self.hass.loop.call_later(delay, self._wake_tick_sync)

    def _wake_tick_sync(self) -> None:
        asyncio.ensure_future(self._wake_tick())

    async def _wake_tick(self) -> None:
        if self.power_state != PowerState.WAKING_UP:
            return
        if asyncio.get_event_loop().time() > self._waking_deadline:
            _LOGGER.debug("Waking up timed out — going OFF")
            await self._set_power_state(PowerState.OFF)
            return
        # Probe the REST API
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
        try:
            async with self._session.get(  # type: ignore[union-attr]
                url, timeout=aiohttp.ClientTimeout(total=POWER_PROBE_TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    _LOGGER.debug("REST probe OK → connecting WS")
                    await self._ws.async_connect()  # type: ignore[union-attr]
                    return
        except Exception:  # noqa: BLE001
            pass
        # Not up yet — retry
        self._schedule_wake_tick(WAKING_POLL_INTERVAL)

    # ── Liveness (while ON) ───────────────────────────────────────────────────

    async def _start_liveness(self) -> None:
        self._cancel_timer("liveness")
        self._liveness_timer = self.hass.loop.call_later(
            ON_LIVENESS_INTERVAL, self._liveness_tick_sync
        )

    def _liveness_tick_sync(self) -> None:
        asyncio.ensure_future(self._liveness_tick())

    async def _liveness_tick(self) -> None:
        if self.power_state != PowerState.ON:
            return
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
        try:
            async with self._session.get(  # type: ignore[union-attr]
                url, timeout=aiohttp.ClientTimeout(total=ON_LIVENESS_TIMEOUT)
            ):
                await self._start_liveness()  # schedule next
                return
        except Exception:  # noqa: BLE001
            pass
        _LOGGER.debug("Liveness probe failed — TV went OFF")
        if self._ws:
            await self._ws.async_close()
        await self._set_power_state(PowerState.OFF)

    # ── OFF slow poll (auto-detect TV waking up) ──────────────────────────────

    def _schedule_off_slow_poll(self) -> None:
        self._cancel_timer("off_poll")
        self._off_poll_timer = self.hass.loop.call_later(
            OFF_SLOW_POLL, self._off_slow_tick_sync
        )

    def _off_slow_tick_sync(self) -> None:
        asyncio.ensure_future(self._off_slow_tick())

    async def _off_slow_tick(self) -> None:
        if self.power_state != PowerState.OFF:
            return
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
        try:
            async with self._session.get(  # type: ignore[union-attr]
                url, timeout=aiohttp.ClientTimeout(total=POWER_PROBE_TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    _LOGGER.debug("OFF poll: TV responded → entering WAKING_UP")
                    await self._enter_waking_up()
                    return
        except Exception:  # noqa: BLE001
            pass
        self._schedule_off_slow_poll()

    # ── TURNING_OFF fallback ──────────────────────────────────────────────────

    def _schedule_turning_off_fallback(self) -> None:
        self._cancel_timer("turning_off")
        self._turning_off_timer = self.hass.loop.call_later(
            TURNING_OFF_TIMEOUT, self._turning_off_fallback_sync
        )

    def _turning_off_fallback_sync(self) -> None:
        asyncio.ensure_future(self._set_power_state(PowerState.OFF))

    # ── Unauthorized retry ────────────────────────────────────────────────────

    def _schedule_unauth_retry(self) -> None:
        self._cancel_timer("unauth")
        self._unauth_timer = self.hass.loop.call_later(
            UNAUTHORIZED_RETRY, self._unauth_retry_sync
        )

    def _unauth_retry_sync(self) -> None:
        asyncio.ensure_future(self._enter_waking_up())

    # ── WS callbacks ─────────────────────────────────────────────────────────

    async def _on_ws_connected(self) -> None:
        _LOGGER.debug("WS connected — TV is ON")
        await self._set_power_state(PowerState.ON)
        # Request installed apps if the TV supports it
        if self.caps.has_ghost_api and self._ws:
            await self._ws.async_request_app_list()

    async def _on_ws_disconnected(self, was_unauthorized: bool) -> None:
        _LOGGER.debug("WS disconnected (unauth=%s, state=%s)", was_unauthorized, self.power_state)
        if self.power_state in (PowerState.TURNING_OFF,):
            await self._set_power_state(PowerState.OFF)
        elif was_unauthorized:
            await self._set_power_state(PowerState.UNAUTHORIZED)
        elif self.power_state not in (PowerState.OFF,):
            await self._set_power_state(PowerState.OFF)

    async def _on_apps_received(self, apps: list[dict]) -> None:
        if self._app_manager:
            self._app_manager.update_apps(apps)
            self.apps = self._app_manager.apps
        _LOGGER.debug("App catalog updated: %d apps", len(self.apps))
        self._notify_listeners()

        # Fire HA event so automations / custom cards can react
        self.hass.bus.async_fire(
            f"{self.entry.domain}_apps_updated",
            {"entry_id": self.entry.entry_id, "count": len(self.apps)},
        )

    # ── Token rotation / preservation ─────────────────────────────────────────

    async def _handle_new_token(self, token: str) -> None:
        """Persist a newly received token to the config entry immediately."""
        _LOGGER.debug("Persisting new TV token")
        self._token = token
        if self._ws:
            self._ws.update_token(token)
        new_data = {**self.entry.data, CONF_TOKEN: token}
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

    # ── WOL ───────────────────────────────────────────────────────────────────

    async def _send_wol(self) -> None:
        if not self._mac:
            return
        _LOGGER.debug("Sending WOL burst to %s", self._mac)
        for _ in range(WOL_BURST_ROUNDS):
            try:
                wakeonlan.send_magic_packet(self._mac)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.debug("WOL error: %s", exc)
            await asyncio.sleep(WOL_BURST_STEP)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cancel_timer(self, name: str) -> None:
        attr = f"_{name}_timer"
        timer = getattr(self, attr, None)
        if timer:
            timer.cancel()
            setattr(self, attr, None)

    def _cancel_all_timers(self) -> None:
        for name in ("wake", "liveness", "off_poll", "turning_off", "unauth"):
            self._cancel_timer(name)

    @property
    def app_names(self) -> list[str]:
        if self._app_manager:
            return self._app_manager.app_names
        return []

    def resolve_app_id(self, name_or_id: str) -> str | None:
        if self._app_manager:
            return self._app_manager.resolve_app_id(name_or_id)
        return None
