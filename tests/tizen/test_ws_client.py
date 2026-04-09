"""Tests for tizen/ws_client.py."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.samsungtv_max.tizen.ws_client import TizenWSClient


def _make_ws_msg(event: str, data: dict | None = None) -> MagicMock:
    """Build a fake aiohttp WSMessage with .type TEXT and .data JSON."""
    import aiohttp
    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.TEXT
    payload = {"event": event}
    if data:
        payload["data"] = data
    msg.data = json.dumps(payload)
    return msg


@pytest.fixture
def callbacks():
    return {
        "on_connected": AsyncMock(),
        "on_disconnected": AsyncMock(),
        "on_apps_received": AsyncMock(),
        "on_token_received": AsyncMock(),
    }


@pytest.fixture
def client(mock_session, callbacks):
    return TizenWSClient(
        mock_session,
        "192.168.1.50",
        token="old_token",
        **callbacks,
    )


class TestTokenExtraction:
    """Tests for ms.channel.connect token handling.

    Each test calls _stop_keepalive() in teardown because _handle_channel_connect
    starts the keepalive task; the HA test plugin detects lingering tasks otherwise.
    """

    async def test_new_token_fires_callback(self, client, callbacks):
        msg = {
            "event": "ms.channel.connect",
            "data": {
                "clients": [
                    {"attributes": {"token": "new_token_123"}}
                ]
            },
        }
        await client._handle_message(json.dumps(msg))
        client._stop_keepalive()  # clean up task started by _handle_channel_connect
        callbacks["on_token_received"].assert_awaited_once_with("new_token_123")
        assert client._token == "new_token_123"

    async def test_same_token_no_callback(self, client, callbacks):
        """No callback if token hasn't changed."""
        msg = {
            "event": "ms.channel.connect",
            "data": {"clients": [{"attributes": {"token": "old_token"}}]},
        }
        await client._handle_message(json.dumps(msg))
        client._stop_keepalive()
        callbacks["on_token_received"].assert_not_awaited()

    async def test_no_token_in_message(self, client, callbacks):
        msg = {"event": "ms.channel.connect", "data": {"clients": []}}
        await client._handle_message(json.dumps(msg))
        client._stop_keepalive()
        callbacks["on_token_received"].assert_not_awaited()
        callbacks["on_connected"].assert_awaited_once()


class TestUnauthorized:
    async def test_unauthorized_sets_flag(self, client):
        msg = {"event": "ms.channel.unauthorized"}
        client._ws = AsyncMock()
        client._ws.closed = False
        await client._handle_message(json.dumps(msg))
        assert client._unauthorized is True


class TestAppListParsing:
    async def test_apps_parsed_and_forwarded(self, client, callbacks):
        apps_data = [
            {"appId": "111299001912", "name": "YouTube", "app_type": 2, "is_visible": True},
            {"appId": "3201907018807", "name": "Netflix", "app_type": 2, "is_visible": True},
        ]
        msg = {"event": "ed.installedApp.get", "data": {"data": apps_data}}
        await client._handle_message(json.dumps(msg))
        callbacks["on_apps_received"].assert_awaited_once()
        received = callbacks["on_apps_received"].call_args[0][0]
        assert len(received) == 2
        assert received[0]["appId"] == "111299001912"

    async def test_empty_app_list(self, client, callbacks):
        msg = {"event": "ed.installedApp.get", "data": {"data": []}}
        await client._handle_message(json.dumps(msg))
        callbacks["on_apps_received"].assert_awaited_once_with([])


class TestSendKey:
    async def test_send_key_when_connected(self, client):
        ws_mock = AsyncMock()
        ws_mock.closed = False
        client._ws = ws_mock
        result = await client.async_send_key("KEY_VOLUMEUP")
        assert result is True
        ws_mock.send_str.assert_awaited_once()
        sent = json.loads(ws_mock.send_str.call_args[0][0])
        assert sent["params"]["DataOfCmd"] == "KEY_VOLUMEUP"
        assert sent["params"]["Cmd"] == "Click"

    async def test_send_key_when_disconnected(self, client):
        client._ws = None
        result = await client.async_send_key("KEY_VOLUMEUP")
        assert result is False
