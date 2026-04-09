"""Power state machine for Samsung Tizen TVs.

Direct port of the five-state FSM described in powerControl.lua.  Implementations
live in ``SamsungTVCoordinator`` (timers, HTTP/WOL, WS callbacks).

Semantic note (important for users)
-----------------------------------
**``PowerState.ON`` is not “TV screen is emitting light”.**  It means: the
integration has completed the Tizen **remote-control WebSocket handshake**
(``ms.channel.connect``) and may send keys.  Many Samsung sets keep **:8001 REST**
and **:8002 WSS** reachable in standby, “Eco”, quick-start, or while the panel is
off, so HA can show **on** while the room sees a dark screen — and the reverse
can happen briefly during transitions.

``async_turn_off`` sends **KEY_POWER** (IR-style toggle / context-dependent), not
a guaranteed “hard off” command.  Rapid turn-on + turn-off in the UI overlaps
**TURNING_OFF** (WS often still up) with **WAKING_UP** (WOL + reconnect); logs
will look “busy” and perceived power may lag behind the FSM.

States (internal)
-----------------
OFF
    No paired remote session; WS closed after transition.  **Off poll** hits
    ``http://<tv>:8001/api/v2/`` first after ``OFF_SLOW_POLL_INITIAL_DELAY``, then
    every ``OFF_SLOW_POLL`` s; HTTP 200 →
    **WAKING_UP** (TV is reachable on the network again).

WAKING_UP
    Discovering / reopening the control plane: **wake tick** polls :8001 on
    ``WAKING_POLL_INTERVAL``, opens WSS on success, until **ON** or give-up
    (``WAKING_GIVE_UP``) → **OFF**.  Previous WS is **closed** on entry so a new
    ``ms.channel.connect`` always runs.  **WoL** runs only when ``async_turn_on``
    is entered from **OFF**; from other states HTTP/WS is used (NIC may still be up).

ON
    ``ms.channel.connect`` received; keys and app launch allowed.  **Liveness**
    polls :8001 every ``ON_LIVENESS_INTERVAL``; repeated failure → **OFF**.
    Dropped WSS while ON schedules **reconnect** (stay ON); liveness still
    eventually marks **OFF** if HTTP dies.

TURNING_OFF
    **KEY_POWER** was sent from **ON**; WS is *not* closed immediately.  If the
    socket closes, → **OFF**.  If nothing happens for ``TURNING_OFF_TIMEOUT``,
    → **OFF** anyway (optimistic fallback).  **async_turn_on** while here →
    **WAKING_UP** (user cancelled real off or TV ignored the key).

UNAUTHORIZED
    TV sent ``ms.channel.unauthorized``; user must allow the device.  After
    ``UNAUTHORIZED_RETRY``, coordinator retries **WAKING_UP**.
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
