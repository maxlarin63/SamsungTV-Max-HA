"""Tests for tizen/power_fsm.py."""

import pytest

from custom_components.samsungtv_max.tizen.power_fsm import PowerState, is_valid_transition, keys_allowed


class TestValidTransitions:
    def test_off_to_waking(self):
        assert is_valid_transition(PowerState.OFF, PowerState.WAKING_UP) is True

    def test_off_to_on_invalid(self):
        assert is_valid_transition(PowerState.OFF, PowerState.ON) is False

    def test_waking_to_on(self):
        assert is_valid_transition(PowerState.WAKING_UP, PowerState.ON) is True

    def test_waking_to_off(self):
        assert is_valid_transition(PowerState.WAKING_UP, PowerState.OFF) is True

    def test_waking_to_unauth(self):
        assert is_valid_transition(PowerState.WAKING_UP, PowerState.UNAUTHORIZED) is True

    def test_on_to_turning_off(self):
        assert is_valid_transition(PowerState.ON, PowerState.TURNING_OFF) is True

    def test_on_to_off(self):
        assert is_valid_transition(PowerState.ON, PowerState.OFF) is True

    def test_turning_off_to_off(self):
        assert is_valid_transition(PowerState.TURNING_OFF, PowerState.OFF) is True

    def test_turning_off_to_waking(self):
        assert is_valid_transition(PowerState.TURNING_OFF, PowerState.WAKING_UP) is True

    def test_unauth_to_waking(self):
        assert is_valid_transition(PowerState.UNAUTHORIZED, PowerState.WAKING_UP) is True

    def test_on_to_waking_invalid(self):
        assert is_valid_transition(PowerState.ON, PowerState.WAKING_UP) is False


class TestKeysAllowed:
    def test_on_allows_keys(self):
        assert keys_allowed(PowerState.ON) is True

    @pytest.mark.parametrize("state", [
        PowerState.OFF,
        PowerState.WAKING_UP,
        PowerState.TURNING_OFF,
        PowerState.UNAUTHORIZED,
    ])
    def test_other_states_block_keys(self, state):
        assert keys_allowed(state) is False
