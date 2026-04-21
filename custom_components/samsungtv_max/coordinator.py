"""Samsung TV Max coordinator.

Owns the WebSocket client and power FSM.  All timer logic lives here,
mirroring powerControl.lua.  Entities register callbacks and read state via
coordinator attributes rather than calling poll().

Token rotation / preservation
------------------------------
When the TV sends a new token in ms.channel.connect, _handle_new_token()
persists it immediately to the config entry via async_update_entry so it
survives restarts and the next connection uses the up-to-date token.

FSM semantics
-------------
``PowerState.ON`` means the **WebSocket remote channel is paired**
(``ms.channel.connect``), not “backlight on”.  See ``tizen/power_fsm.py`` for a
full description of states, timers, and why HA may disagree with the physical
screen.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import wakeonlan
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_GENERATION,
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_TOKEN,
    DOMAIN,
    EVENT_PAIRING_REQUIRED,
    KEY_POWER,
    OFF_SLOW_POLL,
    OFF_SLOW_POLL_INITIAL_DELAY,
    ON_LIVENESS_INTERVAL,
    ON_LIVENESS_TIMEOUT,
    PAIRING_STUCK_WS_OPENS,
    POWER_PROBE_TIMEOUT,
    STANDBY_KEY_WAKE_SETTLE_SEC,
    TIZEN_REST_PORT,
    TIZEN_WS_PORT,
    TURNING_OFF_TIMEOUT,
    UI_OPTIMISTIC_ON_GRACE_SEC,
    UNAUTHORIZED_RETRY,
    WAKING_GIVE_UP,
    WAKING_POLL_INTERVAL,
    WOL_BURST_ROUNDS,
    WOL_BURST_STEP,
)
from .tizen import icon_cache
from .tizen.app_manager import AppManager
from .tizen.caps import TizenCaps, detect_caps, extract_generation
from .tizen.key_sender import KeySender
from .tizen.power_fsm import PowerState
from .tizen.ws_client import TizenWSClient
from .util_mac import (
    directed_broadcast_ipv4,
    normalize_tv_ipv4_host,
    normalize_wol_mac,
)

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

WOL_UDP_PORT = 9  # same default as HC3 / wakeonlan; must match TV WoL setting

# Pacing for ed.apps.icon prefetch — slow enough that a K45 (no `event` key,
# chattier reply window) does not coalesce responses, fast enough that 20 icons
# complete in well under the wake grace period.
_ICON_PROBE_SPACING_SEC = 0.15
_ICON_PREFETCH_BUDGET_SEC = 12.0


def _execute_wol_round(
    mac: str, destinations: tuple[tuple[str, int], ...], round_idx: int
) -> None:
    """One HC3-style round: TV IP, then global broadcast, then subnet broadcast."""
    for tgt_idx, (ip, port) in enumerate(destinations, start=1):
        try:
            wakeonlan.send_magic_packet(mac, ip_address=ip, port=port)
            _LOGGER.debug("WOL UDP sent -> %s r%dt%d", ip, round_idx, tgt_idx)
        except (ValueError, OSError) as err:
            _LOGGER.debug("WOL -> %s r%dt%d failed: %s", ip, round_idx, tgt_idx, err)


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
        # Last observed REST device.PowerState (lowercase), if provided by /api/v2/.
        # Used to improve wake decisions on TVs that keep REST reachable in standby.
        self._last_rest_power_state: str | None = None

        # App catalog populated after WS connect
        self.apps: list[dict] = []
        self.current_app: str | None = None
        # appId → cached icon URL (served by the integration's static path).
        # Populated eagerly from disk in async_setup so cached icons survive a
        # restart, then incrementally refreshed as ed.apps.icon replies arrive.
        self.icon_urls: dict[str, str] = {}
        self._integration_dir: Path = Path(__file__).parent
        self._icon_prefetch_task: asyncio.Task | None = None

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
        # Only one wake poll / WS connect attempt at a time (timer cancel does not stop
        # an already-running _wake_tick coroutine; overlapping ticks caused false timeouts).
        self._wake_lock = asyncio.Lock()
        # UI-only: monotonic deadline; FSM unchanged (see ui_shows_power_on).
        self._ui_on_grace_until: float = 0.0
        # When UI grace expires, we must notify entities; otherwise non-polled entities
        # (like RemoteEntity) can stay "on" until the next coordinator event.
        self._ui_grace_timer: asyncio.TimerHandle | None = None
        # Repeated WS open during WAKING_UP usually means TV is showing allow / pairing prompt.
        self._wake_ws_open_attempts: int = 0
        self._pairing_stuck_notified: bool = False
        # OFF slow poll: log /api/v2/ timeout at INFO once per streak (TV unreachable).
        self._off_poll_timeout_logged: bool = False

        if not normalize_tv_ipv4_host(self._host):
            _LOGGER.warning("TV %r: host must be a numeric IPv4.", self._host)
        elif not normalize_wol_mac(self._mac):
            _LOGGER.info(
                "TV %s: MAC not in config yet (TV off during setup?). "
                "Model/MAC will load when the TV responds on port %s.",
                self._host,
                TIZEN_REST_PORT,
            )

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
            on_keyboard_changed=self._on_keyboard_changed,
            on_ime_content=self._on_ime_content,
            on_icon_received=self._on_icon_received,
        )

        self._app_manager = AppManager(
            self._session,
            self._host,
            self.caps,
            ws_launch_fn=self._ws.async_launch_app_ws,
        )

        self._key_sender = KeySender(self._ws.async_send_key)

        # Stay OFF until user turns on or slow poll sees the TV (avoid WAKING_UP at HA boot).
        self._schedule_off_slow_poll(delay=0.0)
        _LOGGER.info(
            "Samsung TV Max [%s]: integration ready; assuming TV off, polling :%s",
            self._host,
            TIZEN_REST_PORT,
        )

    async def _async_merge_device_from_rest(self, payload: dict) -> None:
        """Persist model/MAC from /api/v2/ JSON when deferred setup left them empty."""
        device = payload.get("device") or {}
        new_model = (device.get("modelName") or "").strip() or self._model
        new_mac = ""
        for candidate in (
            device.get("wifiMac"),
            device.get("mac"),
            device.get("wiredMac"),
            device.get("ethernetMac"),
        ):
            if not candidate:
                continue
            norm = normalize_wol_mac(str(candidate))
            if norm:
                new_mac = norm
                break
        new_generation = extract_generation(new_model) if new_model else self._generation

        cur = dict(self.entry.data)
        changed = False
        if new_mac and new_mac != cur.get(CONF_MAC, ""):
            cur[CONF_MAC] = new_mac
            changed = True
        if new_model and new_model != cur.get(CONF_MODEL, ""):
            cur[CONF_MODEL] = new_model
            cur[CONF_GENERATION] = new_generation
            changed = True
        elif (
            new_generation
            and new_generation != cur.get(CONF_GENERATION, "")
            and new_model
        ):
            cur[CONF_GENERATION] = new_generation
            changed = True

        if not changed:
            return

        self.hass.config_entries.async_update_entry(self.entry, data=cur)
        self._mac = cur.get(CONF_MAC, "")
        self._model = cur.get(CONF_MODEL, "")
        self._generation = cur.get(CONF_GENERATION, "")
        self.caps = detect_caps(self._model)
        if self._app_manager:
            self._app_manager.set_caps(self.caps)
        _LOGGER.info("Loaded TV model/MAC from REST and updated config entry")
        self._notify_listeners()

    @staticmethod
    def _extract_rest_power_state(payload: dict) -> str | None:
        """Extract device.PowerState from /api/v2/ payload (lowercased) if present."""
        device = payload.get("device")
        if not isinstance(device, dict):
            return None
        raw = device.get("PowerState")
        if not isinstance(raw, str):
            return None
        value = raw.strip().lower()
        return value or None

    async def _async_probe_rest_power_state(self) -> str | None:
        """Fetch /api/v2/ once and return device.PowerState if available.

        Used to make wake decisions on explicit user actions (turn on) before the next
        scheduled poll runs.
        """
        if self._session is None:
            return None
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=POWER_PROBE_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    return None
                try:
                    data = await resp.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError):
                    return None
        except Exception:  # noqa: BLE001
            return None
        rest_power = self._extract_rest_power_state(data)
        if rest_power:
            self._last_rest_power_state = rest_power
        return rest_power

    async def async_shutdown(self) -> None:
        """Stop timers and close connections.  Called from async_unload_entry."""
        self._cancel_all_timers()
        if self._icon_prefetch_task and not self._icon_prefetch_task.done():
            self._icon_prefetch_task.cancel()
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

    def _bump_ui_on_grace_deadline(self) -> None:
        """Extend UI “on” smoothing after turn-on or successful WS pair (not FSM)."""
        loop = asyncio.get_event_loop()
        self._ui_on_grace_until = loop.time() + UI_OPTIMISTIC_ON_GRACE_SEC
        if self._ui_grace_timer:
            self._ui_grace_timer.cancel()
            self._ui_grace_timer = None
        self._ui_grace_timer = self.hass.loop.call_later(
            UI_OPTIMISTIC_ON_GRACE_SEC, self._ui_grace_expired_sync
        )

    def _ui_grace_expired_sync(self) -> None:
        """Timer callback to refresh entity states after grace expires."""
        self._ui_grace_timer = None
        self._notify_listeners()

    def ui_shows_power_on(self) -> bool:
        """True if media_player / remote should show on (may differ briefly from power_state)."""
        if self.power_state == PowerState.ON:
            return True
        if self.power_state in (PowerState.TURNING_OFF, PowerState.UNAUTHORIZED):
            return False
        now = asyncio.get_event_loop().time()
        if now >= self._ui_on_grace_until:
            return False
        return self.power_state in (PowerState.WAKING_UP, PowerState.OFF)

    @property
    def tv_awaiting_authorization(self) -> bool:
        """True when TV likely shows allow/pair prompt or denied remote access."""
        if self.power_state == PowerState.UNAUTHORIZED:
            return True
        if self.power_state == PowerState.WAKING_UP:
            return self._wake_ws_open_attempts >= PAIRING_STUCK_WS_OPENS
        return False

    def _pairing_notification_id(self) -> str:
        return f"{DOMAIN}_pairing_{self.entry.entry_id}"

    def _pairing_issue_id(self) -> str:
        """Repairs / Settings → System → Repairs (native HA warning UI)."""
        return f"pairing_{self.entry.entry_id}"

    def _dismiss_pairing_notification(self) -> None:
        persistent_notification.async_dismiss(self.hass, self._pairing_notification_id())
        ir.async_delete_issue(self.hass, DOMAIN, self._pairing_issue_id())

    def _notify_pairing_stuck(self) -> None:
        if self._pairing_stuck_notified:
            return
        self._pairing_stuck_notified = True
        _LOGGER.warning(
            "Samsung TV Max [%s]: WebSocket pairing stuck (%s+ attempts) — check TV for "
            "allow/approve prompt (see Settings → System → Repairs)",
            self._host,
            PAIRING_STUCK_WS_OPENS,
        )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._pairing_issue_id(),
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="pairing_stuck",
            translation_placeholders={"host": self._host},
        )
        persistent_notification.async_create(
            self.hass,
            title="Samsung TV Max — approve on the TV",
            message=(
                f"The TV at {self._host} answers on port {TIZEN_REST_PORT} but remote control "
                "is not completing. On the TV, allow or approve the connection when prompted "
                "(often General → External device management, or the on-screen remote prompt). "
                "If you removed Home Assistant on the TV, that invalidates the saved token — "
                "approve again to store a new one."
            ),
            notification_id=self._pairing_notification_id(),
        )
        self.hass.bus.async_fire(
            EVENT_PAIRING_REQUIRED,
            {
                "entry_id": self.entry.entry_id,
                "host": self._host,
                "reason": "stuck_ws",
            },
        )
        self._notify_listeners()

    def _notify_pairing_denied(self) -> None:
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._pairing_issue_id(),
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="pairing_denied",
            translation_placeholders={"host": self._host},
        )
        persistent_notification.async_create(
            self.hass,
            title="Samsung TV Max — pairing denied",
            message=(
                f"The TV at {self._host} rejected the remote session. Allow remote access for "
                "this device on the TV, or accept the prompt if shown. The saved access token "
                "was cleared so the next connection can pair fresh."
            ),
            notification_id=self._pairing_notification_id(),
        )
        self.hass.bus.async_fire(
            EVENT_PAIRING_REQUIRED,
            {
                "entry_id": self.entry.entry_id,
                "host": self._host,
                "reason": "unauthorized",
            },
        )
        self._notify_listeners()

    async def _clear_persisted_token(self) -> None:
        """Drop stored token (e.g. TV revoked access); next WS connect pairs without token."""
        if not self.entry.data.get(CONF_TOKEN):
            self._token = ""
            if self._ws:
                self._ws.update_token("")
            return
        _LOGGER.info("Samsung TV Max [%s]: clearing stored access token (pairing reset)", self._host)
        self._token = ""
        if self._ws:
            self._ws.update_token("")
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, CONF_TOKEN: ""}
        )

    def _reset_pairing_progress(self) -> None:
        self._wake_ws_open_attempts = 0
        self._pairing_stuck_notified = False

    # ── Power control (public, called by entities) ───────────────────────────

    async def async_turn_on(self) -> None:
        """Power on: optional WoL (from true OFF), then WAKING_UP / HTTP+WS connect."""
        # Some TVs keep the WS control channel alive while the panel is in standby.
        # If REST reports standby, treat the TV as off even if FSM currently says ON.
        if self.power_state == PowerState.ON and self._last_rest_power_state != "standby":
            return
        ipv4 = normalize_tv_ipv4_host(self._host)
        if not ipv4:
            _LOGGER.warning(
                "Power on cancelled: host must be a numeric IPv4 for wake polling (got %r).",
                self._host,
            )
            return
        ws_connected = bool(self._ws and self._ws.is_connected)
        # On explicit user action (turn on), refresh REST power state once so we can decide
        # between waking via WS key vs WoL.
        rest_power = await self._async_probe_rest_power_state()
        if rest_power:
            self._last_rest_power_state = rest_power

        # If WS is connected but REST says standby, try KEY_POWER on the existing session first.
        if ws_connected and self._last_rest_power_state == "standby" and self._ws:
            _LOGGER.info(
                "Samsung TV Max [%s]: turn on — WS connected but REST=standby; sending KEY_POWER",
                self._host,
            )
            try:
                await self._ws.async_send_key(KEY_POWER)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Samsung TV Max [%s]: KEY_POWER via WS failed: %s", self._host, err)
            await asyncio.sleep(STANDBY_KEY_WAKE_SETTLE_SEC)
            ws_after_key = bool(self._ws and self._ws.is_connected)
            rest_after = await self._async_probe_rest_power_state()
            if rest_after:
                self._last_rest_power_state = rest_after
            if not ws_after_key or self._last_rest_power_state == "standby":
                _LOGGER.info(
                    "Samsung TV Max [%s]: after KEY_POWER: ws_alive=%s REST=%s — will add WoL "
                    "if MAC available (WAKING_UP closes this socket)",
                    self._host,
                    ws_after_key,
                    self._last_rest_power_state,
                )

        # Always send WoL when we have a MAC. A live WS here is misleading: _enter_waking_up
        # closes the socket before polling, and deep-standby TVs need magic packets even if
        # a stale control session looked "connected".
        mac = normalize_wol_mac(self._mac)
        if mac:
            _LOGGER.info(
                "Samsung TV Max [%s]: turn on — WoL burst (supplemental) then WAKING_UP "
                "(power=%s, ws_before_wake=%s, rest=%s)",
                self._host,
                self.power_state,
                ws_connected,
                self._last_rest_power_state,
            )
            await self._send_wol(ipv4, mac)
        elif not ws_connected and self.power_state == PowerState.OFF:
            _LOGGER.warning(
                "Samsung TV Max [%s]: power on from OFF without MAC and without WS — cannot "
                "send WoL. Add the TV Wi‑Fi/Ethernet MAC in the integration options.",
                self._host,
            )
            return
        self._bump_ui_on_grace_deadline()
        self._notify_listeners()
        await self._enter_waking_up()

    async def async_turn_off(self) -> None:
        """Power off: send KEY_POWER then enter TURNING_OFF.

        If ``/api/v2/`` reports ``device.PowerState`` = standby while the FSM is still ON
        (e.g. panel was turned off via IR first), align to OFF without sending KEY_POWER so
        we do not toggle the TV back on. TVs without PowerState in REST behave as before.
        """
        if self.power_state != PowerState.ON:
            return
        self._ui_on_grace_until = 0.0
        if self._ui_grace_timer:
            self._ui_grace_timer.cancel()
            self._ui_grace_timer = None
        rest_power = await self._async_probe_rest_power_state()
        if rest_power == "standby":
            _LOGGER.info(
                "Samsung TV Max [%s]: turn off — REST=standby while FSM ON; aligning off "
                "without KEY_POWER",
                self._host,
            )
            await self._set_power_state(PowerState.OFF)
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
        ws = self._ws
        if ws is not None and ws.should_bypass_key_queue(key):
            asyncio.ensure_future(self._async_touch_mode_key_burst(key, max(1, count)))
            return
        self._key_sender.enqueue(key, count)

    async def _async_touch_mode_key_burst(self, key: str, count: int) -> None:
        """Browser pointer mode: send d-pad without KeySender's inter-key delay (HC3)."""
        for _ in range(count):
            cur = self._ws
            if cur is None or self.power_state != PowerState.ON:
                return
            await cur.async_send_key(key)

    async def async_hold_key(self, key: str, duration: float = 0.5) -> None:
        """Send Press, wait *duration* seconds, then Release (TV auto-repeats while held)."""
        if self._ws is None or self.power_state != PowerState.ON:
            return
        if not await self._ws.async_send_key_press(key):
            return
        await asyncio.sleep(duration)
        if self._ws is not None:
            await self._ws.async_send_key_release(key)

    @property
    def keyboard_active(self) -> bool:
        """True when the TV has a text field focused (ms.remote.imeStart)."""
        return self._ws is not None and self._ws.keyboard_active

    async def async_send_text(self, text: str) -> bool:
        """Send text to the focused on-screen input field (browser URL bar, search, etc.).

        Returns False if the TV is not ON, WS is not connected, or the send fails.
        """
        if self._ws is None or self.power_state != PowerState.ON:
            return False
        ok = await self._ws.async_send_input_string(text)
        if ok:
            await self._ws.async_send_input_end()
        return ok

    async def async_launch_app(self, name_or_id: str) -> bool:
        """Launch an app by name or ID; returns False if not possible."""
        if self._app_manager is None or self.power_state != PowerState.ON:
            return False
        return await self._app_manager.async_launch_by_name(name_or_id)

    async def async_enumerate_apps(self) -> None:
        """Re-request the installed-app list from the TV."""
        if self._ws and self._ws.is_connected and self.caps.has_ghost_api:
            await self._ws.async_request_app_list()

    async def async_probe_app_icons(self) -> None:
        """Diagnostic: force-refresh every app icon from the TV.

        v0.4.0 used this to empirically confirm ``ed.apps.icon`` support on K39
        and K45.  From v0.4.1 onward the same flow runs automatically in
        ``_async_prefetch_icons`` whenever the app catalog refreshes, so this
        service is retained only as a manual reset / troubleshooting aid.
        """
        if self._ws is None or not self._ws.is_connected:
            _LOGGER.warning(
                "Samsung TV Max [%s]: probe_app_icons: WS not connected", self._host
            )
            return
        if not self.apps:
            _LOGGER.warning(
                "Samsung TV Max [%s]: probe_app_icons: app list is empty", self._host
            )
            return

        before = len(self._ws.last_icon_replies)
        probed = 0
        skipped = 0
        for app in self.apps:
            icon_path = app.get("icon_path")
            if not icon_path:
                skipped += 1
                continue
            await self._ws.async_probe_app_icon(icon_path)
            probed += 1
            await asyncio.sleep(0.2)

        # Collection window — most firmwares reply within a second or two.
        await asyncio.sleep(5.0)
        after = self._ws.last_icon_replies
        new_replies = len(after) - before
        sample = next(iter(after.items()), None)
        _LOGGER.info(
            "Samsung TV Max [%s]: probe_app_icons: probed=%d skipped=%d new_replies=%d "
            "total_replies=%d sample=%s",
            self._host,
            probed,
            skipped,
            new_replies,
            len(after),
            (sample[0], str(sample[1])[:200]) if sample else None,
        )

    # ── Power FSM ─────────────────────────────────────────────────────────────

    async def _set_power_state(self, new_state: PowerState) -> None:
        if self.power_state == new_state and new_state in (
            PowerState.ON,
            PowerState.OFF,
            PowerState.WAKING_UP,
            PowerState.TURNING_OFF,
            PowerState.UNAUTHORIZED,
        ):
            return

        prev = self.power_state
        _LOGGER.info("Samsung TV Max [%s]: power %s → %s", self._host, prev, new_state)
        self.power_state = new_state

        # Cancel timers that don't apply to new state
        if new_state != PowerState.TURNING_OFF:
            self._cancel_timer("turning_off")

        if new_state == PowerState.ON:
            self._dismiss_pairing_notification()
            self._reset_pairing_progress()
            self._cancel_all_timers()
            self._unauth_timer = None
            if self._key_sender:
                self._key_sender.clear()
            await self._start_liveness()

        elif new_state == PowerState.OFF:
            self._dismiss_pairing_notification()
            self._reset_pairing_progress()
            self._cancel_all_timers()
            if self._ui_grace_timer:
                self._ui_grace_timer.cancel()
                self._ui_grace_timer = None
            if self._ws:
                await self._ws.async_close()
            if self._key_sender:
                self._key_sender.clear()
            self._schedule_off_slow_poll(delay=OFF_SLOW_POLL_INITIAL_DELAY)

        elif new_state == PowerState.WAKING_UP:
            self._cancel_all_timers()
            self._reset_pairing_progress()
            self._dismiss_pairing_notification()
            # Drop any previous session (e.g. ON → TURNING_OFF → WAKING_UP) so wake polling
            # always calls async_connect on a clean socket. Otherwise is_connected stays True,
            # async_connect returns immediately, and ms.channel.connect never fires again.
            if self._ws:
                await self._ws.async_close()

        elif new_state == PowerState.TURNING_OFF:
            self._cancel_timer("wake")
            self._cancel_timer("liveness")
            self._cancel_timer("off_poll")
            self._cancel_timer("unauth")
            self._schedule_turning_off_fallback()

        elif new_state == PowerState.UNAUTHORIZED:
            self._ui_on_grace_until = 0.0
            self._reset_pairing_progress()
            self._cancel_all_timers()
            self._schedule_unauth_retry()

        self._notify_listeners()

    async def _enter_waking_up(self) -> None:
        already_waking = self.power_state == PowerState.WAKING_UP
        await self._set_power_state(PowerState.WAKING_UP)
        if not already_waking:
            self._waking_deadline = asyncio.get_event_loop().time() + WAKING_GIVE_UP
        self._schedule_wake_tick(0)

    def _schedule_wake_tick(self, delay: float) -> None:
        self._cancel_timer("wake")
        self._wake_timer = self.hass.loop.call_later(delay, self._wake_tick_sync)

    def _wake_tick_sync(self) -> None:
        asyncio.ensure_future(self._wake_tick())

    async def _wake_tick(self) -> None:
        async with self._wake_lock:
            if self.power_state != PowerState.WAKING_UP:
                return
            loop_time = asyncio.get_event_loop().time()
            if loop_time > self._waking_deadline:
                _LOGGER.warning(
                    "Samsung TV Max [%s]: wake timed out (%ss) — marking off",
                    self._host,
                    int(WAKING_GIVE_UP),
                )
                await self._set_power_state(PowerState.OFF)
                return
            # Probe the REST API
            url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
            try:
                async with self._session.get(  # type: ignore[union-attr]
                    url, timeout=aiohttp.ClientTimeout(total=POWER_PROBE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.info(
                            "Samsung TV Max [%s]: wake poll: /api/v2/ HTTP %s (retry)",
                            self._host,
                            resp.status,
                        )
                        self._schedule_wake_tick(WAKING_POLL_INTERVAL)
                        return
                    # TV is reachable on REST; refresh wake budget so a stuck WS handshake
                    # does not lose to an overlapping tick's stale deadline.
                    now = asyncio.get_event_loop().time()
                    self._waking_deadline = max(self._waking_deadline, now + WAKING_GIVE_UP)
                    try:
                        data = await resp.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError) as err:
                        _LOGGER.warning(
                            "Samsung TV Max [%s]: /api/v2/ JSON error: %s",
                            self._host,
                            err,
                        )
                    else:
                        await self._async_merge_device_from_rest(data)
                        rest_power = self._extract_rest_power_state(data)
                        self._last_rest_power_state = rest_power
                        if rest_power == "standby":
                            _LOGGER.info(
                                "Samsung TV Max [%s]: wake poll: REST says standby — keep waiting",
                                self._host,
                            )
                            self._schedule_wake_tick(WAKING_POLL_INTERVAL)
                            return
                    if self.power_state != PowerState.WAKING_UP:
                        return
                    _LOGGER.info(
                        "Samsung TV Max [%s]: TV answers on :%s — opening WebSocket :%s",
                        self._host,
                        TIZEN_REST_PORT,
                        TIZEN_WS_PORT,
                    )
                    self._wake_ws_open_attempts += 1
                    if self._wake_ws_open_attempts >= PAIRING_STUCK_WS_OPENS:
                        self._notify_pairing_stuck()
                    await self._ws.async_connect()  # type: ignore[union-attr]
                    # Handshake (ms.channel.connect) is async; keep polling until ON or timeout.
                    if self.power_state == PowerState.ON:
                        return
                    self._schedule_wake_tick(WAKING_POLL_INTERVAL)
                    return
            except TimeoutError:
                _LOGGER.info(
                    "Samsung TV Max [%s]: wake poll: /api/v2/ timeout (%ss) — retry",
                    self._host,
                    POWER_PROBE_TIMEOUT,
                )
            except aiohttp.ClientError as err:
                _LOGGER.info(
                    "Samsung TV Max [%s]: wake poll: /api/v2/ error: %s — retry",
                    self._host,
                    err,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.info(
                    "Samsung TV Max [%s]: wake poll: unexpected %s — retry",
                    self._host,
                    err,
                )
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
            ) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError):
                        data = {}
                    rest_power = self._extract_rest_power_state(data)
                    self._last_rest_power_state = rest_power
                    if rest_power == "standby":
                        _LOGGER.info(
                            "Samsung TV Max [%s]: REST reports standby — marking off",
                            self._host,
                        )
                        await self._set_power_state(PowerState.OFF)
                        return
                await self._start_liveness()  # schedule next
                return
        except Exception:  # noqa: BLE001
            pass
        _LOGGER.info("Samsung TV Max [%s]: liveness lost — marking off", self._host)
        await self._set_power_state(PowerState.OFF)

    # ── OFF slow poll (auto-detect TV waking up) ──────────────────────────────

    def _schedule_off_slow_poll(self, delay: float | None = None) -> None:
        self._cancel_timer("off_poll")
        wait = OFF_SLOW_POLL if delay is None else delay
        self._off_poll_timer = self.hass.loop.call_later(
            wait, self._off_slow_tick_sync
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
                self._off_poll_timeout_logged = False
                if resp.status != 200:
                    _LOGGER.info(
                        "Samsung TV Max [%s]: off poll: /api/v2/ HTTP %s (TV offline or busy)",
                        self._host,
                        resp.status,
                    )
                    self._schedule_off_slow_poll()
                    return
                try:
                    data = await resp.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError) as err:
                    _LOGGER.warning("Samsung TV Max [%s]: off poll JSON error: %s", self._host, err)
                else:
                    await self._async_merge_device_from_rest(data)
                    rest_power = self._extract_rest_power_state(data)
                    self._last_rest_power_state = rest_power
                    if rest_power == "standby":
                        _LOGGER.info(
                            "Samsung TV Max [%s]: off poll: REST says standby — stay off",
                            self._host,
                        )
                        self._schedule_off_slow_poll()
                        return
                _LOGGER.info(
                    "Samsung TV Max [%s]: detected on :%s while off — connecting",
                    self._host,
                    TIZEN_REST_PORT,
                )
                await self._enter_waking_up()
                return
        except TimeoutError:
            if not self._off_poll_timeout_logged:
                self._off_poll_timeout_logged = True
                _LOGGER.info(
                    "Samsung TV Max [%s]: off poll: /api/v2/ timeout (%ss)",
                    self._host,
                    POWER_PROBE_TIMEOUT,
                )
        except aiohttp.ClientError as err:
            self._off_poll_timeout_logged = False
            _LOGGER.info(
                "Samsung TV Max [%s]: off poll: /api/v2/ error: %s",
                self._host,
                err,
            )
        except Exception as err:  # noqa: BLE001
            self._off_poll_timeout_logged = False
            _LOGGER.info(
                "Samsung TV Max [%s]: off poll: unexpected %s",
                self._host,
                err,
            )
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
        _LOGGER.info("Samsung TV Max [%s]: WebSocket paired — TV is on", self._host)
        await self._set_power_state(PowerState.ON)
        self._bump_ui_on_grace_deadline()
        # Request installed apps if the TV supports it
        if self.caps.has_ghost_api and self._ws:
            await self._ws.async_request_app_list()

    async def _async_ws_reconnect_after_drop(self) -> None:
        """Reconnect WebSocket after an unexpected drop while power FSM says ON."""
        await asyncio.sleep(1.0)
        if self.power_state != PowerState.ON or self._ws is None:
            return
        if self._ws.is_connected:
            return
        _LOGGER.info(
            "Samsung TV Max [%s]: reconnecting WebSocket after drop",
            self._host,
        )
        try:
            await self._ws.async_connect()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Samsung TV Max [%s]: reconnect after drop failed: %s",
                self._host,
                err,
            )

    async def _on_ws_disconnected(self, was_unauthorized: bool) -> None:
        _LOGGER.info(
            "Samsung TV Max [%s]: WebSocket closed (unauthorized=%s, power=%s)",
            self._host,
            was_unauthorized,
            self.power_state,
        )
        if self.power_state in (PowerState.TURNING_OFF,):
            await self._set_power_state(PowerState.OFF)
        elif was_unauthorized:
            _LOGGER.warning(
                "Samsung TV Max [%s]: pairing denied — allow remote access on the TV",
                self._host,
            )
            await self._clear_persisted_token()
            self._notify_pairing_denied()
            await self._set_power_state(PowerState.UNAUTHORIZED)
        elif self.power_state == PowerState.WAKING_UP:
            # :8001 often comes up before :8002 during boot / WOL — retry instead of OFF.
            _LOGGER.info("Samsung TV Max [%s]: WS dropped during wake — retrying", self._host)
            self._schedule_wake_tick(WAKING_POLL_INTERVAL)
        elif self.power_state == PowerState.ON and not was_unauthorized:
            # Brief TV / network drops are common; stay ON and let liveness confirm real power-off.
            _LOGGER.info(
                "Samsung TV Max [%s]: WebSocket dropped while on — scheduling reconnect",
                self._host,
            )
            self.hass.async_create_task(self._async_ws_reconnect_after_drop())
        elif self.power_state not in (PowerState.OFF,):
            await self._set_power_state(PowerState.OFF)

    async def _on_apps_received(self, apps: list[dict]) -> None:
        if self._app_manager:
            self._app_manager.update_apps(apps)
            self.apps = self._app_manager.apps
        # Pre-fill icon_url from on-disk cache so UI shows icons immediately on reconnect
        # without waiting for a fresh ed.apps.icon round-trip.
        self._populate_icon_urls_from_disk()
        _LOGGER.debug(
            "App catalog updated: %d apps (%d with cached icon)",
            len(self.apps),
            len(self.icon_urls),
        )
        self._notify_listeners()

        self.hass.bus.async_fire(
            f"{self.entry.domain}_apps_updated",
            {"entry_id": self.entry.entry_id, "count": len(self.apps)},
        )

        # Kick off an async icon prefetch for any app whose icon is not on disk.
        # ed.apps.icon replies arrive out-of-band via _on_icon_received.
        if self._icon_prefetch_task and not self._icon_prefetch_task.done():
            self._icon_prefetch_task.cancel()
        self._icon_prefetch_task = self.hass.async_create_task(
            self._async_prefetch_icons()
        )

    def _populate_icon_urls_from_disk(self) -> None:
        """Look up cached icons for current apps; update ``self.icon_urls``."""
        for app in self.apps:
            app_id = app.get("appId", "")
            if not app_id:
                continue
            url = icon_cache.existing_url(self._integration_dir, self._host, app_id)
            if url:
                self.icon_urls[app_id] = url

    async def _async_prefetch_icons(self) -> None:
        """Emit ``ed.apps.icon`` for every app missing a cached icon, paced."""
        if self._ws is None or not self._ws.is_connected:
            return
        loop = asyncio.get_event_loop()
        deadline = loop.time() + _ICON_PREFETCH_BUDGET_SEC

        pending = [
            a for a in self.apps
            if a.get("icon_path") and a.get("appId") and a["appId"] not in self.icon_urls
        ]
        if not pending:
            return
        _LOGGER.debug(
            "Samsung TV Max [%s]: prefetching %d app icons", self._host, len(pending)
        )
        for app in pending:
            if loop.time() > deadline:
                _LOGGER.debug(
                    "Samsung TV Max [%s]: icon prefetch budget exceeded (%ds) — stopping",
                    self._host,
                    int(_ICON_PREFETCH_BUDGET_SEC),
                )
                return
            if self._ws is None or not self._ws.is_connected:
                return
            with contextlib.suppress(Exception):
                await self._ws.async_probe_app_icon(app["icon_path"])
            await asyncio.sleep(_ICON_PROBE_SPACING_SEC)

    async def _on_icon_received(self, app_id: str, image_b64: str) -> None:
        """ed.apps.icon reply: write PNG and expose URL on the app catalog."""
        if not app_id or not image_b64:
            return
        url = await self.hass.async_add_executor_job(
            icon_cache.write_icon_b64,
            self._integration_dir,
            self._host,
            app_id,
            image_b64,
        )
        if not url:
            return
        if self.icon_urls.get(app_id) == url:
            return
        self.icon_urls[app_id] = url
        self._notify_listeners()

    async def _on_keyboard_changed(self, active: bool) -> None:
        """IME state changed — refresh entity attributes so dashboard conditionals react."""
        _LOGGER.debug("Samsung TV Max [%s]: keyboard_active → %s", self._host, active)
        self._notify_listeners()

    async def _on_ime_content(self, text: str) -> None:
        """First imeUpdate after imeStart — pre-fill the shared input_text helper."""
        try:
            await self.hass.services.async_call(
                "input_text",
                "set_value",
                {"entity_id": "input_text.tv_text_input", "value": text[:255]},
            )
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Could not set input_text.tv_text_input: %s", exc)

    # ── Token rotation / preservation ─────────────────────────────────────────

    async def _handle_new_token(self, token: str) -> None:
        """Persist a newly received token to the config entry immediately."""
        _LOGGER.info("Samsung TV Max [%s]: TV access token updated in config", self._host)
        self._token = token
        if self._ws:
            self._ws.update_token(token)
        new_data = {**self.entry.data, CONF_TOKEN: token}
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

    # ── WOL ───────────────────────────────────────────────────────────────────

    async def _send_wol(self, ipv4: str, mac: str) -> None:
        """Send HC3-style WOL bursts; *ipv4* and *mac* are already validated."""
        # Match Fibaro HC3 QA: each round = TV IP, 255.255.255.255, subnet .255 (port 9).
        directed = directed_broadcast_ipv4(ipv4)
        dests: list[tuple[str, int]] = [
            (ipv4, WOL_UDP_PORT),
            ("255.255.255.255", WOL_UDP_PORT),
        ]
        if directed:
            dests.append((directed, WOL_UDP_PORT))
        dest_tuple = tuple(dests)

        summary = ", ".join(ip for ip, _ in dest_tuple)
        _LOGGER.info(
            "Samsung TV Max [%s]: WoL %s rounds → %s (UDP only — TV may ignore)",
            self._host,
            WOL_BURST_ROUNDS,
            summary,
        )

        for round_idx in range(1, WOL_BURST_ROUNDS + 1):
            await self.hass.async_add_executor_job(
                _execute_wol_round, mac, dest_tuple, round_idx
            )
            await asyncio.sleep(WOL_BURST_STEP)
        _LOGGER.info(
            "Samsung TV Max [%s]: WoL burst done — if the TV stays dark, check WoL on the "
            "TV, wired vs wireless MAC, and deep-standby behavior.",
            self._host,
        )

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
