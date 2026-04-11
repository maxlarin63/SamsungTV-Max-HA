"""Shared pytest fixtures for Samsung TV Max tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_session():
    """Minimal aiohttp.ClientSession mock."""
    session = AsyncMock()
    session.closed = False
    return session


@pytest.fixture
def sample_apps():
    """A short realistic app list as returned by ed.installedApp.get."""
    return [
        {"appId": "111299001912", "name": "YouTube", "app_type": 2, "is_visible": True},
        {"appId": "3201907018807", "name": "Netflix", "app_type": 2, "is_visible": True},
        {
            "appId": "3201606009684",
            "name": "Spotify - Music and Podcasts",
            "app_type": 2,
            "is_visible": True,
        },
        {"appId": "org.tizen.browser", "name": "Web Browser", "app_type": 4, "is_visible": True},
    ]


@pytest.fixture
def mock_hass():
    """Minimal HomeAssistant-like mock."""
    hass = MagicMock()
    hass.loop = MagicMock()
    hass.loop.call_later = MagicMock(return_value=MagicMock())
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    hass.async_create_task = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Minimal config-entry mock."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Living Room TV"
    entry.domain = "samsungtv_max"
    entry.data = {
        "host": "192.168.1.50",
        "model": "QE55Q80RATXXH",
        "mac": "AA:BB:CC:DD:EE:FF",
        "generation": "modern",
        "token": "",
    }
    return entry
