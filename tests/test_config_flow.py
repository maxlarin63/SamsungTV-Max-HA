"""Tests for config_flow.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.samsungtv_max.config_flow import SamsungTVMaxConfigFlow
from custom_components.samsungtv_max.const import CONF_HOST, CONF_MODEL, CONF_TOKEN


class TestAutoDeferredSetup:
    async def test_cannot_connect_creates_entry_without_pairing(self):
        flow = SamsungTVMaxConfigFlow()
        with (
            patch.object(flow, "async_set_unique_id", new_callable=AsyncMock),
            patch.object(flow, "_abort_if_unique_id_configured"),
            patch.object(flow, "_async_detect_tv", new_callable=AsyncMock, return_value="cannot_connect"),
        ):
            result = await flow.async_step_user(
                {CONF_HOST: "192.168.1.50", CONF_NAME: "Living TV"}
            )
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Living TV"
        data = result["data"]
        assert data["host"] == "192.168.1.50"
        assert data["mac"] == ""
        assert data["model"] == ""
        assert data["token"] == ""

    async def test_missing_mac_creates_entry_with_model(self):
        flow = SamsungTVMaxConfigFlow()

        async def detect_partial() -> str:
            flow._model = "QE55Q80RATXXH"
            flow._mac = ""
            flow._generation = "19_"
            return "missing_mac"

        with (
            patch.object(flow, "async_set_unique_id", new_callable=AsyncMock),
            patch.object(flow, "_abort_if_unique_id_configured"),
            patch.object(flow, "_async_detect_tv", side_effect=detect_partial),
        ):
            result = await flow.async_step_user({CONF_HOST: "192.168.1.50"})
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        assert result["data"]["model"] == "QE55Q80RATXXH"
        assert result["data"]["mac"] == ""
        assert result["data"]["generation"] == "19_"
        assert result["data"]["token"] == ""


class TestDetectTV:
    async def test_successful_detection(self):
        flow = SamsungTVMaxConfigFlow()
        flow._host = "192.168.1.50"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "device": {
                "modelName": "QE55Q80RATXXH",
                "wifiMac": "AA:BB:CC:DD:EE:FF",
            }
        })
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("aiohttp.TCPConnector"):
            result = await flow._async_detect_tv()

        assert result == "ok"
        assert flow._model == "QE55Q80RATXXH"
        assert flow._mac == "aa:bb:cc:dd:ee:ff"

    async def test_duid_is_not_used_as_mac(self):
        flow = SamsungTVMaxConfigFlow()
        flow._host = "192.168.1.50"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "device": {
                    "modelName": "QE55Q80RATXXH",
                    "wifiMac": "",
                    "duid": "not-a-mac",
                }
            }
        )
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("aiohttp.TCPConnector"):
            result = await flow._async_detect_tv()

        assert result == "missing_mac"
        assert flow._mac == ""

    async def test_legacy_tv_returns_unsupported(self):
        flow = SamsungTVMaxConfigFlow()
        flow._host = "192.168.1.50"

        import aiohttp
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientConnectionError)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("aiohttp.TCPConnector"):
            result = await flow._async_detect_tv()

        assert result == "cannot_connect"

    async def test_non_200_returns_unsupported(self):
        flow = SamsungTVMaxConfigFlow()
        flow._host = "192.168.1.50"

        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("aiohttp.TCPConnector"):
            result = await flow._async_detect_tv()

        assert result == "unsupported_model"
