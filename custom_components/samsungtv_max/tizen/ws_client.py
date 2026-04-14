"""Tizen WebSocket remote-control client.

Ported from tizenWs.lua.  Uses aiohttp (already a HA dependency) over a TLS
WebSocket connection to wss://<host>:8002/api/v2/channels/samsung.remote.control.

Token handling
--------------
On ``ms.channel.connect``, newer Tizen sets a **session** token at ``data.token``.
``data.clients[*].attributes.token`` is often a separate id — the session token must
be used on the next ``wss://...?token=`` reconnect (Fibaro HC3 behavior).

The chosen token is forwarded via ``on_token_received`` so the coordinator can
persist it to the config entry.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any
from urllib.parse import urlencode

import aiohttp

from ..const import (
    KEY_DOWN,
    KEY_ENTER,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_UP,
    TIZEN_KEEPALIVE_INTERVAL,
    TIZEN_TOUCH_DPAD_STEP,
    TIZEN_TOUCH_DPAD_THROTTLE_SEC,
    TIZEN_WS_PORT,
    WS_APP_NAME,
    WS_EVENT_CHANNEL_CONNECT,
    WS_EVENT_CHANNEL_DISCONNECT,
    WS_EVENT_CHANNEL_UNAUTHORIZED,
    WS_EVENT_IME_END,
    WS_EVENT_IME_START,
    WS_EVENT_INSTALLED_APP,
    WS_EVENT_TOUCH_DISABLE,
    WS_EVENT_TOUCH_ENABLE,
    WS_METHOD_CHANNEL_EMIT,
    WS_METHOD_REMOTE_CONTROL,
)

_S = TIZEN_TOUCH_DPAD_STEP
_TOUCH_MOVE_DELTAS: dict[str, tuple[int, int]] = {
    KEY_UP: (0, -_S),
    KEY_DOWN: (0, _S),
    KEY_LEFT: (-_S, 0),
    KEY_RIGHT: (_S, 0),
}
_TOUCH_QUEUE_BYPASS_KEYS: frozenset[str] = frozenset(_TOUCH_MOVE_DELTAS) | {KEY_ENTER}

_LOGGER = logging.getLogger(__name__)

# Callbacks
OnConnected = Callable[[], Coroutine[Any, Any, None]]
OnDisconnected = Callable[[bool], Coroutine[Any, Any, None]]  # arg: was_unauthorized
OnAppsReceived = Callable[[list[dict]], Coroutine[Any, Any, None]]
OnTokenReceived = Callable[[str], Coroutine[Any, Any, None]]
OnKeyboardChanged = Callable[[bool], Coroutine[Any, Any, None]]  # arg: keyboard_active
OnImeContent = Callable[[str], Coroutine[Any, Any, None]]  # arg: decoded text


class TizenWSClient:
    """Manages a single wss:// WebSocket session to the TV remote-control channel."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = TIZEN_WS_PORT,
        token: str = "",
        *,
        on_connected: OnConnected | None = None,
        on_disconnected: OnDisconnected | None = None,
        on_apps_received: OnAppsReceived | None = None,
        on_token_received: OnTokenReceived | None = None,
        on_keyboard_changed: OnKeyboardChanged | None = None,
        on_ime_content: OnImeContent | None = None,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._token = token

        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_apps_received = on_apps_received
        self._on_token_received = on_token_received
        self._on_keyboard_changed = on_keyboard_changed
        self._on_ime_content = on_ime_content

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._reader_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None
        self._unauthorized = False
        self._closed = False
        # HC3 tizenWs.lua: ms.remote.touchEnable / touchDisable (browser pointer mode)
        self._touch_mode = False
        self._touch_throttle_until = 0.0
        # HC3 tizenWs.lua: ms.remote.imeStart / imeEnd (on-screen keyboard / text field focus)
        self._keyboard_active = False
        self._ime_type: str | None = None
        self._ime_initial_content_forwarded = False

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    @property
    def touch_mode(self) -> bool:
        """True after ``ms.remote.touchEnable`` (e.g. Tizen browser); d-pad uses pointer."""
        return self._touch_mode

    @property
    def keyboard_active(self) -> bool:
        """True between ``ms.remote.imeStart`` and ``ms.remote.imeEnd``."""
        return self._keyboard_active

    def should_bypass_key_queue(self, key: str) -> bool:
        """HC3 keyControl: touch-mode d-pad bypasses the inter-key queue."""
        return self._touch_mode and key in _TOUCH_QUEUE_BYPASS_KEYS

    def update_token(self, token: str) -> None:
        """Update the token used for the next connection attempt."""
        self._token = token

    async def async_connect(self) -> None:
        """Open the WebSocket connection (non-blocking; callbacks fire on events)."""
        if self.is_connected:
            return
        self._closed = False
        self._unauthorized = False

        name_b64 = base64.b64encode(WS_APP_NAME.encode()).decode()
        params: dict[str, str] = {"name": name_b64}
        if self._token:
            # Token can contain characters like '+' which must be URL-encoded.
            params["token"] = self._token
        url = (
            f"wss://{self._host}:{self._port}"
            f"/api/v2/channels/samsung.remote.control"
            f"?{urlencode(params)}"
        )

        _LOGGER.debug("WS connecting: %s", url)
        _LOGGER.info(
            "Samsung TV Max WS [%s]: connecting to wss://%s:%s/api/v2/channels/samsung.remote.control",
            self._host,
            self._host,
            self._port,
        )

        try:
            ws = await self._session.ws_connect(
                url,
                ssl=False,      # TV uses self-signed cert
                heartbeat=None, # we handle keepalive ourselves
                timeout=aiohttp.ClientWSTimeout(ws_close=10),
            )
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("Samsung TV Max WS [%s]: connect failed: %s", self._host, exc)
            if self._on_disconnected and not self._closed:
                asyncio.ensure_future(self._on_disconnected(False))
            return

        self._ws = ws
        self._reader_task = asyncio.ensure_future(self._reader_loop(ws))
        _LOGGER.info(
            "Samsung TV Max WS [%s]: TLS session up, waiting for ms.channel.connect",
            self._host,
        )

    async def async_close(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._closed = True
        self._touch_mode = False
        self._keyboard_active = False
        self._ime_type = None
        self._stop_keepalive()
        if self._reader_task:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def async_send_key(self, key: str) -> bool:
        """Send a single key-press, or pointer move/click when touch mode is active (HC3).

        In touch mode (``ms.remote.touchEnable``), ``KEY_UP``/``DOWN``/``LEFT``/``RIGHT`` map to
        ``ProcessMouseDevice`` moves with ``TIZEN_TOUCH_DPAD_STEP``; ``KEY_ENTER`` maps to
        ``LeftClick``.  Repeats inside ``TIZEN_TOUCH_DPAD_THROTTLE_SEC`` are dropped (success).
        """
        if self._touch_mode and key in _TOUCH_QUEUE_BYPASS_KEYS:
            loop = asyncio.get_running_loop()
            now = loop.time()
            if now < self._touch_throttle_until:
                return True
            self._touch_throttle_until = now + TIZEN_TOUCH_DPAD_THROTTLE_SEC
            if key == KEY_ENTER:
                return await self.async_send_touch_click()
            dx, dy = _TOUCH_MOVE_DELTAS[key]
            return await self.async_send_touch_move(dx, dy)

        return await self._send_key_cmd(key, "Click")

    async def async_send_key_press(self, key: str) -> bool:
        """Send key-down (TV auto-repeats until Release)."""
        return await self._send_key_cmd(key, "Press")

    async def async_send_key_release(self, key: str) -> bool:
        """Send key-up (stops TV auto-repeat started by Press)."""
        return await self._send_key_cmd(key, "Release")

    async def _send_key_cmd(self, key: str, cmd: str) -> bool:
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {
                    "Cmd": cmd,
                    "DataOfCmd": key,
                    "Option": "false",
                    "TypeOfRemote": "SendRemoteKey",
                },
            }
        )

    async def async_request_app_list(self) -> bool:
        """Request the installed-app list via ed.installedApp.get."""
        return await self._send_json(
            {
                "method": WS_METHOD_CHANNEL_EMIT,
                "params": {
                    "event": WS_EVENT_INSTALLED_APP,
                    "to": "host",
                },
            }
        )

    async def async_launch_app_ws(self, app_id: str) -> bool:
        """Launch a native app (app_type 4) via WS deep-link.  Port of __launchTizenAppWs."""
        _LOGGER.debug("App launch WS DEEP_LINK: %s", app_id)
        return await self._send_json(
            {
                "method": WS_METHOD_CHANNEL_EMIT,
                "params": {
                    "event": "ed.apps.launch",
                    "to": "host",
                    "data": {
                        "appId": app_id,
                        "action_type": "DEEP_LINK",
                        "metaTag": "",
                    },
                },
            }
        )

    async def async_send_touch_move(self, dx: int, dy: int) -> bool:
        """Send a pointer move event (used in browser/touch mode)."""
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {
                    "Cmd": "Move",
                    "Position": {"x": dx, "y": dy, "Time": "0"},
                    "TypeOfRemote": "ProcessMouseDevice",
                },
            }
        )

    async def async_send_touch_click(self) -> bool:
        """Send a left-click pointer event."""
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {
                    "Cmd": "LeftClick",
                    "TypeOfRemote": "ProcessMouseDevice",
                },
            }
        )

    async def async_send_input_string(self, text: str) -> bool:
        """Type *text* into the focused on-screen field (SendInputString).

        Text is UTF-8 → base64 encoded per the Samsung remote-control protocol.
        Works only when a text field is focused (``ms.remote.imeStart`` received).
        """
        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {
                    "Cmd": b64,
                    "DataOfCmd": "base64",
                    "TypeOfRemote": "SendInputString",
                },
            }
        )

    async def async_send_input_end(self) -> bool:
        """Signal the end of text input (SendInputEnd)."""
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {"TypeOfRemote": "SendInputEnd"},
            }
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _send_json(self, payload: dict) -> bool:
        if not self.is_connected or self._ws is None:
            return False
        try:
            await self._ws.send_str(json.dumps(payload))
            return True
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("WS send error: %s", exc)
            return False

    async def _reader_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """Read incoming messages until the socket closes."""
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("WS reader error: %s", exc)
        finally:
            self._stop_keepalive()
            self._ws = None
            if not self._closed and self._on_disconnected:
                asyncio.ensure_future(self._on_disconnected(self._unauthorized))

    async def _handle_message(self, raw: str) -> None:
        _LOGGER.debug("TV → %s", raw[:300])
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        event = msg.get("event", "")

        if event == WS_EVENT_CHANNEL_CONNECT:
            await self._handle_channel_connect(msg)

        elif event == WS_EVENT_CHANNEL_UNAUTHORIZED:
            _LOGGER.warning(
                "Samsung TV Max WS [%s]: ms.channel.unauthorized — allow this device on the TV",
                self._host,
            )
            self._unauthorized = True
            if self._ws and not self._ws.closed:
                await self._ws.close()

        elif event == WS_EVENT_CHANNEL_DISCONNECT:
            _LOGGER.debug("WS: channel disconnect from TV")

        elif event == WS_EVENT_TOUCH_ENABLE:
            self._touch_mode = True
            _LOGGER.debug("Samsung TV Max WS [%s]: touch mode ON (d-pad → pointer)", self._host)

        elif event == WS_EVENT_TOUCH_DISABLE:
            self._touch_mode = False
            _LOGGER.debug("Samsung TV Max WS [%s]: touch mode OFF (d-pad → keys)", self._host)

        elif event == WS_EVENT_IME_START:
            self._keyboard_active = True
            self._ime_initial_content_forwarded = False
            self._ime_type = msg.get("data") if isinstance(msg.get("data"), str) else None
            _LOGGER.debug(
                "Samsung TV Max WS [%s]: IME active (type=%s)", self._host, self._ime_type
            )
            if self._on_keyboard_changed:
                await self._on_keyboard_changed(True)

        elif event == "ms.remote.imeUpdate":
            await self._handle_ime_update(msg)

        elif event == WS_EVENT_IME_END:
            self._keyboard_active = False
            self._ime_type = None
            self._ime_initial_content_forwarded = False
            _LOGGER.debug("Samsung TV Max WS [%s]: IME closed", self._host)
            if self._on_keyboard_changed:
                await self._on_keyboard_changed(False)

        elif event == WS_EVENT_INSTALLED_APP:
            await self._handle_installed_apps(msg)

    async def _handle_channel_connect(self, msg: dict) -> None:
        """ms.channel.connect — extract token, fire on_connected."""
        self._touch_mode = False
        self._keyboard_active = False
        self._ime_type = None
        # Fibaro / newer Tizen: ``data.token`` is the session token used on reconnect.
        # ``clients[*].attributes.token`` is often a *different* id (e.g. 10051859 vs 58374607).
        # Some firmware omits ``data.token`` on occasional ``ms.channel.connect`` frames; if we
        # then persist the client token, the next cold ``?token=`` breaks and the TV re-prompts.
        token: str = ""
        try:
            data = msg.get("data", {}) or {}
            if isinstance(data, dict):
                root = data.get("token", "")
                if isinstance(root, str) and root.strip():
                    token = root.strip()
                elif self._token:
                    # Keep session token; do not downgrade to client/attributes-only fields.
                    token = self._token
                else:
                    clients = data.get("clients", [])
                    if isinstance(clients, list):
                        for client in clients:
                            if not isinstance(client, dict):
                                continue
                            attrs = client.get("attributes", {})
                            if not isinstance(attrs, dict):
                                continue
                            t = attrs.get("token", "")
                            if isinstance(t, str) and t.strip():
                                token = t.strip()
                                break

                    if not token:
                        attrs2 = data.get("attributes", {})
                        if isinstance(attrs2, dict):
                            t3 = attrs2.get("token", "")
                            if isinstance(t3, str) and t3.strip():
                                token = t3.strip()
        except Exception:  # noqa: BLE001
            pass

        if token and token != self._token:
            _LOGGER.debug("WS: new token received: %s", token)
            self._token = token
            if self._on_token_received:
                await self._on_token_received(token)

        self._start_keepalive()

        if self._on_connected:
            await self._on_connected()

    async def _handle_installed_apps(self, msg: dict) -> None:
        """ed.installedApp.get response — parse and forward app list."""
        try:
            apps_raw = msg.get("data", {}).get("data", [])
            apps = [
                {
                    "appId": a.get("appId", ""),
                    "name": a.get("name", ""),
                    "app_type": a.get("app_type", 2),
                    "is_visible": a.get("is_visible", True),
                }
                for a in apps_raw
                if a.get("appId")
            ]
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("App list parse error: %s", exc)
            return

        _LOGGER.debug("Apps received: %d entries", len(apps))
        if self._on_apps_received:
            await self._on_apps_received(apps)

    async def _handle_ime_update(self, msg: dict) -> None:
        """ms.remote.imeUpdate — decode base64 field content, forward once per imeStart."""
        if self._ime_initial_content_forwarded or not self._on_ime_content:
            return
        raw = msg.get("data")
        if not isinstance(raw, str) or not raw:
            return
        try:
            text = base64.b64decode(raw).decode("utf-8")
        except Exception:  # noqa: BLE001
            return
        self._ime_initial_content_forwarded = True
        _LOGGER.debug("Samsung TV Max WS [%s]: IME initial content: %s", self._host, text[:120])
        await self._on_ime_content(text)

    # ── Keepalive ─────────────────────────────────────────────────────────────

    def _start_keepalive(self) -> None:
        self._stop_keepalive()
        self._keepalive_task = asyncio.ensure_future(self._keepalive_loop())

    def _stop_keepalive(self) -> None:
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

    async def _keepalive_loop(self) -> None:
        """Send a WS ping every TIZEN_KEEPALIVE_INTERVAL seconds."""
        try:
            while True:
                await asyncio.sleep(TIZEN_KEEPALIVE_INTERVAL)
                if self._ws and not self._ws.closed:
                    try:
                        await self._ws.ping()
                    except Exception:  # noqa: BLE001
                        break
        except asyncio.CancelledError:
            pass
