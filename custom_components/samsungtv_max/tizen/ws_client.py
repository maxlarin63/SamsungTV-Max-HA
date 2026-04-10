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
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any
from urllib.parse import urlencode

import aiohttp

from ..const import (
    TIZEN_KEEPALIVE_INTERVAL,
    TIZEN_WS_PORT,
    WS_APP_NAME,
    WS_EVENT_CHANNEL_CONNECT,
    WS_EVENT_CHANNEL_DISCONNECT,
    WS_EVENT_CHANNEL_UNAUTHORIZED,
    WS_EVENT_INSTALLED_APP,
    WS_METHOD_CHANNEL_EMIT,
    WS_METHOD_REMOTE_CONTROL,
)

_LOGGER = logging.getLogger(__name__)

# Callbacks
OnConnected = Callable[[], Coroutine[Any, Any, None]]
OnDisconnected = Callable[[bool], Coroutine[Any, Any, None]]  # arg: was_unauthorized
OnAppsReceived = Callable[[list[dict]], Coroutine[Any, Any, None]]
OnTokenReceived = Callable[[str], Coroutine[Any, Any, None]]


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
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._token = token

        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_apps_received = on_apps_received
        self._on_token_received = on_token_received

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._reader_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None
        self._unauthorized = False
        self._closed = False

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

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
        self._stop_keepalive()
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def async_send_key(self, key: str) -> bool:
        """Send a single key-press command.  Returns False if not connected."""
        return await self._send_json(
            {
                "method": WS_METHOD_REMOTE_CONTROL,
                "params": {
                    "Cmd": "Click",
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

        elif event == WS_EVENT_INSTALLED_APP:
            await self._handle_installed_apps(msg)

    async def _handle_channel_connect(self, msg: dict) -> None:
        """ms.channel.connect — extract token, fire on_connected."""
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
