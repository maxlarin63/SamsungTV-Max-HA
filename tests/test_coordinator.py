"""Tests for coordinator.py — power FSM transitions and token rotation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.samsungtv_max.coordinator import SamsungTVCoordinator
from custom_components.samsungtv_max.tizen.power_fsm import PowerState


@pytest.fixture
def coordinator(mock_hass, mock_config_entry):
    return SamsungTVCoordinator(mock_hass, mock_config_entry)


class TestPowerStateTransitions:
    async def test_initial_state_is_off(self, coordinator):
        assert coordinator.power_state == PowerState.OFF

    async def test_set_on_notifies_listeners(self, coordinator):
        listener = MagicMock()
        coordinator.async_add_listener(listener)
        await coordinator._set_power_state(PowerState.ON)
        listener.assert_called_once()

    async def test_set_off_closes_ws(self, coordinator):
        ws_mock = AsyncMock()
        coordinator._ws = ws_mock
        coordinator.power_state = PowerState.ON
        await coordinator._set_power_state(PowerState.OFF)
        ws_mock.async_close.assert_awaited_once()

    async def test_idempotent_on(self, coordinator):
        """Setting ON twice from ON should not call listeners again."""
        coordinator.power_state = PowerState.ON
        listener = MagicMock()
        coordinator.async_add_listener(listener)
        await coordinator._set_power_state(PowerState.ON)
        listener.assert_not_called()

    async def test_idempotent_off(self, coordinator):
        coordinator.power_state = PowerState.OFF
        coordinator._ws = None
        listener = MagicMock()
        coordinator.async_add_listener(listener)
        await coordinator._set_power_state(PowerState.OFF)
        listener.assert_not_called()


class TestTokenRotation:
    async def test_new_token_persisted(self, coordinator, mock_hass, mock_config_entry):
        await coordinator._handle_new_token("fresh_token_xyz")
        assert coordinator._token == "fresh_token_xyz"
        mock_hass.config_entries.async_update_entry.assert_called_once()
        call_kwargs = mock_hass.config_entries.async_update_entry.call_args
        saved_data = call_kwargs[1]["data"] if call_kwargs[1] else call_kwargs[0][1]
        # Verify the token was written into the entry data dict
        assert "fresh_token_xyz" in str(saved_data)

    async def test_token_forwarded_to_ws_client(self, coordinator):
        ws_mock = MagicMock()
        coordinator._ws = ws_mock
        await coordinator._handle_new_token("another_token")
        ws_mock.update_token.assert_called_once_with("another_token")


class TestWsCallbacks:
    async def test_on_connected_sets_on(self, coordinator):
        coordinator.power_state = PowerState.WAKING_UP
        ws_mock = AsyncMock()
        ws_mock.async_request_app_list = AsyncMock()
        coordinator._ws = ws_mock
        coordinator.caps = MagicMock()
        coordinator.caps.has_ghost_api = False  # skip app list request
        await coordinator._on_ws_connected()
        assert coordinator.power_state == PowerState.ON

    async def test_on_disconnected_while_turning_off_goes_off(self, coordinator):
        coordinator.power_state = PowerState.TURNING_OFF
        coordinator._ws = None
        await coordinator._on_ws_disconnected(was_unauthorized=False)
        assert coordinator.power_state == PowerState.OFF

    async def test_on_disconnected_unauthorized_goes_unauthorized(self, coordinator):
        coordinator.power_state = PowerState.ON
        coordinator._ws = None
        await coordinator._on_ws_disconnected(was_unauthorized=True)
        assert coordinator.power_state == PowerState.UNAUTHORIZED


class TestSendKey:
    def test_key_blocked_when_not_on(self, coordinator):
        coordinator.power_state = PowerState.OFF
        ks = MagicMock()
        coordinator._key_sender = ks
        coordinator.send_key("KEY_VOLUMEUP")
        ks.enqueue.assert_not_called()

    def test_key_sent_when_on(self, coordinator):
        coordinator.power_state = PowerState.ON
        ks = MagicMock()
        coordinator._key_sender = ks
        coordinator.send_key("KEY_MUTE", count=2)
        ks.enqueue.assert_called_once_with("KEY_MUTE", 2)
