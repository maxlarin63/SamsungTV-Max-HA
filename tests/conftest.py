"""Shared pytest fixtures for Samsung TV Max tests."""

from __future__ import annotations

import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Silence noisy DEBUG/INFO loggers in test output.

    ``pytest-homeassistant-custom-component`` calls ``logging.basicConfig(level=INFO)`` at
    import time and, when invoked with ``-v``, bumps the root logger to ``DEBUG``. That
    floods the terminal with ``DEBUG:asyncio:Using proactor: IocpProactor`` (the autouse
    ``enable_event_loop_debug`` fixture flips ``loop.set_debug(True)`` for every test) and
    with the integration's own ``DEBUG`` / ``INFO`` chatter — none of which any test
    asserts on (no ``caplog`` usage anywhere in the suite).

    ``trylast=True`` ensures this runs *after* the plugin's ``pytest_configure``, otherwise
    the plugin would re-raise the root logger to ``DEBUG`` on top of us.
    """
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("custom_components.samsungtv_max").setLevel(logging.WARNING)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):  # noqa: ANN001
    """Re-enable sockets before the asyncio ``event_loop`` fixture runs on Windows.

    ``pytest-homeassistant-custom-component`` calls ``pytest_socket.disable_socket()`` in
    ``pytest_runtest_setup``, before fixtures run. Both Proactor and Selector loops need
    ``socket.socketpair()`` for the self-pipe; unblocking only for ``event_loop`` keeps
    the intent of pytest-socket for test bodies. Linux/macOS unchanged.
    """
    if sys.platform == "win32" and getattr(fixturedef, "argname", None) == "event_loop":
        import pytest_socket

        pytest_socket.enable_socket()
    yield


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
