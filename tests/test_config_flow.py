"""Tests for config_flow.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.samsungtv_max.config_flow import SamsungTVMaxConfigFlow
from custom_components.samsungtv_max.const import CONF_HOST, CONF_MODEL, CONF_TOKEN


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
        assert flow._mac == "AA:BB:CC:DD:EE:FF"

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
