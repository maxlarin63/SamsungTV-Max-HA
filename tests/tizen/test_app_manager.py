"""Tests for tizen/app_manager.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.samsungtv_max.tizen.app_manager import AppManager
from custom_components.samsungtv_max.tizen.caps import TizenCaps


@pytest.fixture
def manager(mock_session, sample_apps):
    ws_launch = AsyncMock(return_value=True)
    caps = TizenCaps(meta_tag_nav=True, has_ghost_api=True)
    m = AppManager(mock_session, "192.168.1.50", caps, ws_launch_fn=ws_launch)
    m.update_apps(sample_apps)
    return m, ws_launch


class TestAppResolution:
    def test_resolve_by_id(self, manager):
        m, _ = manager
        assert m.resolve_app_id("111299001912") == "111299001912"

    def test_resolve_by_name_exact(self, manager):
        m, _ = manager
        assert m.resolve_app_id("YouTube") == "111299001912"

    def test_resolve_by_name_case_insensitive(self, manager):
        m, _ = manager
        assert m.resolve_app_id("youtube") == "111299001912"

    def test_resolve_by_logical_key(self, manager):
        m, _ = manager
        assert m.resolve_app_id("APP_YOUTUBE") == "111299001912"

    def test_resolve_unknown_returns_none(self, manager):
        m, _ = manager
        assert m.resolve_app_id("NonExistentApp") is None

    def test_fallback_for_netflix(self):
        """When app list is empty, fallback IDs are used."""
        ws_launch = AsyncMock(return_value=True)
        caps = TizenCaps()
        m = AppManager(MagicMock(), "192.168.1.50", caps, ws_launch_fn=ws_launch)
        # No update_apps call → empty list
        assert m.resolve_app_id("APP_NETFLIX") == "3201907018807"


class TestAppLaunch:
    async def test_launch_native_via_ws(self, manager):
        m, ws_launch = manager
        # org.tizen.browser is in TIZEN_NATIVE_IDS → WS launch
        result = await m.async_launch("org.tizen.browser")
        ws_launch.assert_called_once_with("org.tizen.browser")

    async def test_launch_downloaded_via_rest(self, mock_session, sample_apps):
        ws_launch = AsyncMock(return_value=True)
        caps = TizenCaps()
        m = AppManager(mock_session, "192.168.1.50", caps, ws_launch_fn=ws_launch)
        m.update_apps(sample_apps)

        # Patch _rest_launch
        m._rest_launch = AsyncMock(return_value=True)
        result = await m.async_launch("111299001912")  # YouTube, app_type 2
        m._rest_launch.assert_called_once_with("111299001912")

    async def test_launch_by_name(self, manager):
        m, _ = manager
        m._rest_launch = AsyncMock(return_value=True)
        result = await m.async_launch_by_name("Netflix")
        m._rest_launch.assert_called_once_with("3201907018807")
