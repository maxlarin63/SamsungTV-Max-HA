"""Power state machine for Samsung Tizen TVs.

Direct port of the five-state FSM described in powerControl.lua.

States
------
OFF          No usable WS session.  Slow HTTP poll active.
WAKING_UP    Connecting: HTTP poll ~1 s, give up after 30 s, optional WOL burst.
ON           ms.channel.connect done; key sending enabled.
TURNING_OFF  Power-off command sent; optimistic until WS drops or 20 s timeout.
UNAUTHORIZED Remote blocked on TV; retry WAKING_UP after 30 s.
"""

from __future__ import annotations

from enum import StrEnum


class PowerState(StrEnum):
    OFF = "off"
    WAKING_UP = "waking_up"
    ON = "on"
    TURNING_OFF = "turning_off"
    UNAUTHORIZED = "unauthorized"


# Valid state transitions (from_state → {allowed to_states})
_VALID_TRANSITIONS: dict[PowerState, set[PowerState]] = {
    PowerState.OFF: {PowerState.WAKING_UP},
    PowerState.WAKING_UP: {
        PowerState.ON,
        PowerState.OFF,
        PowerState.UNAUTHORIZED,
        PowerState.WAKING_UP,  # re-enter on retry
    },
    PowerState.ON: {PowerState.TURNING_OFF, PowerState.OFF, PowerState.UNAUTHORIZED},
    PowerState.TURNING_OFF: {PowerState.OFF, PowerState.WAKING_UP},
    PowerState.UNAUTHORIZED: {PowerState.WAKING_UP, PowerState.OFF},
}


def is_valid_transition(from_state: PowerState, to_state: PowerState) -> bool:
    """Return True if the transition from_state → to_state is allowed."""
    return to_state in _VALID_TRANSITIONS.get(from_state, set())


def keys_allowed(state: PowerState) -> bool:
    """Return True when key-sending is permitted (mirrors shouldSendKey in Lua)."""
    return state is PowerState.ON
